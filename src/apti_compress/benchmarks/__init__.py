"""
apti_compress.benchmarks
=========================
Multi-content automated benchmark harness.
Executes batch encoding across sample video datasets and evaluates visual quality (SSIM/PSNR),
compression ratio, and encoding throughput.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from ..core import encode_video
from ..metrics import compute_ssim_psnr

logger = logging.getLogger("apti_compress.benchmarks")

CONTENT_CATEGORIES = [
    "lecture",
    "screencast",
    "presentation",
    "demo",
]

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def run_suite(dataset_dir: str, profiles: List[str]) -> Dict[str, Any]:
    """
    Run multi-content benchmark suite across video dataset.
    
    Args:
        dataset_dir: Directory containing sample test videos.
        profiles: List of profile names (e.g. ['quality', 'balanced', 'storage', 'extreme']).
        
    Returns:
        Dict with benchmark results list and summary metadata.
    """
    dataset_path = Path(dataset_dir).resolve()
    if not dataset_path.exists() or not dataset_path.is_dir():
        print(f"\n[BENCHMARK] Dataset directory not found: {dataset_path}")
        print("  Place sample videos in the dataset folder to run automated quality benchmarks.\n")
        return {"results": [], "summary": f"Directory not found: {dataset_path}"}

    videos = [
        f for f in dataset_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not videos:
        print(f"\n[BENCHMARK] No supported video files found in: {dataset_path}")
        print("  Supported extensions: .mp4, .mov, .avi, .mkv, .webm\n")
        return {"results": [], "summary": "No video files found"}

    print("\n" + "=" * 80)
    print(f"  🎬 AptiCompress Benchmark Harness")
    print(f"  Dataset: {dataset_path} ({len(videos)} file(s))")
    print(f"  Profiles: {', '.join(profiles)}")
    print("=" * 80 + "\n")

    results = []

    for video_file in videos:
        for prof in profiles:
            print(f"  ▶ Benchmarking [{prof.upper()}] on {video_file.name}...")
            try:
                res = encode_video(
                    input_path=str(video_file),
                    profile_name_or_obj=prof,
                    overwrite=True
                )
                
                out_path = res.get("output_path") or res.get("primary_path")
                orig_mb = res["orig_size_mb"]
                out_mb = res.get("output_size_mb") or res.get("primary_size_mb", 0.0)
                reduction_pct = ((orig_mb - out_mb) / orig_mb * 100) if orig_mb > 0 else 0.0

                print(f"    Evaluating SSIM / PSNR visual quality metrics...")
                metrics = compute_ssim_psnr(str(video_file), out_path)

                item = {
                    "video": video_file.name,
                    "profile": prof,
                    "codec": res.get("output_codec") or res.get("primary_codec", "h264"),
                    "orig_size_mb": round(orig_mb, 2),
                    "output_size_mb": round(out_mb, 2),
                    "reduction_pct": round(reduction_pct, 1),
                    "elapsed_sec": round(res["elapsed_sec"], 1),
                    "ssim": metrics["ssim"],
                    "psnr": metrics["psnr"],
                }
                results.append(item)

            except Exception as e:
                logger.error(f"Failed benchmark run for {video_file.name} with profile {prof}: {e}")
                print(f"    ✖ Failed: {e}")

    # Output Markdown summary table
    if results:
        print("\n" + "=" * 85)
        print("  📊 BENCHMARK RESULTS SUMMARY")
        print("=" * 85)
        print(f"| {'Video File':<20} | {'Profile':<14} | {'Codec':<6} | {'Orig (MB)':<9} | {'Out (MB)':<8} | {'Saved %':<7} | {'Time (s)':<8} | {'SSIM':<6} | {'PSNR (dB)':<9} |")
        print("|" + "-"*22 + "|" + "-"*16 + "|" + "-"*8 + "|" + "-"*11 + "|" + "-"*10 + "|" + "-"*9 + "|" + "-"*10 + "|" + "-"*8 + "|" + "-"*11 + "|")
        
        for r in results:
            v_name = r['video'][:18] + '..' if len(r['video']) > 20 else r['video']
            ssim_str = f"{r['ssim']:<6.4f}" if r['ssim'] is not None else "N/A   "
            psnr_str = f"{r['psnr']:<9.2f}" if r['psnr'] is not None else "N/A      "
            print(
                f"| {v_name:<20} | {r['profile']:<14} | {r['codec'].upper():<6} | "
                f"{r['orig_size_mb']:<9.2f} | {r['output_size_mb']:<8.2f} | {r['reduction_pct']:<6.1f}% | "
                f"{r['elapsed_sec']:<8.1f} | {ssim_str} | {psnr_str} |"
            )
        print("=" * 85 + "\n")

    summary_str = f"Evaluated {len(results)} test run(s) across {len(videos)} video file(s)."
    return {"results": results, "summary": summary_str}
