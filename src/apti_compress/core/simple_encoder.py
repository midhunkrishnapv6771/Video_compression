"""
apti_compress.core.simple_encoder
==================================
LEGACY: Simple H264 Smart Encoder for AptiTalent Educational Web UI.
Uses `-tune stillimage` and smart CRF presets optimized for educational screen recordings.

NOTE: This is a legacy implementation. The main encoder (encoder.py) uses the newer
progressive enhancement encoding architecture with AV1/HEVC/H.264 support via profiles.
Use encode_dual_bundle from encoder.py for new development.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from .ffmpeg_manager import get_ffmpeg_bin, verify_video_input
from ..utils.security import sanitize_filename

# Quality Preset Configuration Matrix for Screen Recordings
# Uses -tune stillimage for maximum text/code font clarity at low bitrates
QUALITY_PRESETS: Dict[str, Dict[str, Any]] = {
    "high": {
        "label": "High Quality",
        "crf": 22,
        "vf": "scale=w=1280:h=720:force_original_aspect_ratio=decrease,fps=30",
        "audio_bitrate": "128k",
        "description": "Best for detailed code & text videos (720p @ 30fps)"
    },
    "balanced": {
        "label": "Balanced (Recommended)",
        "crf": 28,
        "vf": "scale=w=960:h=540:force_original_aspect_ratio=decrease,fps=24",
        "audio_bitrate": "96k",
        "description": "Best balance of quality and storage savings (540p @ 24fps)"
    },
    "max": {
        "label": "Maximum Save",
        "crf": 34,
        "vf": "scale=w=640:h=360:force_original_aspect_ratio=decrease,fps=15",
        "audio_bitrate": "64k",
        "description": "Smallest possible file size for fast uploads (360p @ 15fps)"
    }
}


def simple_compress(
    input_path: str,
    output_dir: str,
    quality_preset: str = "balanced",
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Dict[str, Any]:
    """
    Perform a single smart H264 compression optimized for educational video uploads.
    
    Args:
        input_path: Path to the raw source video file.
        output_dir: Path to the directory where the output video will be saved.
        quality_preset: 'high', 'balanced', or 'max'. Default is 'balanced'.
        progress_callback: Optional callback(pct_0_to_100, message_string) for SSE progress updates.
        
    Returns:
        Dict with result metadata (output_path, orig_mb, output_mb, reduction_pct, elapsed_sec).
    """
    t_start = time.time()
    input_path = str(Path(input_path).resolve())
    
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input video file not found: {input_path}")
        
    orig_size_bytes = os.path.getsize(input_path)
    if orig_size_bytes == 0:
        raise ValueError("Input video file is empty (0 bytes).")
        
    orig_mb = orig_size_bytes / (1024 * 1024)
    preset_key = quality_preset.lower() if quality_preset.lower() in QUALITY_PRESETS else "balanced"
    cfg = QUALITY_PRESETS[preset_key]
    
    ffmpeg_bin = get_ffmpeg_bin()
    duration_sec = verify_video_input(ffmpeg_bin, input_path)
    if duration_sec <= 0:
        duration_sec = 60.0  # Fallback estimate if probe fails
        
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    
    stem = Path(input_path).stem
    safe_stem = sanitize_filename(stem)
    out_filename = f"{safe_stem}_{preset_key}_compressed.mp4"
    out_path = str(out_dir_path / out_filename)
    
    cmd = [
        ffmpeg_bin, "-y",
        "-i", input_path,
        "-vf", cfg["vf"],
        "-c:v", "libx264",
        "-preset", "medium",  # Changed from slow to medium for stability
        "-tune", "stillimage",
        "-crf", str(cfg["crf"]),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", cfg["audio_bitrate"],
        "-ac", "1",
        "-movflags", "+faststart",
        out_path
    ]
    
    if progress_callback:
        progress_callback(5, "Initializing FFmpeg encoder...")
    
    # Run FFmpeg with timeout to prevent hangs
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600  # 10 minute timeout
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg encoding timed out after 10 minutes")
    
    if result.returncode != 0:
        error_msg = f"FFmpeg encoding failed with exit code {result.returncode}"
        if result.stderr:
            error_msg += f"\nFFmpeg stderr: {result.stderr[-1000:]}"  # Last 1000 chars of error
        raise RuntimeError(error_msg)
        
    if not os.path.isfile(out_path):
        raise RuntimeError("Encoding finished but output file was not found.")
        
    out_size_bytes = os.path.getsize(out_path)
    out_mb = out_size_bytes / (1024 * 1024)
    elapsed_sec = time.time() - t_start
    reduction_pct = ((orig_mb - out_mb) / orig_mb * 100) if orig_mb > 0 else 0.0
    
    if progress_callback:
        progress_callback(100, "Compression complete!")
        
    return {
        "output_path": out_path,
        "filename": out_filename,
        "orig_mb": round(orig_mb, 2),
        "output_mb": round(out_mb, 2),
        "reduction_pct": round(reduction_pct, 1),
        "elapsed_sec": round(elapsed_sec, 1),
        "preset": cfg["label"]
    }
