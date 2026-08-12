#!/usr/bin/env python3
"""
main.py - Unified Entry Point for AptiTalent Screen Recording Compression Engine
==================================================================================
Usage:
  python main.py compress -i video.mp4 -p balanced
  python main.py benchmark -d ./Sample_Videos -p all
  python main.py list-profiles
  python main.py setup-ffmpeg
"""

import sys
from pathlib import Path

# Add src/ to sys.path so apti_compress is importable regardless of installation state
_SRC_DIR = Path(__file__).resolve().parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from apti_compress.cli import main

if __name__ == "__main__":
    sys.exit(main())
