"""Quick verification that camera preview is in settings."""

import sys
from PySide6.QtWidgets import QApplication
from gui.pages.settings_page import SettingsPage
from gui.pages.settings.camera import CameraSettings

# Test 1: Check if CameraSettings has preview methods
print("=" * 60)
print("VERIFICATION: Camera Settings Preview Implementation")
print("=" * 60)

# Check CameraSettings class
print("\n1. Checking CameraSettings class...")
methods_to_check = [
    '_init_split_layout',
    '_init_preview_panel',
    'start_preview',
    'stop_preview',
    '_update_preview_frame',
    'showEvent',
    'hideEvent'
]

for method in methods_to_check:
    has_method = hasattr(CameraSettings, method)
    status = "✅" if has_method else "❌"
    print(f"   {status} {method}")

# Test 2: Check if SettingsPage exists
print("\n2. Checking SettingsPage class...")
print(f"   ✅ SettingsPage imported successfully")

# Test 3: Try to instantiate CameraSettings
print("\n3. Testing CameraSettings instantiation...")
try:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    test_widget = CameraSettings()

    # Check for preview-related attributes
    has_preview_label = hasattr(test_widget, 'preview_label')
    has_preview_timer = hasattr(test_widget, 'preview_timer')
    has_split_layout = hasattr(test_widget, 'split_layout')
    has_settings_container = hasattr(test_widget, 'settings_container')
    has_preview_container = hasattr(test_widget, 'preview_container')

    print(f"   {'✅' if has_preview_label else '❌'} preview_label attribute")
    print(f"   {'✅' if has_preview_timer else '❌'} preview_timer attribute")
    print(f"   {'✅' if has_split_layout else '❌'} split_layout attribute")
    print(f"   {'✅' if has_settings_container else '❌'} settings_container attribute")
    print(f"   {'✅' if has_preview_container else '❌'} preview_container attribute")

    print("\n✅ CameraSettings instantiated successfully!")

except Exception as e:
    print(f"\n❌ Error instantiating CameraSettings: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print("\nIf all checks passed, the camera preview is properly implemented!")
print("Run your main application (gui.py) to see it in action.")

