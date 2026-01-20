# Settings Module Quick Reference

## 📚 Quick Import Guide

```python
# Import the main settings page
from gui.pages import SettingsPage

# Import individual settings modules
from gui.pages.settings import (
    CameraSettings,
    DetectionSettings,
    NotificationsSettings,
    SystemSettings,
    NetworkSettings,
    DatabaseSettings,
    SecuritySettings,
    UserSettings
)

# Import base class for custom settings
from gui.pages.settings import BaseSettingsSection

# Import styling
from gui.styles import DarkTheme, StyleSheets
```

## 🚀 Quick Start Examples

### Create Settings Page
```python
# In your main window
self.settings_page = SettingsPage(parent=self)

# Add to layout or stacked widget
self.main_content.addWidget(self.settings_page)
```

### Get All Settings
```python
all_settings = self.settings_page.get_all_settings()
print(all_settings)
# Output: {
#     'camera': {'camera_type': 'USB Webcam', ...},
#     'detection': {'confidence_threshold': '85', ...},
#     ...
# }
```

### Load Settings
```python
saved_settings = {
    'camera': {
        'camera_type': 'Intel RealSense',
        'resolution': '1920 x 1080 (Full HD)',
        'autofocus': False
    },
    'detection': {
        'confidence_threshold': '90',
        'min_defect_size': '15'
    }
}
self.settings_page.load_all_settings(saved_settings)
```

### Access Specific Control (Legacy)
```python
# Direct property access
camera_type = self.settings_page.camera_type_combo.currentText()
confidence = self.settings_page.confidence_input.text()
```

### Listen to Setting Changes
```python
# In your main window, implement handler methods
def on_camera_type_changed(self, value):
    print(f"Camera type changed to: {value}")
    # Update camera hardware

def on_autofocus_changed(self, value):
    print(f"Autofocus {'enabled' if value else 'disabled'}")
    # Apply autofocus setting
```

## 📋 Settings Keys Reference

### Camera Settings
```python
{
    'camera_type': str,        # 'USB Webcam' or 'Intel RealSense'
    'camera_device': int,      # Device index
    'resolution': str,         # '1920 x 1080 (Full HD)', etc.
    'fps': str,               # '30 FPS', '60 FPS', etc.
    'autofocus': bool,        # True/False
    'manual_focus': int       # 0-255
}
```

### Detection Settings
```python
{
    'confidence_threshold': str,  # '85', '90', etc.
    'min_defect_size': str       # '10', '15', etc.
}
```

### Notifications Settings
```python
{
    'notifications_enabled': bool,    # True/False
    'sound_alerts': bool,            # True/False
    'email_enabled': bool,           # True/False
    'email_address': str,            # 'user@example.com'
    'notification_priority': str     # 'All Defects', 'Critical Only', etc.
}
```

### System Settings
```python
{
    'language': str,      # 'English', 'Deutsch', etc.
    'theme': str,        # 'Dark', 'Light', 'Auto'
    'auto_start': bool,  # True/False
    'auto_save': bool,   # True/False
    'log_level': str     # 'Debug', 'Info', 'Warning', etc.
}
```

### Network Settings
```python
{
    'remote_access': bool,    # True/False
    'api_port': str,         # '8080', etc.
    'streaming_port': str,   # '8081', etc.
    'protocol': str,         # 'HTTP', 'HTTPS', etc.
    'use_proxy': bool        # True/False
}
```

### Database Settings
```python
{
    'db_type': str,          # 'SQLite', 'PostgreSQL', etc.
    'db_host': str,          # 'localhost', '192.168.1.1', etc.
    'db_port': str,          # '5432', '3306', etc.
    'auto_backup': bool,     # True/False
    'backup_interval': str   # 'Daily', 'Weekly', etc.
}
```

### Security Settings
```python
{
    'authentication_enabled': bool,  # True/False
    'session_timeout': str,         # '30', '60', etc.
    'password_policy': str,         # 'Basic', 'Medium', 'Strong'
    'two_factor_auth': bool,        # True/False
    'data_encryption': bool,        # True/False
    'audit_logging': bool           # True/False
}
```

### User Settings
```python
{
    'username': str,        # 'admin', 'operator', etc.
    'full_name': str,      # 'John Doe'
    'user_email': str,     # 'john@example.com'
    'user_role': str       # 'Administrator', 'Operator', etc.
}
```

## 🔧 Common Operations

### Save Settings to JSON
```python
import json

settings = self.settings_page.get_all_settings()
with open('settings.json', 'w') as f:
    json.dump(settings, f, indent=2)
```

