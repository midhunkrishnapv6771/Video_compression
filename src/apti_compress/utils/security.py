"""
apti_compress.utils.security
============================
Provides path sanitization and Windows reserved device name safeguards.
"""

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


def sanitize_filename(name: str) -> str:
    """Sanitize string to prevent path traversal, shell issues, and Windows reserved names."""
    clean = "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()
    if clean.upper() in WINDOWS_RESERVED_NAMES:
        clean = f"clip_{clean}"
    return clean or "video_clip"
