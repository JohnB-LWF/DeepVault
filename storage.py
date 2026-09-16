"""
Storage module for encrypted journal file handling.
Manages journal persistence with AES-256-GCM encryption.

On-disk layout (all binary, nothing stored in plaintext except metadata
needed to reproduce the key derivation):
    1 byte  format version
    4 bytes PBKDF2 iteration count (big-endian, unsigned)
    32 bytes salt
    N bytes IV + AES-GCM ciphertext (includes the authentication tag)
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Tuple
import config
import crypto_utils
from cryptography.exceptions import InvalidTag

_ITERATIONS_LENGTH = 4


def _normalize_entry_id(entry_id: str) -> str:
    """Normalize a user-supplied entry ID or truncated preview."""
    return entry_id.strip().strip("[]").replace("...", "")


def initialize_journal() -> Dict[str, Any]:
    """
    Initialize a new empty journal structure.
    
    Returns:
        Dictionary with salt and empty entries list
    """
    return {
        "salt": crypto_utils.generate_salt().hex(),
        "entries": []
    }


def load_journal(passphrase: str) -> Tuple[Dict[str, Any], bytes]:
    """
    Load and decrypt the journal from disk.
    
    Args:
        passphrase: Master passphrase
        
    Returns:
        Tuple of (decrypted journal dictionary, derived AES key). The key is
        returned so callers can reuse it for subsequent saves instead of
        re-running the expensive PBKDF2 derivation (and holding the raw
        passphrase in memory) on every write.
        
    Raises:
        FileNotFoundError: If journal file doesn't exist
        ValueError: If the file is corrupt, truncated, or the passphrase is wrong
    """
    config.init_journal_dir()
    
    if not config.JOURNAL_PATH.exists():
        raise FileNotFoundError(f"Journal not found at {config.JOURNAL_PATH}")
    
    with open(config.JOURNAL_PATH, "rb") as f:
        file_data = f.read()

    header_length = 1 + _ITERATIONS_LENGTH + config.SALT_LENGTH
    if len(file_data) < header_length:
        raise ValueError("Journal file is truncated or corrupted")

    version = file_data[0]
    if version != config.FORMAT_VERSION:
        raise ValueError(f"Unsupported journal file version: {version}")

    iterations = int.from_bytes(file_data[1:1 + _ITERATIONS_LENGTH], "big")
    salt_start = 1 + _ITERATIONS_LENGTH
    salt = file_data[salt_start:salt_start + config.SALT_LENGTH]
    encrypted_blob = file_data[salt_start + config.SALT_LENGTH:]
    
    key = crypto_utils.derive_key(passphrase, salt, iterations)
    
    try:
        plaintext = crypto_utils.decrypt_data(encrypted_blob, key)
        journal_data = json.loads(plaintext.decode())
        # Carry salt/iterations along so save_journal can reuse them
        journal_data["salt"] = salt.hex()
        journal_data["iterations"] = iterations
        return journal_data, key
    except InvalidTag:
        raise ValueError("Failed to decrypt journal: wrong passphrase or corrupted file")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to decrypt journal (wrong passphrase?): {e}")


def save_journal(journal: Dict[str, Any], key: bytes) -> None:
    """
    Encrypt and save the journal to disk atomically.
    
    Args:
        journal: Journal dictionary (must contain "salt"; "iterations" is
            optional and defaults to config.ITERATIONS for new journals)
        key: 32-byte AES key already derived from the passphrase and salt
    """
    config.init_journal_dir()
    
    if "salt" not in journal or not journal["salt"]:
        raise ValueError("Journal is missing its salt; cannot save")
    salt = bytes.fromhex(journal["salt"])
    iterations = journal.get("iterations", config.ITERATIONS)
    
    # Serialize journal to JSON bytes (without salt/iterations in the body,
    # those live only in the file header)
    journal_copy = journal.copy()
    journal_copy.pop("salt", None)
    journal_copy.pop("iterations", None)
    plaintext = json.dumps(journal_copy, indent=2).encode()
    
    encrypted_blob = crypto_utils.encrypt_data(plaintext, key)
    
    header = bytes([config.FORMAT_VERSION]) + iterations.to_bytes(_ITERATIONS_LENGTH, "big") + salt
    file_data = header + encrypted_blob

    journal["iterations"] = iterations  # keep in sync for future saves in this session

    # Write atomically (temp file + rename) so a crash mid-write can never
    # leave a half-written, corrupted vault on disk.
    tmp_path = config.JOURNAL_PATH.with_suffix(config.JOURNAL_PATH.suffix + ".tmp")
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file_data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, config.JOURNAL_PATH)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
    try:
        os.chmod(config.JOURNAL_PATH, 0o600)
    except OSError:
        pass  # best-effort on platforms without POSIX permission bits


def add_entry(journal: Dict[str, Any], title: str, body: str) -> Dict[str, Any]:
    """
    Add a new entry to the journal.
    
    Args:
        journal: Journal dictionary
        title: Entry title
        body: Entry body/content
        
    Returns:
        Updated journal with new entry
    """
    entry = {
        "id": str(uuid.uuid4()),
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "body": body
    }
    journal["entries"].append(entry)
    return journal


def delete_entry(journal: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
    """
    Delete an entry from the journal by ID.
    
    Args:
        journal: Journal dictionary
        entry_id: UUID of entry to delete
        
    Returns:
        Updated journal without the entry
        
    Raises:
        ValueError: If entry not found
    """
    entry = get_entry_by_id(journal, entry_id)

    original_len = len(journal["entries"])
    journal["entries"] = [e for e in journal["entries"] if e["id"] != entry["id"]]
    
    if len(journal["entries"]) == original_len:
        raise ValueError(f"Entry with ID {entry_id} not found")
    
    return journal


def search_entries(journal: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """
    Search entries by title or body content (case-insensitive).
    
    Args:
        journal: Journal dictionary
        query: Search query string
        
    Returns:
        List of matching entries
    """
    query_lower = query.lower()
    results = []
    
    for entry in journal["entries"]:
        if (query_lower in entry["title"].lower() or 
            query_lower in entry["body"].lower()):
            results.append(entry)
    
    return results


def get_entry_by_id(journal: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
    """
    Get a single entry by ID.
    
    Args:
        journal: Journal dictionary
        entry_id: UUID of entry
        
    Returns:
        Entry dictionary
        
    Raises:
        ValueError: If entry not found
    """
    normalized_id = _normalize_entry_id(entry_id)

    for entry in journal["entries"]:
        if entry["id"] == normalized_id:
            return entry

    prefix_matches = [entry for entry in journal["entries"] if entry["id"].startswith(normalized_id)]

    if len(prefix_matches) == 1:
        return prefix_matches[0]

    if len(prefix_matches) > 1:
        raise ValueError(f"Entry ID prefix {entry_id} is ambiguous")

    for entry in journal["entries"]:
        if entry["id"] == entry_id:
            return entry

    raise ValueError(f"Entry with ID {entry_id} not found")
