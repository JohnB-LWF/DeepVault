"""
Configuration and constants for the Encrypted Journal CLI.
"""

import os
from pathlib import Path

# Journal file path
JOURNAL_DIR = Path.home() / ".encrypted_journal"
JOURNAL_PATH = JOURNAL_DIR / "journal.enc"

# Crypto settings
SALT_LENGTH = 32  # 256 bits for PBKDF2 salt
IV_LENGTH = 16    # 128 bits for AES IV
ITERATIONS = 600000  # PBKDF2 iterations (OWASP 2023+ recommendation for PBKDF2-HMAC-SHA256)
FORMAT_VERSION = 2  # on-disk layout: version(1) + iterations(4) + salt(32) + iv+ciphertext+tag

# UI settings
TYPING_DELAY = 0.01  # seconds per character
BANNER_COLOR = "cyan"

# Ensure journal directory exists
def init_journal_dir():
    """Create journal directory if it doesn't exist, locked down to the owner only."""
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(JOURNAL_DIR, 0o700)
    except OSError:
        pass  # best-effort on platforms without POSIX permission bits (e.g. Windows)
