# Settings Module Restructuring

## Overview

The settings system has been completely restructured following best practices for modular architecture. Each settings category now has its own dedicated module for better maintainability and scalability.

## Directory Structure

```
gui/
├── pages/
│   ├── settings_page.py          # Main settings page coordinator
│   └── settings/                 # Settings modules directory
│       ├── __init__.py           # Module exports
│       ├── base.py               # Base class for all settings
│       ├── camera.py             # Camera settings
│       ├── detection.py          # Detection parameters
│       ├── notifications.py      # Notification settings
│       ├── system.py             # System configuration
│       ├── network.py            # Network settings
│       ├── database.py           # Database configuration
│       ├── security.py           # Security settings
│       └── user.py               # User profile settings
```

## Architecture

### Base Settings Section (`base.py`)

All settings sections inherit from `BaseSettingsSection`, which provides:

- **Consistent UI styling** for all sections
- **Signal-based communication** for settings changes
- **Standard interface** via `get_settings()` and `load_settings()` methods
- **Helper methods** for adding field labels and emitting changes

#### Key Features:

```python
class BaseSettingsSection(QWidget):
    settings_changed = Signal(str, object)  # Signal for any setting change
    
    def get_settings(self) -> dict:
        """Get all settings as a dictionary"""
        
    def load_settings(self, settings: dict):
        """Load settings from a dictionary"""
```

### Individual Setting Modules

Each settings module is self-contained and follows a consistent pattern:

1. **Imports** - Only what's needed for that specific section
2. **Class Definition** - Inherits from `BaseSettingsSection`
3. **UI Initialization** - Creates all controls for that section
4. **Event Handlers** - Handles user interactions
5. **Settings Interface** - Implements `get_settings()` and `load_settings()`

#### Example Structure:

```python
from .base import BaseSettingsSection

class CameraSettings(BaseSettingsSection):
    def __init__(self, parent=None):
        super().__init__("Camera Configuration", parent)
        self._init_camera_controls()
    
    def _init_camera_controls(self):
        # Create UI controls
        pass
    
    def get_settings(self) -> dict:
        # Return current settings
        pass
    
    def load_settings(self, settings: dict):
        # Load saved settings
        pass
```

## Settings Modules

### 1. Camera Settings (`camera.py`)

Manages camera hardware configuration:

- Camera type selection (USB Webcam, Intel RealSense)
- Device selection
- Resolution and frame rate
- Auto-focus toggle
- Manual focus control with slider

**Settings Keys:**
- `camera_type`: str
- `camera_device`: int
- `resolution`: str
- `fps`: str
- `autofocus`: bool
- `manual_focus`: int (0-255)

### 2. Detection Settings (`detection.py`)

Controls defect detection parameters:

- Confidence threshold percentage
- Minimum defect size in pixels

**Settings Keys:**
- `confidence_threshold`: str
- `min_defect_size`: str

### 3. Notifications Settings (`notifications.py`)

Configures alert and notification preferences:

- Enable/disable notifications
- Sound alerts
- Email notifications
- Email address
- Notification priority levels

**Settings Keys:**
- `notifications_enabled`: bool
- `sound_alerts`: bool
- `email_enabled`: bool
- `email_address`: str
- `notification_priority`: str

### 4. System Settings (`system.py`)

General system configuration:

- Language selection
- Theme (Dark/Light/Auto)
- Auto-start on system boot
- Auto-save inspection results
- Log level configuration

**Settings Keys:**
- `language`: str
- `theme`: str
- `auto_start`: bool
- `auto_save`: bool
- `log_level`: str

### 5. Network Settings (`network.py`)

Network and connectivity configuration:

- Remote access toggle
- API port
- Streaming port
- Connection protocol
- Proxy server settings

**Settings Keys:**
- `remote_access`: bool
- `api_port`: str
- `streaming_port`: str
- `protocol`: str
- `use_proxy`: bool

### 6. Database Settings (`database.py`)

Database configuration and backup:

- Database type (SQLite, PostgreSQL, MySQL, MongoDB)
- Database host/path
- Port configuration
- Auto-backup toggle
- Backup interval
- Connection test functionality

**Settings Keys:**
- `db_type`: str
- `db_host`: str
- `db_port`: str
- `auto_backup`: bool
- `backup_interval`: str

### 7. Security Settings (`security.py`)

Security and authentication:

- User authentication toggle
- Session timeout
- Password policy
- Two-factor authentication (2FA)
- Data encryption
- Audit logging

**Settings Keys:**
- `authentication_enabled`: bool
- `session_timeout`: str
- `password_policy`: str
- `two_factor_auth`: bool
- `data_encryption`: bool
- `audit_logging`: bool

