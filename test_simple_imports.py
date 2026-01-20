"""Simple test to check if modules can be imported."""
import sys
import os

# Add project root to path
sys.path.insert(0, r'C:\Users\pinolo-streaming\github\InspektLine')

print("Starting import tests...")

try:
    print("1. Importing styles...")
    from gui.styles import DarkTheme, StyleSheets
    print("   SUCCESS - Styles imported")
except Exception as e:
    print(f"   FAILED - {e}")
    sys.exit(1)

try:
    print("2. Importing base settings...")
    from gui.pages.settings.base import BaseSettingsSection
    print("   SUCCESS - BaseSettingsSection imported")
except Exception as e:
    print(f"   FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("3. Importing camera settings...")
    from gui.pages.settings.camera import CameraSettings
    print("   SUCCESS - CameraSettings imported")
except Exception as e:
    print(f"   FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("4. Importing all settings modules...")
    from gui.pages.settings import (
        CameraSettings, DetectionSettings, NotificationsSettings,
        SystemSettings, NetworkSettings, DatabaseSettings,
        SecuritySettings, UserSettings
    )
    print("   SUCCESS - All settings modules imported")
except Exception as e:
    print(f"   FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("5. Importing settings page...")
    from gui.pages.settings_page import SettingsPage
    print("   SUCCESS - SettingsPage imported")
except Exception as e:
    print(f"   FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All imports successful!")
print("The settings module restructuring is complete and working.")