### Load Settings from JSON
```python
import json

with open('settings.json', 'r') as f:
    settings = json.load(f)
self.settings_page.load_all_settings(settings)
```

### Switch to Specific Section
```python
self.settings_page.switch_section('camera')
self.settings_page.switch_section('security')
```

### Update Camera Device List
```python
# Get camera settings section
camera_section = self.settings_page.sections['camera']
camera_widget = camera_section.widget().findChild(CameraSettings)

# Update devices
camera_widget.update_camera_devices(['Camera 0', 'Camera 1', 'RealSense D435'])
```

## 🎨 Custom Settings Section

### Create New Section
```python
from gui.pages.settings.base import BaseSettingsSection
from PySide6.QtWidgets import QCheckBox, QLineEdit

class MyCustomSettings(BaseSettingsSection):
    def __init__(self, parent=None):
        super().__init__("My Custom Settings", parent)
        self._init_controls()
    
    def _init_controls(self):
        # Add label
        self.add_field_label("Custom Option")
        
        # Add checkbox
        self.my_checkbox = QCheckBox("Enable custom feature")
        self.my_checkbox.stateChanged.connect(
            lambda state: self.emit_setting_changed("custom_feature", state)
        )
        self.main_layout.addWidget(self.my_checkbox)
    
    def get_settings(self) -> dict:
        return {
            'custom_feature': self.my_checkbox.isChecked()
        }
    
    def load_settings(self, settings: dict):
        if 'custom_feature' in settings:
            self.my_checkbox.setChecked(settings['custom_feature'])
```

### Register New Section
```python
# In settings_page.py, add to create_all_sections():
sections_config = [
    # ... existing sections ...
    ("custom", "Custom Settings", MyCustomSettings),
]

# Add to menu items in create_settings_menu():
menu_items = [
    # ... existing items ...
    ("⚙️", "Custom", "custom", False),
]
```

## 🐛 Troubleshooting

### Import Errors
```python
# Make sure gui package is in Python path
import sys
sys.path.insert(0, '/path/to/InspektLine')

# Then import
from gui.pages import SettingsPage
```

### Setting Not Saving
```python
# Ensure get_settings() returns correct dict
settings = camera_section.get_settings()
print(settings)  # Debug output

# Ensure load_settings() applies values
camera_section.load_settings({'camera_type': 'USB Webcam'})
```

### Widget Not Found
```python
# Use correct widget retrieval
section = self.settings_page.sections['camera']
scroll_area = section  # This is QScrollArea
content_widget = scroll_area.widget()  # Get the content
camera_widget = content_widget.findChild(CameraSettings)  # Find settings widget
```

## 📖 File Locations

```
gui/
├── pages/
│   ├── __init__.py                    # Exports: CameraPage, DatasetPage, SettingsPage
│   ├── settings_page.py              # Main settings coordinator
│   └── settings/
│       ├── __init__.py               # Exports all settings modules
│       ├── base.py                   # Base class
│       ├── camera.py                 # Camera settings
│       ├── detection.py              # Detection settings
│       ├── notifications.py          # Notification settings
│       ├── system.py                 # System settings
│       ├── network.py                # Network settings
│       ├── database.py               # Database settings
│       ├── security.py               # Security settings
│       └── user.py                   # User settings
└── styles/
    ├── __init__.py                   # Exports: DarkTheme, StyleSheets
    ├── themes.py                     # Color definitions
    └── stylesheets.py                # Widget styles
```

## 🔗 Related Documentation

- **Full Documentation**: `documentation/SETTINGS_RESTRUCTURING.md`
- **Architecture Diagrams**: `documentation/SETTINGS_ARCHITECTURE_DIAGRAM.md`
- **Summary**: `documentation/SETTINGS_RESTRUCTURING_SUMMARY.md`

## 💡 Tips

1. **Always use get_settings()** before closing the app
2. **Call load_settings()** after loading from file/database
3. **Use signals** for reactive UI updates
4. **Inherit from BaseSettingsSection** for consistency
5. **Keep modules focused** on single responsibility
6. **Document setting keys** in module docstrings
7. **Test settings persistence** early and often

## ⚡ Performance Notes

- Settings sections are created once at initialization
- QStackedWidget ensures only visible section is rendered
- Scroll areas provide efficient memory usage
- No performance impact from modular structure

## 🎯 Best Practices

✅ **DO:**
- Use emit_setting_changed() for all changes
- Implement both get_settings() and load_settings()
- Keep modules under 250 lines
- Add type hints to functions
- Write docstrings for classes and methods

❌ **DON'T:**
- Access widgets directly from outside
- Store state outside of widgets
- Mix different concerns in one module
- Skip input validation
- Forget to connect signals

