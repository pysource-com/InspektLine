"""Test script to verify settings module imports."""

import sys
import traceback

print("=" * 60)
print("Testing Settings Module Imports")
print("=" * 60)

# Test 1: Import styles
print("\n1. Testing styles import...")
try:
    from gui.styles import DarkTheme, StyleSheets
    print("   ✓ Styles imported successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    traceback.print_exc()

# Test 2: Import base
print("\n2. Testing base settings import...")
try:
    from gui.pages.settings.base import BaseSettingsSection
    print("   ✓ BaseSettingsSection imported successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    traceback.print_exc()

# Test 3: Import camera settings
print("\n3. Testing camera settings import...")
try:
    from gui.pages.settings.camera import CameraSettings
    print("   ✓ CameraSettings imported successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    traceback.print_exc()

# Test 4: Import detection settings
print("\n4. Testing detection settings import...")
try:
    from gui.pages.settings.detection import DetectionSettings
    print("   ✓ DetectionSettings imported successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    traceback.print_exc()

# Test 5: Import notifications settings
print("\n5. Testing notifications settings import...")
try:
    from gui.pages.settings.notifications import NotificationsSettings
    print("   ✓ NotificationsSettings imported successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    traceback.print_exc()

# Test 6: Import all from settings module
print("\n6. Testing settings module __init__ import...")
try:
    from gui.pages.settings import (
        CameraSettings, DetectionSettings, NotificationsSettings,
        SystemSettings, NetworkSettings, DatabaseSettings,
        SecuritySettings, UserSettings
    )
    print("   ✓ All settings modules imported successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    traceback.print_exc()

# Test 7: Import settings page
print("\n7. Testing settings page import...")
try:
    from gui.pages.settings_page import SettingsPage
    print("   ✓ SettingsPage imported successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing complete!")
print("=" * 60)

