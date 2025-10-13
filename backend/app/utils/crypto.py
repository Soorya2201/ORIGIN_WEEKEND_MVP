"""Cryptographic utility functions."""

import hashlib
import secrets
from typing import str


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_sha256(data: bytes) -> str:
    """Generate SHA256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def hash_sha256_string(text: str) -> str:
    """Generate SHA256 hash of text string."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
