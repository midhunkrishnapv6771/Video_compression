"""
apti_compress.profiles.base
===========================
Base profile class for compression strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseProfile(ABC):
    """Abstract base class for compression profiles."""
    
    def __init__(self, name: str, display_name: str):
        self.name = name
        self.display_name = display_name
    
    @abstractmethod
    def get_video_filter(self) -> str:
        """Return FFmpeg video filter string."""
        pass
    
    @abstractmethod
    def get_codec_args(self, codec_type: str) -> list:
        """Return codec-specific FFmpeg arguments."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize profile to dictionary."""
        pass
    
    # Default audio settings
    audio_bitrate = "128k"
    audio_rate = "44100"
    res_label = "auto"
