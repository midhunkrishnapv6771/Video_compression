"""
apti_compress.core
==================
Core encoding logic and FFmpeg binary management.
"""

from .ffmpeg_manager import (
    get_ffmpeg_bin,
    auto_install_ffmpeg,
    check_encoder_support,
    verify_video_input,
    get_ffmpeg_version,
)
from .encoder import (
    encode_single_variant,
    encode_dual_bundle,
)

__all__ = [
    "get_ffmpeg_bin",
    "auto_install_ffmpeg",
    "check_encoder_support",
    "verify_video_input",
    "get_ffmpeg_version",
    "encode_single_variant",
    "encode_dual_bundle",
]
