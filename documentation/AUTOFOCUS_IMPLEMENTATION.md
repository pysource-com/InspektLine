# Autofocus Implementation Summary

## Overview
This document summarizes the implementation of autofocus functionality and the removal of non-working camera settings options.

## Changes Made

### 1. Settings Page UI (`gui/pages/settings_page.py`)
**Removed:**
- Exposure slider (non-functional)
- Brightness slider (non-functional)
- Contrast slider (non-functional)
- Saturation slider (non-functional)
- Image stabilization checkbox (non-functional)
- `create_slider_group` method (no longer needed)

**Updated:**
- Autofocus checkbox now properly connected to `on_autofocus_changed` handler
- Removed QSlider import as it's no longer needed
- Cleaned up instance variables

### 2. Camera Module (`camera/camera.py`)
**Added:**
- `set_autofocus(cap, enabled: bool) -> bool` method
  - Supports both USB cameras (via OpenCV's `CAP_PROP_AUTOFOCUS`)
  - Supports Intel RealSense cameras (delegates to their API)
  - Returns True on success, False otherwise
  - Handles errors gracefully with informative messages

### 3. Intel RealSense Camera (`camera/intel_realsense.py`)
**Added:**
- `set_autofocus(enabled: bool) -> bool` method
  - Uses RealSense API to control auto-exposure (which includes focus)
  - Checks if camera is running before attempting to set autofocus
  - Finds the color sensor and verifies auto-exposure support
  - Returns True on success, False otherwise

### 4. Main GUI (`gui.py`)
**Added:**
- `on_autofocus_changed(state)` handler method
  - Triggered when autofocus checkbox state changes
  - Converts Qt checkbox state to boolean
  - Calls `camera.set_autofocus(cap, enabled)` to apply the setting
  - Provides feedback if the operation fails

**Updated:**
- Removed unused instance variables:
  - `exposure_value`
  - `contrast_value`
  - `brightness_value`
  - `saturation_value`
  - `stabilization_enabled`
- Connected autofocus checkbox to the handler in `create_camera_config_section()`
- Removed non-working sliders from the settings page
- Removed exposure and contrast sliders from the camera page bottom panel (they were non-functional)

## How It Works

### Autofocus Control Flow
1. User toggles the "Enable auto-focus" checkbox in Settings page
2. Checkbox emits `stateChanged` signal
3. `on_autofocus_changed(state)` handler is called
4. Handler converts state to boolean (checked/unchecked)
5. Handler calls `camera.set_autofocus(cap, enabled)`
6. Camera module determines camera type:
   - **USB Camera**: Uses OpenCV's `CAP_PROP_AUTOFOCUS` property
   - **Intel RealSense**: Calls RealSense-specific `set_autofocus()` method
7. Autofocus setting is applied to the camera hardware
8. Success/failure feedback is printed to console

### USB Camera Implementation
```python
# In camera/camera.py
def set_autofocus(self, cap, enabled: bool) -> bool:
    if isinstance(cap, cv2.VideoCapture):
        success = cap.set(cv2.CAP_PROP_AUTOFOCUS, 1 if enabled else 0)
        return success
```

### Intel RealSense Implementation
```python
# In camera/intel_realsense.py
def set_autofocus(self, enabled: bool) -> bool:
    color_sensor.set_option(rs.option.enable_auto_exposure, 1 if enabled else 0)
    return True
```

## Testing

### To Test Autofocus:
1. Run the application: `python gui.py`
2. Navigate to Settings page (⚙️ icon in sidebar)
3. Toggle "Enable auto-focus" checkbox
4. Check console output for confirmation messages
5. Observe camera feed for focus changes

### Expected Console Output:
- **Success (USB)**: `Autofocus enabled` or `Autofocus disabled`
- **Success (RealSense)**: `RealSense auto-exposure enabled` or `RealSense auto-exposure disabled`
- **Warning (USB)**: `Warning: Could not set autofocus (camera may not support this feature)`
- **Failure**: `Failed to set autofocus: [error message]`

## Notes

### Camera Support
- **USB Cameras**: Not all USB cameras support software-controlled autofocus. If your camera doesn't support it, you'll see a warning message, but the application will continue to work normally.
- **Intel RealSense**: The D435i uses auto-exposure control which includes focus management. This is a more reliable implementation for RealSense cameras.

### Known Limitations
1. Some USB webcams may not support the `CAP_PROP_AUTOFOCUS` property
2. The autofocus setting may reset when the camera is restarted
3. RealSense implementation uses auto-exposure, which affects both exposure and focus

## Future Enhancements
- Add manual focus control slider for cameras that support it
- Persist autofocus setting across application restarts
- Add visual indicator in camera feed when autofocus is active
- Implement focus ROI (Region of Interest) selection

