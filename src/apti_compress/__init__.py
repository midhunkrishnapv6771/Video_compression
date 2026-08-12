"""
apti_compress
=============
Production Dual-Store Video Compression Engine & Quality Benchmark Harness (AptiTalent).

Modules:
  - core: Encoding pipeline and FFmpeg management.
  - profiles: Compression profile strategy definitions (Balanced, Storage, Quality).
  - metrics: SSIM / PSNR visual quality evaluation.
  - benchmarks: Multi-content automated benchmark harness.
  - utils: Security sanitization and hashing utilities.
"""

from .core import encode_video, encode_dual_bundle, encode_single_variant, get_ffmpeg_bin
from .profiles import get_profile, list_profiles, BaseProfile
from .metrics import compute_ssim_psnr, evaluate_quality_gate
from .benchmarks import run_suite

__version__ = "1.0.0"

__all__ = [
    "encode_video",
    "encode_dual_bundle",
    "encode_single_variant",
    "get_ffmpeg_bin",
    "get_profile",
    "list_profiles",
    "BaseProfile",
    "compute_ssim_psnr",
    "evaluate_quality_gate",
    "run_suite",
]
