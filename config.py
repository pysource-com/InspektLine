"""Application-level constants and defaults.

For runtime-configurable settings, see ``services.settings_service.SettingsService``.
"""

# Application metadata
APP_NAME = "InspektLine"
APP_VERSION = "2.0.0"
APP_TITLE = f"{APP_NAME} - Visual Inspection System"

# Camera defaults
CAMERA_INDEX = 0
CAMERA_TYPE = "usb-standard"

# Storage defaults
STORAGE_DIR = "storage"
DATABASE_NAME = "inspektline.db"
DATASET_DIR = "storage/dataset"
