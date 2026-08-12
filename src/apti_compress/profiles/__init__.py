"""
apti_compress.profiles
======================
Compression profile strategy definitions for AptiTalent video encoding.
"""

from .base import BaseProfile
from .registry import get_profile, list_profiles, DEFAULT_PROFILE_NAME, CustomProfile

__all__ = [
    "BaseProfile",
    "get_profile",
    "list_profiles",
    "DEFAULT_PROFILE_NAME",
    "CustomProfile",
]
