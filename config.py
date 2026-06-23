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
ITERATIONS = 480000  # PBKDF2 iterations (NIST recommendation)

# UI settings
TYPING_DELAY = 0.01  # seconds per character
BANNER_COLOR = "cyan"

# Ensure journal directory exists
def init_journal_dir():
    """Create journal directory if it doesn't exist."""
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
