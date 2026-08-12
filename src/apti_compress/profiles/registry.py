"""
apti_compress.profiles.registry
================================
Profile registry and concrete profile implementations.

Bitrate math (Maximum ceiling budgets; actual file sizes vary dynamically with content complexity):
  Quality       → 2500k video + 128k audio = 2628 kbps total = ~18.80 MB/min (max budget ceiling)
  Balanced      → 1200k video +  96k audio = 1296 kbps total =  ~9.27 MB/min (max budget ceiling)
  Storage       →  450k video +  64k audio =  514 kbps total =  ~3.68 MB/min (max budget ceiling)
  Extreme       →  200k video +  48k audio =  248 kbps total =  ~1.77 MB/min (max budget ceiling)
  Ultra Extreme →  100k video +  32k audio =  132 kbps total =  ~0.94 MB/min (max budget ceiling)
"""

from typing import Union, Dict, Any, Optional
from .base import BaseProfile

DEFAULT_PROFILE_NAME = "balanced"


class BalancedProfile(BaseProfile):
    """Balanced profile — 720p @ 30fps, ~1200 kbps cap. Excellent sweet spot."""

    audio_bitrate = "96k"
    audio_rate = "44100"
    res_label = "720p"

    def __init__(self):
        super().__init__("balanced", "Balanced")

    def get_video_filter(self) -> str:
        return "scale='min(1280,iw)':-2"

    def get_codec_args(self, codec_type: str) -> list:
        if codec_type == "av1":
            return ["-c:v", "libaom-av1", "-crf", "28", "-b:v", "1200k",
                    "-maxrate", "1200k", "-bufsize", "2400k", "-cpu-used", "5"]
        elif codec_type == "hevc":
            return ["-c:v", "libx265", "-crf", "26", "-preset", "fast",
                    "-maxrate", "1200k", "-bufsize", "2400k"]
        else:  # h264
            return ["-c:v", "libx264", "-crf", "24", "-preset", "fast",
                    "-tune", "stillimage", "-maxrate", "1200k", "-bufsize", "2400k"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": "720p @ 30fps — ~1200 kbps cap, recommended sweet-spot",
        }


class StorageProfile(BaseProfile):
    """
    Storage Optimized — 540p @ 20fps.
    Proportional Bitrate & Text Readability Tier:
    Capped at 450 kbps with CRF 28-30 to ensure 540p text remains crisp & readable,
    avoiding severe pixelation artifacts while reducing file size significantly.
    """

    audio_bitrate = "64k"
    audio_rate = "22050"
    res_label = "540p"

    def __init__(self):
        super().__init__("storage", "Storage Optimized")

    def get_video_filter(self) -> str:
        return "scale=960:540:flags=lanczos,fps=20"

    def get_codec_args(self, codec_type: str) -> list:
        if codec_type == "av1":
            return ["-c:v", "libaom-av1", "-crf", "34", "-b:v", "450k",
                    "-maxrate", "450k", "-bufsize", "900k",
                    "-cpu-used", "6", "-row-mt", "1"]
        elif codec_type == "hevc":
            return ["-c:v", "libx265", "-crf", "30", "-preset", "fast",
                    "-maxrate", "450k", "-bufsize", "900k",
                    "-x265-params", "aq-mode=3:no-sao=1"]
        else:  # h264
            return ["-c:v", "libx264", "-crf", "28", "-preset", "fast",
                    "-tune", "stillimage", "-maxrate", "450k", "-bufsize", "900k"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": "540p @ 20fps — ~450 kbps cap, compact size with readable text",
        }


class QualityProfile(BaseProfile):
    """Quality-optimized profile — 1080p @ 30fps, highest clarity, ~2.5 Mbps cap."""

    audio_bitrate = "128k"
    audio_rate = "44100"
    res_label = "1080p"

    def __init__(self):
        super().__init__("quality", "Quality Optimized")

    def get_video_filter(self) -> str:
        return "scale='min(1920,iw)':-2"

    def get_codec_args(self, codec_type: str) -> list:
        if codec_type == "av1":
            return ["-c:v", "libaom-av1", "-crf", "24", "-b:v", "2500k",
                    "-maxrate", "2500k", "-bufsize", "5000k", "-cpu-used", "3"]
        elif codec_type == "hevc":
            return ["-c:v", "libx265", "-crf", "22", "-preset", "medium",
                    "-maxrate", "2500k", "-bufsize", "5000k"]
        else:  # h264
            return ["-c:v", "libx264", "-crf", "20", "-preset", "medium",
                    "-tune", "stillimage", "-maxrate", "2500k", "-bufsize", "5000k"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": "1080p @ 30fps — highest quality, ~2.5 Mbps cap",
        }


