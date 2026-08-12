"""
apti_compress.server
====================
Tutor Video Compressor Web Server Package (FastAPI).
"""

from .compressor_server import app, run_server

__all__ = ["app", "run_server"]
