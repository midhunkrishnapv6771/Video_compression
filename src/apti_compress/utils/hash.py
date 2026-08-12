"""
apti_compress.utils.hash
========================
Provides SHA-256 file hashing utilities for audit trails and integrity checks.
"""

import hashlib
from pathlib import Path
from typing import Union


def verify_file_sha256(file_path: Union[str, Path]) -> str:
    """Calculate SHA256 hash of a file."""
    path = Path(file_path)
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
