"""
apti_compress.metrics
======================
SSIM / PSNR visual quality evaluation harness.
Calculates structural similarity (SSIM) and peak signal-to-noise ratio (PSNR)
between reference video and compressed video using FFmpeg filters.
Includes temporal framerate resampling and spatial resolution normalization.
"""

import re
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("apti_compress.metrics")


def _get_video_info(ffmpeg: str, video_path: str) -> Tuple[int, int, float]:
    """Get video width, height, and framerate using ffprobe."""
    ffprobe = str(Path(ffmpeg).parent / "ffprobe.exe")
    if not Path(ffprobe).exists():
        ffprobe = str(Path(ffmpeg).parent / "ffprobe")
    if not Path(ffprobe).exists():
        ffprobe = "ffprobe"

    cmd = [
        ffprobe, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "json", video_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            stream = data.get("streams", [{}])[0]
            w = int(stream.get("width", 1920))
            h = int(stream.get("height", 1080))
            fps_str = stream.get("r_frame_rate", "30/1")
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = float(num) / float(den) if float(den) > 0 else 30.0
            else:
                fps = float(fps_str)
            return w, h, fps
    except Exception:
        pass
    return 1920, 1080, 30.0


def compute_ssim_psnr(original_path: str, compressed_path: str, ffmpeg_bin: Optional[str] = None) -> Dict[str, Optional[float]]:
    """
    Compute real SSIM and PSNR metrics between original reference video and compressed video file.
    Applies spatial resolution scaling and temporal framerate normalization prior to metric calculation.
    
    Args:
        original_path: Path to reference (raw) video.
        compressed_path: Path to distorted (compressed) video.
        ffmpeg_bin: Optional explicit path to FFmpeg binary.
        
    Returns:
        Dict containing float values for 'ssim' (0.0 - 1.0) and 'psnr' (dB), or None if unmeasurable.
    """
    if not Path(original_path).is_file() or not Path(compressed_path).is_file():
        logger.warning("Files missing for SSIM/PSNR calculation. Returning None metrics.")
        return {"ssim": None, "psnr": None}

    if ffmpeg_bin is None:
        from ..core.ffmpeg_manager import get_ffmpeg_bin
        try:
            ffmpeg_bin = get_ffmpeg_bin()
        except Exception:
            ffmpeg_bin = "ffmpeg"

    w, h, fps = _get_video_info(ffmpeg_bin, original_path)

    # Filter graph with temporal alignment (fps=fps) and spatial scaling (scale=w:h)
    filter_graph_ssim = f"[0:v]scale={w}:{h},fps={fps:.2f}[dist];[1:v]fps={fps:.2f}[ref];[dist][ref]ssim"
    filter_graph_psnr = f"[0:v]scale={w}:{h},fps={fps:.2f}[dist];[1:v]fps={fps:.2f}[ref];[dist][ref]psnr"

    cmd_ssim = [
        ffmpeg_bin, "-y",
        "-i", compressed_path,
        "-i", original_path,
        "-filter_complex", filter_graph_ssim,
        "-f", "null", "-"
    ]

    cmd_psnr = [
        ffmpeg_bin, "-y",
        "-i", compressed_path,
        "-i", original_path,
        "-filter_complex", filter_graph_psnr,
        "-f", "null", "-"
    ]

    ssim_val: Optional[float] = None
    psnr_val: Optional[float] = None

    try:
        res_ssim = subprocess.run(cmd_ssim, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        ssim_match = re.search(r"SSIM\s+All:([0-9.]+)", res_ssim.stderr)
        if ssim_match:
            ssim_val = float(ssim_match.group(1))
    except Exception as e:
        logger.debug(f"SSIM filter execution failed: {e}")

    try:
        res_psnr = subprocess.run(cmd_psnr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        psnr_match = re.search(r"average:([0-9.]+)", res_psnr.stderr)
        if psnr_match:
            psnr_val = float(psnr_match.group(1))
    except Exception as e:
        logger.debug(f"PSNR filter execution failed: {e}")

    return {
        "ssim": round(ssim_val, 4) if ssim_val is not None else None,
        "psnr": round(psnr_val, 2) if psnr_val is not None else None
    }


def evaluate_quality_gate(metrics: dict, threshold: float = 0.90) -> bool:
    """Evaluate if visual quality metrics pass production Quality Gate (default SSIM >= 0.90)."""
    ssim = metrics.get("ssim")
    if ssim is None:
        return False
    return ssim >= threshold
