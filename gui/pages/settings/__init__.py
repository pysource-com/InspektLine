"""Settings modules for InspektLine GUI."""

from .base import BaseSettingsSection
from .camera import CameraSettings
from .detection import DetectionSettings
from .notifications import NotificationsSettings
from .system import SystemSettings
from .network import NetworkSettings
from .database import DatabaseSettings
from .security import SecuritySettings
from .user import UserSettings

__all__ = [
    'BaseSettingsSection',
    'CameraSettings',
    'DetectionSettings',
    'NotificationsSettings',
    'SystemSettings',
    'NetworkSettings',
    'DatabaseSettings',
    'SecuritySettings',
    'UserSettings',
]

