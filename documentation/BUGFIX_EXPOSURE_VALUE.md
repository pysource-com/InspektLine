# Bug Fix: AttributeError for exposure_value

## Issue
After removing non-working camera controls, the application crashed on startup with:
```
AttributeError: 'VideoDisplayWidget' object has no attribute 'exposure_value'
```

## Root Cause
When we removed the unused instance variables (`exposure_value`, `contrast_value`, etc.) from the `__init__` method, we forgot to remove the references to these variables in the `create_bottom_panel()` method.

The bottom panel of the camera page had exposure and contrast sliders that were:
1. Not actually controlling the camera (non-functional)
2. Still referencing the removed instance variables

## Solution
Removed the entire sliders section from `create_bottom_panel()` method in `gui.py`:
- Removed exposure slider and all its layout code
- Removed contrast slider and all its layout code
- Kept only the functional buttons (Start Inspection, Capture, Pause, Record)

## Files Modified
- `gui.py` - Removed non-working sliders from bottom panel
- `AUTOFOCUS_IMPLEMENTATION.md` - Updated documentation

## Testing
The application now starts successfully without errors. The camera page bottom panel shows only the control buttons without the non-functional sliders.

## Verification
```bash
python gui.py
```
Application should start normally and display the camera feed with working controls.