### 8. User Settings (`user.py`)

User profile management:

- Username
- Full name
- Email
- Role assignment
- Password change functionality

**Settings Keys:**
- `username`: str
- `full_name`: str
- `user_email`: str
- `user_role`: str

## Main Settings Page (`settings_page.py`)

The `SettingsPage` class orchestrates all settings sections:

### Features:

1. **Left Navigation Menu** - Icon-based menu for section switching
2. **Section Management** - Loads and manages all settings sections
3. **Settings Persistence** - Provides `get_all_settings()` and `load_all_settings()`
4. **Legacy Compatibility** - Property accessors for backward compatibility

### Usage Example:

```python
from gui.pages import SettingsPage

# Create settings page
settings_page = SettingsPage(parent_window)

# Get all settings
all_settings = settings_page.get_all_settings()
# Returns: {
#     'camera': {...},
#     'detection': {...},
#     'notifications': {...},
#     ...
# }

# Load settings
settings_page.load_all_settings(saved_settings)

# Access specific controls (legacy compatibility)
camera_combo = settings_page.camera_type_combo
```

## Adding New Settings

To add a new settings section:

1. **Create new module** in `gui/pages/settings/`:

```python
# gui/pages/settings/mysection.py
from .base import BaseSettingsSection

class MySection(BaseSettingsSection):
    def __init__(self, parent=None):
        super().__init__("My Section Title", parent)
        self._init_controls()
    
    def _init_controls(self):
        # Add your controls
        pass
    
    def get_settings(self) -> dict:
        return {}
    
    def load_settings(self, settings: dict):
        pass
```

2. **Export in `__init__.py`**:

```python
from .mysection import MySection

__all__ = [..., 'MySection']
```

3. **Add to settings_page.py**:

```python
from gui.pages.settings import MySection

# In create_all_sections():
sections_config = [
    # ... existing sections ...
    ("mysection", "My Section", MySection),
]

# In create_settings_menu():
menu_items = [
    # ... existing items ...
    ("🎯", "My Section", "mysection", False),
]
```

## Benefits of New Structure

### 1. **Modularity**
- Each settings category is independent
- Easy to modify one section without affecting others
- Clear separation of concerns

### 2. **Maintainability**
- Smaller, focused files (100-200 lines each)
- Easy to locate and fix issues
- Self-documenting code structure

### 3. **Scalability**
- Simple to add new settings sections
- Easy to extend existing sections
- No impact on other sections

### 4. **Reusability**
- Base class provides common functionality
- Consistent patterns across all sections
- Settings sections can be reused in different contexts

### 5. **Testability**
- Each module can be tested independently
- Mock parent window for isolated testing
- Clear input/output contracts

### 6. **Code Organization**
- Follows Python package structure best practices
- Proper use of `__init__.py` for clean imports
- Consistent naming conventions

## Migration Notes

### Backward Compatibility

The new structure maintains backward compatibility through property accessors:

```python
# Old way (still works)
settings_page.camera_type_combo

# New way (recommended)
camera_section = settings_page.sections['camera']
camera_widget = camera_section.widget().findChild(CameraSettings)
camera_widget.camera_type_combo
```

### Breaking Changes

None - the public API remains the same.

## Best Practices

1. **Always inherit from `BaseSettingsSection`** for new settings modules
2. **Use `emit_setting_changed()`** to notify of changes
3. **Implement both `get_settings()` and `load_settings()`** for persistence
4. **Use consistent styling** via `StyleSheets` and `DarkTheme`
5. **Add field labels** using `add_field_label()` helper
6. **Keep modules focused** - one responsibility per module
7. **Document settings keys** in module docstrings

## Testing

To test a settings section:

```python
from gui.pages.settings import CameraSettings

# Create section
section = CameraSettings(parent=None)

# Get default settings
settings = section.get_settings()
print(settings)

# Modify and retrieve
section.camera_type_combo.setCurrentIndex(1)
updated_settings = section.get_settings()

# Load settings
section.load_settings({'camera_type': 'Intel RealSense'})
```

## Future Enhancements

Potential improvements:

1. **Settings validation** - Add validators in base class
2. **Settings templates** - Predefined configuration sets
3. **Import/Export** - Save/load settings to JSON files
4. **Settings search** - Search across all settings
5. **Recent changes** - Track and display recent modifications
6. **Settings groups** - Logical grouping within sections
7. **Tooltips** - Context-sensitive help for each setting

## Conclusion

This restructuring provides a solid foundation for the settings system that is:
- Easy to understand and navigate
- Simple to maintain and extend
- Consistent across all sections
- Following Python and Qt best practices

The modular approach makes it easy for developers to work on specific areas without understanding the entire settings system.

