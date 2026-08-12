"""
apti_compress.server.compressor_server
========================================
Tutor Video Compression Web Server (FastAPI).
Local web server serving the AptiTalent tutor video compression interface.
Starts on http://localhost:8765.
"""

import os
import sys
import json
import asyncio
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

_SERVER_DIR = Path(__file__).resolve().parent
_SRC_DIR = _SERVER_DIR.parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from apti_compress.core import encode_dual_bundle, get_ffmpeg_bin
from apti_compress.profiles import get_profile, CustomProfile

app = FastAPI(title="AptiTalent Tutor Video Compressor Engine")

# Resolve project root: src/apti_compress/server/ -> 3 levels up
_SERVER_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SERVER_DIR.parents[2]
_PUBLIC_DIR = _PROJECT_ROOT / "public"
_COMPRESSED_DIR = _PROJECT_ROOT / "Compressed"
_COMPRESSED_DIR.mkdir(parents=True, exist_ok=True)

if _PUBLIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_PUBLIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index_file = _PUBLIC_DIR / "compress.html"
    if not index_file.exists():
        return HTMLResponse("<h2>Error: public/compress.html not found</h2>", status_code=404)
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))


@app.get("/api/status")
async def check_status():
    try:
        ffmpeg_bin = get_ffmpeg_bin()
        return {"status": "online", "ffmpeg": True, "ffmpeg_path": ffmpeg_bin}
    except Exception as e:
        return {"status": "degraded", "ffmpeg": False, "error": str(e)}


@app.get("/api/presets")
async def get_presets():
    return {
        "balanced": {"label": "Balanced", "description": "720p @ 30fps — Recommended sweet-spot"},
        "storage": {"label": "Storage Optimized", "description": "540p @ 20fps — Compact size, readable text"},
        "extreme": {"label": "Extreme Compression", "description": "360p @ 15fps — High compression"},
        "ultra_extreme": {"label": "Ultra Extreme", "description": "240p @ 12fps — Maximum storage priority"},
    }


@app.post("/api/compress")
async def compress_video(
    file: UploadFile = File(...),
    quality: str = Form("balanced"),
    codec: str = Form("auto"),
    custom_resolution: str = Form(None),
    custom_fps: int = Form(None),
    custom_crf: int = Form(None),
    custom_bitrate: str = Form(None)
):
    """
    Receives video file, saves to temporary location, compresses video using dual-store encoding,
    and returns metadata JSON.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No video file provided.")
        
    ext = Path(file.filename).suffix.lower()
    if ext not in [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".ts"]:
        raise HTTPException(status_code=400, detail=f"Unsupported video format: {ext}")
        
    # Create temp input file
    temp_dir = Path(tempfile.gettempdir()) / "apti_compress_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_input_path = temp_dir / f"upload_{file.filename}"
    
    with open(temp_input_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    try:
        # Check if using custom configuration
        if custom_resolution or custom_fps or custom_crf or custom_bitrate:
            profile_name = "custom"
            # Create custom profile
            profile = CustomProfile(
                resolution=custom_resolution if custom_resolution else None,
                fps=int(custom_fps) if custom_fps else None,
                crf=int(custom_crf) if custom_crf else None,
                audio_bitrate=custom_bitrate if custom_bitrate else None
            )
        else:
            # Map web preset names to profile names
            profile_map = {
                "high": "quality",
                "balanced": "balanced",
                "max": "storage",
                "storage": "storage",
                "quality": "quality",
                "extreme": "extreme",
                "ultra_extreme": "ultra_extreme",
            }
            profile_name = profile_map.get(quality, "balanced")
            profile = get_profile(profile_name)
        
        # Use dual-store encoding offloaded to background threadpool
        res = await asyncio.to_thread(
            encode_dual_bundle,
            input_path=str(temp_input_path),
            output_dir=str(_COMPRESSED_DIR),
            profile_name_or_obj=profile,
            overwrite=True,
            preferred_codec=codec if codec != "auto" else None
        )
        
        try:
            temp_input_path.unlink(missing_ok=True)
        except Exception:
            pass
            
        # Calculate savings from primary codec
        orig_mb = res["orig_size_mb"]
        primary_mb = res["primary_size_mb"]
        fallback_mb = res["fallback_size_mb"]
        total_mb = res["total_stored_mb"]
        reduction_pct = ((orig_mb - primary_mb) / orig_mb * 100) if orig_mb > 0 else 0.0
        
        return JSONResponse({
            "success": True,
            "result": {
                "output_path": res["primary_path"],
                "filename": Path(res["primary_path"]).name,
                "orig_mb": round(orig_mb, 2),
                "output_mb": round(primary_mb, 2),
                "fallback_mb": round(fallback_mb, 2) if fallback_mb else 0,
                "total_mb": round(total_mb, 2),
                "reduction_pct": round(reduction_pct, 1),
                "elapsed_sec": round(res["elapsed_sec"], 1),
                "preset": profile_name,
                "primary_codec": res["primary_codec"],
                "bundle_dir": res["bundle_dir"]
            }
        })
    except Exception as e:
        try:
            temp_input_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/open-folder")
async def open_compressed_folder():
    """Opens the local Compressed folder in Windows File Explorer."""
    try:
        folder_path = str(_COMPRESSED_DIR.resolve())
        if sys.platform == "win32":
            os.startfile(folder_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", folder_path])
        else:
            subprocess.run(["xdg-open", folder_path])
        return {"success": True, "message": "Folder opened"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_server(host: str = "127.0.0.1", port: int = 8765):
    print("=" * 65)
    print("  🚀 AptiTalent Tutor Video Compressor Server Starting...")
    print(f"  🌐 URL: http://{host}:{port}")
    print("=" * 65)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
