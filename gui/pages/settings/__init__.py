"""Settings modules for InspektLine GUI."""

from .base import BaseSettingsSection
from .camera import CameraSettings
from .detection import DetectionSettings

__all__ = [
    'BaseSettingsSection',
    'CameraSettings',
    'DetectionSettings',
]