class ExtremeProfile(BaseProfile):
    """
    Extreme Compression — 360p @ 15fps.
    Heavy compression tier: ~200 kbps video cap (248 kbps total). Optimized for compact size.
    """

    audio_bitrate = "48k"
    audio_rate = "16000"
    res_label = "360p"

    def __init__(self):
        super().__init__("extreme", "Extreme Compression")

    def get_video_filter(self) -> str:
        return "scale=640:360:flags=lanczos,fps=15"

    def get_codec_args(self, codec_type: str) -> list:
        if codec_type == "av1":
            return [
                "-c:v", "libaom-av1",
                "-crf", "36",
                "-b:v", "200k",
                "-maxrate", "200k", "-bufsize", "400k",
                "-cpu-used", "6",
                "-row-mt", "1",
            ]
        elif codec_type == "hevc":
            return [
                "-c:v", "libx265",
                "-crf", "32",
                "-preset", "fast",
                "-maxrate", "200k", "-bufsize", "400k",
                "-x265-params", "aq-mode=3:no-sao=1",
            ]
        else:  # h264
            return [
                "-c:v", "libx264",
                "-crf", "30",
                "-preset", "fast",
                "-tune", "stillimage",
                "-maxrate", "200k", "-bufsize", "400k",
            ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": "360p @ 15fps — ~200 kbps cap, text-optimized extreme compression",
        }


class CustomProfile(BaseProfile):
    """Custom profile with user-specified parameters."""

    def __init__(
        self,
        resolution: str = None,
        fps: int = None,
        crf: int = None,
        audio_bitrate: str = None,
        audio_rate: str = None,
        maxrate: str = None,
    ):
        super().__init__("custom", "Custom Configuration")
        self.resolution = resolution
        self.fps = fps
        self.crf = crf
        self.audio_bitrate = audio_bitrate or "96k"
        self.audio_rate = audio_rate or "44100"
        self._maxrate = maxrate  # optional hard cap

    @property
    def res_label(self) -> str:
        if self.resolution:
            return self.resolution.split("x")[-1] + "p" if "x" in self.resolution else self.resolution
        return "custom"

    def get_video_filter(self) -> str:
        parts = []
        if self.resolution:
            width, height = self.resolution.split("x")
            parts.append(f"scale={width}:{height}:flags=lanczos")
        if self.fps:
            parts.append(f"fps={self.fps}")
        return ",".join(parts) if parts else "scale='min(960,iw)':-2"

    def get_codec_args(self, codec_type: str) -> list:
        crf_val = self.crf if self.crf else 28
        cap = ["-maxrate", self._maxrate, "-bufsize", str(int(self._maxrate.replace("k","")) * 2) + "k"] \
              if self._maxrate else []
        if codec_type == "av1":
            return ["-c:v", "libaom-av1", "-crf", str(crf_val), "-b:v", "0", "-cpu-used", "5"] + cap
        elif codec_type == "hevc":
            return ["-c:v", "libx265", "-crf", str(crf_val), "-preset", "fast"] + cap
        else:  # h264
            return ["-c:v", "libx264", "-crf", str(crf_val), "-preset", "fast"] + cap

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": "Custom user configuration",
            "resolution": self.resolution,
            "fps": self.fps,
            "crf": self.crf,
            "audio_bitrate": self.audio_bitrate,
            "audio_rate": self.audio_rate,
        }


class UltraExtremeProfile(BaseProfile):
    """
    Ultra Extreme Compression — 240p @ 12fps.
    Emergency bandwidth tier: ~60 kbps cap. For maximum possible file size savings.
    """

    audio_bitrate = "32k"
    audio_rate = "16000"
    res_label = "240p"

    def __init__(self):
        super().__init__("ultra_extreme", "Ultra Extreme")

    def get_video_filter(self) -> str:
        return "scale=426:240:flags=lanczos,fps=12"

    def get_codec_args(self, codec_type: str) -> list:
        if codec_type == "av1":
            return [
                "-c:v", "libaom-av1",
                "-crf", "42",
                "-b:v", "100k",
                "-maxrate", "100k", "-bufsize", "200k",
                "-cpu-used", "6",
                "-row-mt", "1",
            ]
        elif codec_type == "hevc":
            return [
                "-c:v", "libx265",
                "-crf", "38",
                "-preset", "fast",
                "-maxrate", "100k", "-bufsize", "200k",
                "-x265-params", "aq-mode=3:no-sao=1",
            ]
        else:  # h264
            return [
                "-c:v", "libx264",
                "-crf", "36",
                "-preset", "fast",
                "-tune", "stillimage",
                "-maxrate", "100k", "-bufsize", "200k",
            ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": "240p @ 12fps — ~100 kbps cap, maximum storage priority with clean structure",
        }


# Profile registry
_PROFILES: Dict[str, BaseProfile] = {
    "balanced": BalancedProfile(),
    "storage": StorageProfile(),
    "quality": QualityProfile(),
    "extreme": ExtremeProfile(),
    "ultra_extreme": UltraExtremeProfile(),
}


def get_profile(name_or_obj: Union[str, BaseProfile]) -> BaseProfile:
    """Get profile by name or return the profile object itself."""
    if isinstance(name_or_obj, BaseProfile):
        return name_or_obj
    if name_or_obj in _PROFILES:
        return _PROFILES[name_or_obj]
    raise ValueError(f"Unknown profile: {name_or_obj}. Available: {list(_PROFILES.keys())}")


def list_profiles() -> list:
    """Return list of available profile names."""
    return list(_PROFILES.keys())
