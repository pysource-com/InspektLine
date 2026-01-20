# Camera Settings Preview - Quick Reference

## What's New? 📹

The camera settings page now shows a **live preview** of your camera feed right next to the settings controls!

## Visual Layout

```
Settings Page Layout:
┌──────────────┬──────────────┐
│   Settings   │     Live     │
│   Controls   │   Preview    │
│   (Left)     │   (Right)    │
└──────────────┴──────────────┘
```

## Key Features

### 1. **Split-Panel Design**
- Settings on the left (adjustable controls)
- Live camera preview on the right
- Professional, modern layout

### 2. **Real-Time Preview**
- See settings changes instantly
- ~30 FPS smooth playback
- Auto aspect ratio scaling

### 3. **Smart Resource Management**
- Preview starts when you open settings
- Preview stops when you leave settings
- Efficient CPU usage

### 4. **Info Overlay**
Shows on the preview:
- 🟢 LIVE indicator
- FPS: Current frame rate
- Res: Current resolution

## How to Use

1. **Open the application**
2. **Navigate to Settings → Camera**
3. **See the live preview** on the right
4. **Adjust any setting** and watch it update in real-time!

## Settings You Can Adjust (with live feedback)

- 📹 Camera Type (USB/Intel RealSense)
- 🔌 Camera Device (select which camera)
- 🖼️ Resolution (Full HD, HD, VGA)
- ⚡ Frame Rate (60/30/15 FPS)
- 🎯 Autofocus (on/off)
- 🔍 Manual Focus (0-255 slider)

## Testing

**Run standalone test:**
```bash
python test_camera_settings_preview.py
```

**In main application:**
- Just navigate to Settings → Camera
- The preview appears automatically!

## Technical Details

| Feature | Value |
|---------|-------|
| Preview FPS | ~30 |
| Layout Type | Split Panel (Horizontal) |
| Preview Size | 400-600px width, responsive |
| Timer Interval | 33ms |
| Auto-start | ✅ Yes |
| Auto-stop | ✅ Yes |

## Files Modified

- `gui/pages/settings/camera.py` - Main implementation

## Files Created

- `test_camera_settings_preview.py` - Test application
- `documentation/CAMERA_SETTINGS_PREVIEW.md` - Full docs
- `documentation/CAMERA_SETTINGS_PREVIEW_SUMMARY.md` - Summary
- `documentation/CAMERA_SETTINGS_PREVIEW_QUICKREF.md` - This file

## Benefits

✅ Immediate visual feedback  
✅ No need to switch pages  
✅ Professional appearance  
✅ Resource efficient  
✅ Better user experience  

## Need Help?

See the full documentation:
- `documentation/CAMERA_SETTINGS_PREVIEW.md` - Complete guide
- `documentation/CAMERA_SETTINGS_PREVIEW_SUMMARY.md` - Implementation summary

---

**Status:** ✅ Ready to use!

