"""
Cryptographic utilities for encryption/decryption and key derivation.
Uses AES-256-GCM for authenticated encryption and PBKDF2 for key derivation.
"""

import os
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import config


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit AES key from a passphrase using PBKDF2-SHA256.
    
    Args:
        passphrase: Master passphrase (string)
        salt: Random salt bytes for key derivation
        
    Returns:
        32-byte key suitable for AES-256
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=config.ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(passphrase.encode())


def generate_salt() -> bytes:
    """Generate a random salt for key derivation."""
    return os.urandom(config.SALT_LENGTH)


def generate_iv() -> bytes:
    """Generate a random IV for AES encryption."""
    return os.urandom(config.IV_LENGTH)


def encrypt_data(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt plaintext using AES-256-GCM.
    
    Args:
        plaintext: Data to encrypt (bytes)
        key: 32-byte AES key
        
    Returns:
        Encrypted blob containing IV + ciphertext + tag
    """
    iv = generate_iv()
    cipher = AESGCM(key)
    
    # GCM mode provides authenticated encryption (includes integrity tag)
    ciphertext = cipher.encrypt(iv, plaintext, None)
    
    # Return IV + ciphertext (tag is included in GCM ciphertext)
    return iv + ciphertext


def decrypt_data(ciphertext_blob: bytes, key: bytes) -> bytes:
    """
    Decrypt ciphertext using AES-256-GCM.
    
    Args:
        ciphertext_blob: Encrypted blob (IV + ciphertext + tag)
        key: 32-byte AES key
        
    Returns:
        Decrypted plaintext (bytes)
        
    Raises:
        cryptography.exceptions.InvalidTag: If authentication fails
    """
    iv = ciphertext_blob[:config.IV_LENGTH]
    ciphertext = ciphertext_blob[config.IV_LENGTH:]
    
    cipher = AESGCM(key)
    plaintext = cipher.decrypt(iv, ciphertext, None)
    
    return plaintext
