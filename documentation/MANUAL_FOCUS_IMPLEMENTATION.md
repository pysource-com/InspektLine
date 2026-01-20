# Manual Focus Implementation

## Overview
Added manual focus control functionality that allows users to adjust camera focus manually using a slider when autofocus is disabled.

## Features Added

### 1. Settings Page UI (`gui/pages/settings_page.py`)
**Added:**
- Manual Focus slider (0-255 range)
- Focus value label showing current focus value
- Dynamic enable/disable based on autofocus state
- Info text explaining when manual focus is available
- `_on_autofocus_toggled()` method to handle slider state

**Behavior:**
- Slider is **disabled** when autofocus is enabled
- Slider is **enabled** when autofocus is disabled
- Shows current focus value next to the slider
- Real-time updates as you drag the slider

### 2. Camera Module (`camera/camera.py`)
**Added:**
- `set_manual_focus(cap, focus_value: int) -> bool` method
  - Supports both USB cameras (via OpenCV's `CAP_PROP_FOCUS`)
  - Supports Intel RealSense cameras (delegates to their API)
  - Automatically disables autofocus before setting manual focus
  - Returns True on success, False otherwise
  - Handles errors gracefully with informative messages

### 3. Intel RealSense Camera (`camera/intel_realsense.py`)
**Added:**
- `set_manual_focus(focus_value: int) -> bool` method
  - Note: D435i uses fixed focus, so manual adjustment may not have effect
  - Disables auto-exposure first
  - Provides informative console output

### 4. Main GUI (`gui.py`)
**Added:**
- `on_manual_focus_changed(value)` handler method
  - Triggered when manual focus slider value changes
  - Calls `camera.set_manual_focus(cap, value)` to apply the setting
  - Provides feedback if the operation fails

## How It Works

### User Interaction Flow
1. User navigates to Settings page (⚙️ icon)
2. User **unchecks** "Enable auto-focus" checkbox
3. Manual Focus slider becomes **enabled**
4. User drags the slider to adjust focus (0-255)
5. Focus changes in real-time as slider moves
6. Current focus value is displayed next to slider

### Technical Flow
1. Slider value changes
2. `on_manual_focus_changed(value)` handler is called
3. Handler calls `camera.set_manual_focus(cap, value)`
4. Camera module determines camera type:
   - **USB Camera**: 
     - Disables autofocus with `CAP_PROP_AUTOFOCUS = 0`
     - Sets focus value with `CAP_PROP_FOCUS`
   - **Intel RealSense**: 
     - Calls RealSense-specific `set_manual_focus()` method
     - Note: D435i has fixed focus
5. Focus setting is applied to camera hardware
6. Success/failure feedback is printed to console

### Code Implementation

#### USB Camera (OpenCV)
```python
# In camera/camera.py
def set_manual_focus(self, cap, focus_value: int) -> bool:
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus
    success = cap.set(cv2.CAP_PROP_FOCUS, focus_value)
    return success
```

#### Intel RealSense
```python
# In camera/intel_realsense.py
def set_manual_focus(self, focus_value: int) -> bool:
    color_sensor.set_option(rs.option.enable_auto_exposure, 0)
    # Note: D435i uses fixed focus
    return True
```

#### UI Logic
```python
# In settings_page.py
def _on_autofocus_toggled(self, state):
    is_autofocus_enabled = state == Qt.CheckState.Checked.value
    self.manual_focus_slider.setEnabled(not is_autofocus_enabled)
```

## Focus Value Range
- **Minimum**: 0 (near focus)
- **Maximum**: 255 (far focus)
- **Default**: 128 (middle range)

The focus value represents the focus distance, where:
- Lower values (0-50): Focus on near objects
- Middle values (100-150): General purpose focus
- Higher values (200-255): Focus on far objects

## Camera Support

### USB Cameras
- **Support**: Varies by camera model
- **Property**: OpenCV `CAP_PROP_FOCUS`
- **Behavior**: If supported, focus will adjust in real-time
- **If Unsupported**: Warning message appears, but app continues normally

### Intel RealSense D435i
- **Support**: Limited (fixed focus camera)
- **Behavior**: Setting is applied but may not have visible effect
- **Note**: D435i has a fixed focus optimized for its depth sensing range

## Testing

### To Test Manual Focus:
1. Run the application: `python gui.py`
2. Navigate to Settings page (⚙️ icon in sidebar)
3. **Uncheck** "Enable auto-focus" checkbox
4. Manual Focus slider becomes active
5. Drag the slider left/right to adjust focus
6. Check console output for confirmation messages
7. Observe camera feed for focus changes

### Expected Console Output:
- **Success (USB)**: `Manual focus set to: [value]`
- **Success (RealSense)**: `RealSense manual focus set to: [value]`
- **Warning (USB)**: `Warning: Could not set manual focus (camera may not support this feature)`
- **Info (RealSense)**: `Note: D435i camera uses fixed focus and may not support manual adjustment`

## UI/UX Design

### Visual States
1. **Manual Focus Enabled** (default):
   - Checkbox: ☐ Unchecked
   - Manual Focus Slider: Active (blue slider)
   - Value label: Updates in real-time
   - Info text: Visible

2. **Autofocus Enabled**:
   - Checkbox: ✓ Checked
   - Manual Focus Slider: Grayed out (disabled)
   - Info text: Visible

### Slider Styling
- Uses the application's dark theme
- Blue accent color when active
- Smooth dragging experience
- Instant value updates

## Known Limitations

1. **USB Cameras**: Not all USB webcams support manual focus control via software
2. **Intel RealSense D435i**: Has fixed focus, manual adjustment may not work
3. **Focus Range**: The effective range depends on camera specifications
4. **Real-time Preview**: Focus changes should be visible immediately, but may have slight delay depending on camera

## Integration with Existing Features

### Autofocus Interaction
- Manual focus is **mutually exclusive** with autofocus
- When autofocus is enabled, manual focus is disabled
- When manual focus is used, autofocus is automatically disabled
- State is managed automatically by the UI

### Settings Persistence
- Current implementation: Focus value resets to 128 on app restart
- Future enhancement: Could persist focus settings to config file

## Future Enhancements

1. **Per-Camera Presets**: Save focus presets for different cameras
2. **Auto-Calculate Focus**: Calculate optimal focus based on detected objects
3. **Focus Assist**: Visual indicator showing when subject is in focus
4. **Focus Bracketing**: Capture multiple images at different focus distances
5. **Focus Range Detection**: Auto-detect min/max focus range for each camera
6. **Keyboard Shortcuts**: Quick focus adjustments with +/- keys

## Troubleshooting

### Manual Focus Not Working
1. **Check Console**: Look for error messages
2. **Camera Support**: Verify your camera supports manual focus
3. **Autofocus State**: Ensure autofocus is disabled
4. **Camera Driver**: Some cameras need specific drivers for focus control

### Slider Always Disabled
1. **Check Autofocus**: Make sure "Enable auto-focus" is unchecked
2. **Restart App**: Try restarting the application
3. **Check Console**: Look for initialization errors

### No Visible Focus Change
1. **Camera Type**: Some cameras (like D435i) have fixed focus
2. **Focus Range**: Try the full range (0-255) to see any effect
3. **Camera Distance**: Focus effect is more visible with objects at varying distances

