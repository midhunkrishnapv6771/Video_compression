"""
apti_compress.cli
=================
Unified Command-Line Interface (CLI) dispatcher for apti-compress.
Supports subcommands: `compress`, `benchmark`, `list-profiles`, and `setup-ffmpeg`.
"""

import sys
import argparse
from typing import List, Optional

from .core import encode_video, auto_install_ffmpeg, get_ffmpeg_bin
from .profiles import list_profiles, CustomProfile
from .benchmarks import run_suite, CONTENT_CATEGORIES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apti-compress",
        description="AptiTalent Configurable Video Compression Engine & Benchmark Suite",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # Subcommand: compress
    p_compress = subparsers.add_parser("compress", help="Compress a single video file")
    p_compress.add_argument("-i", "--input", required=True, type=str, help="Path to raw video file")
    p_compress.add_argument("-p", "--profile", type=str, default="balanced", choices=["balanced", "storage", "quality", "extreme", "custom"],
                            help="Compression profile strategy (default: balanced)")
    p_compress.add_argument("-o", "--output-dir", type=str, default=None, help="Output directory path")
    p_compress.add_argument("--overwrite", action="store_true", help="Force re-encode if output exists")
    p_compress.add_argument("--resolution", type=str, default=None, help="Custom resolution (e.g., 1280x720)")
    p_compress.add_argument("--fps", type=int, default=None, help="Custom FPS (e.g., 30)")
    p_compress.add_argument("--crf", type=int, default=None, help="Custom CRF value (18-40)")
    p_compress.add_argument("--audio-bitrate", type=str, default=None, help="Custom audio bitrate (e.g., 128k)")

    # Subcommand: benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run multi-content quality benchmark suite")
    p_bench.add_argument("-d", "--dataset-dir", type=str, default="./Sample_Videos",
                         help="Folder containing sample videos (default: ./Sample_Videos)")
    p_bench.add_argument("-p", "--profile", type=str, default="all",
                         help="Profile strategy to run ('balanced', 'storage', 'quality', or 'all')")

    # Subcommand: list-profiles
    subparsers.add_parser("list-profiles", help="List registered compression profile strategies")

    # Subcommand: setup-ffmpeg
    subparsers.add_parser("setup-ffmpeg", help="Verify or download static FFmpeg release")

    # Subcommand: server
    p_server = subparsers.add_parser("server", help="Start the educational video compression web application")
    p_server.add_argument("--port", type=int, default=8765, help="Port to run server on (default: 8765)")
    p_server.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")

    return parser


def main(args_list: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(args_list)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "compress":
        try:
            # Check if using custom configuration
            if args.profile == "custom" or args.resolution or args.fps or args.crf or args.audio_bitrate:
                profile = CustomProfile(
                    resolution=args.resolution,
                    fps=args.fps,
                    crf=args.crf,
                    audio_bitrate=args.audio_bitrate
                )
            else:
                from .profiles import get_profile
                profile = get_profile(args.profile)
            
            res = encode_video(
                input_path=args.input,
                profile_name_or_obj=profile,
                output_dir=args.output_dir,
                overwrite=args.overwrite,
            )
            print()
            print("  [OK] Compression Summary:")
            print(f"       Profile Mode:    {res['profile'].upper()}")
            print(f"       Original size:   {res['orig_size_mb']:.2f} MB")
            print(f"       Output ({res['output_codec'].upper()}):    {res['output_size_mb']:.2f} MB")
            print(f"       Execution Time:  {res['elapsed_sec']:.1f} seconds")
            print(f"       Output Folder:   {res['bundle_dir']}")
            print(f"       Run Metadata:    {res['benchmark_log']}")
            print()
            return 0
        except Exception as e:
            print(f"\n  [ERROR] {e}\n")
            return 1

    elif args.command == "benchmark":
        profs = ["balanced", "storage", "quality"] if args.profile.lower() == "all" else [args.profile.lower()]
        run_suite(args.dataset_dir, profs)
        return 0

    elif args.command == "list-profiles":
        from .profiles import get_profile
        print()
        print("Registered Compression Profiles:")
        print("-" * 60)
        for name in list_profiles():
            p = get_profile(name).to_dict()
            print(f"  • Key:          {p['name']}")
            print(f"    Name:         {p['display_name']}")
            print(f"    Description:  {p['description']}")
            print("-" * 60)
        print()
        return 0

    elif args.command == "setup-ffmpeg":
        exe = get_ffmpeg_bin()
        print(f"\n[OK] FFmpeg is ready for use at: {exe}\n")
        return 0

    elif args.command == "server":
        from .server import run_server
        run_server(host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
