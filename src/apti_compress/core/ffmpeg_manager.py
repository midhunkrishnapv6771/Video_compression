"""
apti_compress.core.ffmpeg_manager
=================================
Manages FFmpeg and FFprobe binary location, automatic static installation, encoder support detection, and video validation.
"""

import os
import sys
import shutil
import zipfile
import logging
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any

from ..utils.hash import verify_file_sha256

logger = logging.getLogger("apti_compress.ffmpeg")

_SCRIPT_DIR = Path(__file__).resolve().parents[3]
_LOCAL_FFMPEG = _SCRIPT_DIR / "ffmpeg_bin" / "ffmpeg.exe"

_FFMPEG_ZIP_URL = (
    "https://github.com/GyanD/codexffmpeg/releases/download/"
    "7.1.1/ffmpeg-7.1.1-essentials_build.zip"
)

_FFMPEG_ZIP_EXPECTED_SHA256: Optional[str] = None


def _show_progress(block_num: int, block_size: int, total_size: int) -> None:
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 // total_size)
        bar = "=" * (pct // 5) + "-" * (20 - pct // 5)
        mb_done = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(
            f"\r  Downloading FFmpeg: [{bar}] {pct}%  "
            f"({mb_done:.1f} / {mb_total:.1f} MB)   ",
            end="",
            flush=True,
        )
    if downloaded >= total_size:
        print()


def auto_install_ffmpeg() -> str:
    """Download and extract official static FFmpeg release if missing."""
    ffmpeg_dir = _SCRIPT_DIR / "ffmpeg_bin"
    ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"

    if ffmpeg_exe.is_file():
        return str(ffmpeg_exe)

    print()
    print("=" * 60)
    print("  FFmpeg binary not found locally.")
    print("  Downloading official static release. Please wait...")
    print("=" * 60)

    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    zip_path = ffmpeg_dir / "ffmpeg_download.zip"

    try:
        urllib.request.urlretrieve(_FFMPEG_ZIP_URL, zip_path, reporthook=_show_progress)
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"\n[ERROR] Could not download FFmpeg automatically.\n"
            f"Details: {e}\n\n"
            f"Manual install: Download from https://ffmpeg.org/download.html\n"
            f"and place ffmpeg.exe in: {ffmpeg_dir}"
        ) from e

    download_hash = verify_file_sha256(zip_path)
    logger.info(f"[security] Downloaded FFmpeg package SHA256: {download_hash[:16]}...")
    if _FFMPEG_ZIP_EXPECTED_SHA256 and download_hash != _FFMPEG_ZIP_EXPECTED_SHA256:
        try:
            os.unlink(zip_path)
        except OSError:
            pass
        raise RuntimeError(
            f"FFmpeg download integrity check failed!\n"
            f"Expected: {_FFMPEG_ZIP_EXPECTED_SHA256}\n"
            f"Got:      {download_hash}"
        )

    print("  Extracting binary...", end="", flush=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            candidates = [n for n in zf.namelist() if n.endswith("bin/ffmpeg.exe")]
            if not candidates:
                raise RuntimeError("ffmpeg.exe not found inside downloaded package.")
            zf.extract(candidates[0], ffmpeg_dir / "_extracted")

        extracted_exe = ffmpeg_dir / "_extracted" / candidates[0]
        extracted_exe.replace(ffmpeg_exe)
        shutil.rmtree(ffmpeg_dir / "_extracted", ignore_errors=True)
    finally:
        try:
            zip_path.unlink(missing_ok=True)
        except Exception:
            pass

    print(" Done!")
    print(f"  FFmpeg saved to: {ffmpeg_exe}")
    print("=" * 60)
    print()
    return str(ffmpeg_exe)


def get_ffmpeg_bin() -> str:
    """Resolve path to local or system FFmpeg binary."""
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    if _LOCAL_FFMPEG.is_file():
        return str(_LOCAL_FFMPEG)
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    return auto_install_ffmpeg()


def check_encoder_support(ffmpeg_bin: str) -> Dict[str, bool]:
    """Inspect exact encoders available in local FFmpeg build."""
    try:
        res = subprocess.run(
            [ffmpeg_bin, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        return {
            "av1": "libaom-av1" in res.stdout,
            "hevc": "libx265" in res.stdout,
            "h264": "libx264" in res.stdout,
        }
    except Exception:
        return {"av1": False, "hevc": False, "h264": True}


def verify_video_input(ffmpeg_bin: str, input_path: str) -> float:
    """Pre/post-validate video file using ffprobe and return duration in seconds."""
    ffprobe = ffmpeg_bin.replace("ffmpeg.exe", "ffprobe.exe").replace("ffmpeg", "ffprobe")
    if not shutil.which(ffprobe) and not os.path.isfile(ffprobe):
        ffprobe = "ffprobe"

    try:
        res = subprocess.run(
            [
                ffprobe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception:
        pass
    return 0.0


def get_ffmpeg_version(ffmpeg: str) -> str:
    """Extract FFmpeg version header string."""
    try:
        res = subprocess.run([ffmpeg, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        first_line = res.stdout.splitlines()[0] if res.stdout else "Unknown FFmpeg"
        return first_line
    except Exception:
        return "FFmpeg 7.1.1 (Static)"
