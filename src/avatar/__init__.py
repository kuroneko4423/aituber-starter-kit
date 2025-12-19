"""Avatar control module for VTube Studio and other avatar software."""

from .base import BaseAvatarController
from .vtube_studio import VTubeStudioController

__all__ = [
    "BaseAvatarController",
    "VTubeStudioController",
]
