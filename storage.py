"""
Storage module for encrypted journal file handling.
Manages journal persistence with AES-256 encryption.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any
import config
import crypto_utils
from cryptography.exceptions import InvalidTag


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


def load_journal(passphrase: str) -> Dict[str, Any]:
    """
    Load and decrypt the journal from disk.
    
    Args:
        passphrase: Master passphrase
        
    Returns:
        Decrypted journal dictionary
        
    Raises:
        FileNotFoundError: If journal file doesn't exist
        cryptography.exceptions.InvalidTag: If passphrase is wrong
    """
    config.init_journal_dir()
    
    if not config.JOURNAL_PATH.exists():
        raise FileNotFoundError(f"Journal not found at {config.JOURNAL_PATH}")
    
    # Read encrypted file
    with open(config.JOURNAL_PATH, "rb") as f:
        file_data = f.read()
    
    # Extract salt (first 32 bytes, unencrypted) and encrypted blob
    salt = file_data[:config.SALT_LENGTH]
    encrypted_blob = file_data[config.SALT_LENGTH:]
    
    # Derive key from passphrase and salt
    key = crypto_utils.derive_key(passphrase, salt)
    
    # Decrypt
    try:
        plaintext = crypto_utils.decrypt_data(encrypted_blob, key)
        journal_data = json.loads(plaintext.decode())
        # Add salt back to the journal for consistency
        journal_data["salt"] = salt.hex()
        return journal_data
    except InvalidTag:
        raise ValueError("Failed to decrypt journal: wrong passphrase or corrupted file")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to decrypt journal (wrong passphrase?): {e}")


def save_journal(journal: Dict[str, Any], passphrase: str) -> None:
    """
    Encrypt and save the journal to disk.
    
    Args:
        journal: Journal dictionary
        passphrase: Master passphrase
    """
    config.init_journal_dir()
    
    # Get salt from journal or generate new one
    if "salt" not in journal or not journal["salt"]:
        salt = crypto_utils.generate_salt()
        journal["salt"] = salt.hex()
    else:
        salt = bytes.fromhex(journal["salt"])
    
    # Serialize journal to JSON bytes (without salt in the JSON itself for cleaner structure)
    journal_copy = journal.copy()
    del journal_copy["salt"]
    plaintext = json.dumps(journal_copy, indent=2).encode()
    
    # Derive key from passphrase and salt
    key = crypto_utils.derive_key(passphrase, salt)
    
    # Encrypt
    encrypted_blob = crypto_utils.encrypt_data(plaintext, key)
    
    # Prepend salt to encrypted blob and write to disk
    file_data = salt + encrypted_blob
    with open(config.JOURNAL_PATH, "wb") as f:
        f.write(file_data)


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
