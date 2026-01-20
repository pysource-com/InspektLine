# Manual Focus Slider - Bug Fix

## Issue
The manual focus slider was not appearing in the Settings page Camera Configuration section.

## Root Cause
The application was using the `create_camera_config_section()` method in `gui.py` instead of the modular `SettingsPage` class from `gui/pages/settings_page.py`. The `gui.py` version was missing the manual focus slider implementation.

## Solution
Added the manual focus slider to the `create_camera_config_section()` method in `gui.py`:

### Changes Made:

1. **Added Manual Focus Slider UI** (in `gui.py`):
   - Manual Focus label
   - Horizontal slider (0-255 range, default: 128)
   - Value display label showing current focus value
   - Info text explaining when it's available

2. **Added `_on_autofocus_toggled()` Method**:
   - Dynamically enables/disables the manual focus slider based on autofocus state
   - Slider is enabled when autofocus is OFF
   - Slider is disabled when autofocus is ON

3. **Connected Event Handlers**:
   - Autofocus checkbox connected to both `on_autofocus_changed()` and `_on_autofocus_toggled()`
   - Manual focus slider connected to `on_manual_focus_changed()`
   - Slider value changes update the value label in real-time

## Implementation Details

### Manual Focus Slider Code
```python
# Manual Focus slider
manual_focus_label = QLabel("Manual Focus")
manual_focus_label.setStyleSheet("color: #999; font-size: 13px; margin-top: 15px; margin-bottom: 8px;")
section_layout.addWidget(manual_focus_label)

focus_control_layout = QHBoxLayout()
focus_control_layout.setSpacing(15)

self.manual_focus_slider = QSlider(Qt.Orientation.Horizontal)
self.manual_focus_slider.setMinimum(0)
self.manual_focus_slider.setMaximum(255)
self.manual_focus_slider.setValue(128)
self.manual_focus_slider.setStyleSheet(self.get_slider_style())
self.manual_focus_slider.setEnabled(not self.auto_focus_enabled)
self.manual_focus_slider.valueChanged.connect(self.on_manual_focus_changed)
focus_control_layout.addWidget(self.manual_focus_slider, stretch=1)

self.focus_value_label = QLabel("128")
self.focus_value_label.setStyleSheet("color: #999; font-size: 13px; min-width: 35px;")
self.manual_focus_slider.valueChanged.connect(lambda v: self.focus_value_label.setText(str(v)))
focus_control_layout.addWidget(self.focus_value_label)

section_layout.addLayout(focus_control_layout)
```

### Dynamic Enable/Disable Handler
```python
def _on_autofocus_toggled(self, state):
    """Handle autofocus checkbox toggle to enable/disable manual focus slider."""
    is_autofocus_enabled = state == Qt.CheckState.Checked.value
    if hasattr(self, 'manual_focus_slider'):
        self.manual_focus_slider.setEnabled(not is_autofocus_enabled)
```

## Current State

### Settings Page Layout (Camera Configuration Section):
```
┌─────────────────────────────────────────────┐
│ Camera Configuration                        │
│                                             │
│ Camera Type:  [USB Webcam ▼]                │
│ Camera Device: [Camera 0 ▼]                 │
│ Resolution: [1920x1080 ▼] FPS: [30 FPS ▼]  │
│                                             │
│ ☐ Enable auto-focus    (unchecked default) │
│                                             │
│ Manual Focus                                │
│ [━━━━━━━●━━━━━━━] 128  (blue, active)      │
│ Note: Manual focus is only available when   │
│ auto-focus is disabled                      │
└─────────────────────────────────────────────┘
```

## Testing
Run the application:
```bash
python gui.py
```

Then:
1. Click Settings (⚙️) in sidebar
2. Look at Camera Configuration section
3. Manual Focus slider should be visible and enabled by default
4. Drag the slider to adjust focus (0-255)
5. Value label updates in real-time
6. Check "Enable auto-focus" to disable the slider
7. Uncheck to re-enable the slider

## Files Modified
- `gui.py` - Added manual focus slider to `create_camera_config_section()` and `_on_autofocus_toggled()` method

## Status
✅ **FIXED** - Manual focus slider now appears in Settings page Camera Configuration section
✅ Slider is enabled by default (autofocus is off by default)
✅ Slider dynamically enables/disables based on autofocus state
✅ Value label shows current focus value
✅ All event handlers properly connected

