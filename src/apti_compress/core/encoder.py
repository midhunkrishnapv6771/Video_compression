"""
apti_compress.core.encoder
==========================
AptiTalent Educational Video Compression Engine.
Pipeline architecture for profile-driven video compression (AV1/HEVC/H.264).
"""

import os
import sys
import time
import json
import uuid
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Union, Tuple

from ..profiles import get_profile, BaseProfile, DEFAULT_PROFILE_NAME
from ..utils.security import sanitize_filename
from ..utils.hash import verify_file_sha256
from .ffmpeg_manager import (
    get_ffmpeg_bin,
    check_encoder_support,
    verify_video_input,
)

logger = logging.getLogger("apti_compress.encoder")

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

_SCRIPT_DIR = Path(__file__).resolve().parents[3]
_OUTPUT_DIR = _SCRIPT_DIR / "Compressed"


def _safe_remove(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def _get_mime_codec(codec_type: str) -> str:
    """Return exact HTML5 MIME codec attribute based on actual generated codec."""
    if codec_type == "av1":
        return 'type="video/mp4; codecs=av01.0.05M.08"'
    elif codec_type == "hevc":
        return 'type="video/mp4; codecs=hvc1"'
    else:
        return 'type="video/mp4; codecs=avc1.42E01E"'


def encode_single_variant(
    ffmpeg: str,
    input_path: str,
    output_path: str,
    codec_type: str,
    profile: BaseProfile,
    retries: int = 1,
) -> Tuple[str, float]:
    """Encode single video variant driven generically by profile strategy object."""
    vf = profile.get_video_filter()
    codec_args = profile.get_codec_args(codec_type)

    attempt = 0
    last_err = ""
    while attempt <= retries:
        attempt += 1
        tmp_path = str(Path(output_path).parent / f"_tmp_{uuid.uuid4().hex}.mp4")

        cmd = [
            ffmpeg, "-y",
            "-i", input_path,
            "-vf", vf,
            *codec_args,
            "-c:a", "aac",
            "-b:a", profile.audio_bitrate,
            "-ar", profile.audio_rate,
            "-ac", "1",
            "-movflags", "+faststart",
            tmp_path,
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=600)
            if res.returncode != 0:
                _safe_remove(tmp_path)
                last_err = f"FFmpeg {codec_type} encode failed (code {res.returncode}):\n{res.stderr[-500:]}"
                if "Unknown encoder" in res.stderr or "Invalid argument" in res.stderr:
                    logger.error(f"[fatal] Permanent encoder error detected: {last_err}")
                    break
                if attempt <= retries:
                    logger.warning(f"[retry] Transient failure (attempt {attempt}/{retries+1}). Retrying...")
                    time.sleep(1)
                    continue
                break

            out_dur = verify_video_input(ffmpeg, tmp_path)
            if out_dur <= 0:
                _safe_remove(tmp_path)
                last_err = f"FFmpeg {codec_type} produced an unplayable output file."
                if attempt <= retries:
                    logger.warning(f"[retry] Output zero-duration check failed. Retrying...")
                    time.sleep(1)
                    continue
                break

            try:
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass
                shutil.move(tmp_path, output_path)
                final_out = output_path
            except (PermissionError, OSError):
                parent_dir = Path(output_path).parent
                stem_name = Path(output_path).stem
                ext_name = Path(output_path).suffix
                final_out = str(parent_dir / f"{stem_name}_{int(time.time())}{ext_name}")
                shutil.move(tmp_path, final_out)

            return final_out, os.path.getsize(final_out) / (1024 * 1024)
        except subprocess.TimeoutExpired:
            _safe_remove(tmp_path)
            last_err = f"Encoding process timed out (>10 min) for {codec_type}."
            if attempt <= retries:
                logger.warning(f"[retry] Timeout expired. Retrying...")
                time.sleep(1)
                continue
            break
        except Exception as e:
            _safe_remove(tmp_path)
            last_err = f"Exception during {codec_type} encode: {e}"
            if attempt <= retries:
                logger.warning(f"[retry] Exception during {codec_type} encode. Retrying...")
                time.sleep(1)
                continue
            break

    raise RuntimeError(last_err or f"Encoding failed for {codec_type} after {retries+1} attempts.")




def encode_video(
    input_path: str,
    output_dir: Optional[str] = None,
    profile_name_or_obj: Union[str, BaseProfile] = DEFAULT_PROFILE_NAME,
    overwrite: bool = False,
    preferred_codec: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Core video compression engine.
    Encodes video into a single optimized MP4 file using selected profile and codec.
    """
    t_start = time.time()
    input_path = str(Path(input_path).resolve())
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Video file not found: {input_path}")

    profile = profile_name_or_obj if isinstance(profile_name_or_obj, BaseProfile) else get_profile(profile_name_or_obj)

    orig_size = os.path.getsize(input_path)
    if orig_size == 0:
        raise ValueError(f"Input video file is empty (0 bytes): {input_path}")

    orig_size_mb = orig_size / (1024 * 1024)
    ffmpeg = get_ffmpeg_bin()
    encoders = check_encoder_support(ffmpeg)
    duration = verify_video_input(ffmpeg, input_path)

    raw_stem = Path(input_path).stem
    if raw_stem.startswith("upload_"):
        raw_stem = raw_stem[len("upload_"):]
    safe_stem = sanitize_filename(raw_stem) or "video"

    if output_dir is None:
        out_dir_path = _OUTPUT_DIR / f"{safe_stem}_{profile.name}"
    else:
        out_dir_path = Path(output_dir)

    out_dir_path.mkdir(parents=True, exist_ok=True)

    # Use preferred codec if specified and available, otherwise auto-select
    if preferred_codec and preferred_codec in encoders and encoders[preferred_codec]:
        primary_type = preferred_codec
    elif preferred_codec == "h264":
        primary_type = "h264"
    else:
        primary_type = "av1" if encoders["av1"] else ("hevc" if encoders["hevc"] else "h264")
    
    res_label = getattr(profile, "res_label", "auto")
    time_stamp = time.strftime("%H%M%S")
    primary_filename = f"{safe_stem}_{profile.name}_{res_label}_{primary_type}_{time_stamp}.mp4"
    primary_path = str(out_dir_path / primary_filename)
    meta_path = str(out_dir_path / f"{safe_stem}_{profile.name}_{res_label}_{time_stamp}_log.json")

    logger.info(f"[encoder] Launching [{profile.display_name}] | Codec: {primary_type.upper()} | File: {os.path.basename(input_path)}")

    # Encode single output file
    if not os.path.isfile(primary_path) or overwrite:
        logger.info(f"  -> Encoding ({primary_type.upper()})...")
        primary_path, s_prim = encode_single_variant(ffmpeg, input_path, primary_path, primary_type, profile=profile)
    else:
        s_prim = os.path.getsize(primary_path) / (1024 * 1024)

    elapsed_sec = time.time() - t_start

    # Persist structured run log
    run_log = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "profile": profile.to_dict(),
        "input_file": os.path.basename(input_path),
        "input_hash_sha256": verify_file_sha256(Path(input_path)),
        "input_size_mb": orig_size_mb,
        "input_duration_sec": duration,
        "codec": primary_type,
        "output_file": os.path.basename(primary_path),
        "output_size_mb": s_prim,
        "encoding_elapsed_sec": round(elapsed_sec, 2),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=2)

    logger.info(
        f"[encoder] [OK] Done [{profile.name.upper()}] | {primary_type.upper()}: {s_prim:.2f} MB "
        f"(was {orig_size_mb:.2f} MB) | {elapsed_sec:.1f}s"
    )

    return {
        "bundle_dir": str(out_dir_path),
        "profile": profile.name,
        "output_path": primary_path,
        "primary_path": primary_path,  # Kept for backward compatibility
        "output_codec": primary_type,
        "primary_codec": primary_type,  # Kept for backward compatibility
        "fallback_path": None,
        "benchmark_log": meta_path,
        "orig_size_mb": orig_size_mb,
        "output_size_mb": s_prim,
        "primary_size_mb": s_prim,     # Kept for backward compatibility
        "fallback_size_mb": 0.0,
        "total_stored_mb": s_prim,
        "duration_sec": duration,
        "elapsed_sec": elapsed_sec,
    }


def encode_dual_bundle(*args, **kwargs) -> Dict[str, Any]:
    """Alias for encode_video provided for backward compatibility."""
    return encode_video(*args, **kwargs)

