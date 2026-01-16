# Dataset Collection - Quick Reference

## 🚀 Quick Start

1. **Run the application:**
   ```bash
   python gui.py
   ```

2. **Navigate to Dataset page** (2nd icon in sidebar)

3. **Start capturing:**
   - **OK button** or `→` / `Enter` = Good sample
   - **NOT OK button** or `←` / `Backspace` = Defective sample

## 📁 Where are images saved?

```
storage/dataset/
├── ok/                 # Good samples
│   └── ok_20260116_143022_456.jpg
└── not_ok/            # Defective samples
    └── notok_surface_defect_20260116_143030_123.jpg
```

## 🎨 Features

✅ **Automatic saving** - Images saved instantly when you press OK/NOT OK  
✅ **Gallery view** - See thumbnails in right sidebar (green=OK, red=NOT OK)  
✅ **Statistics** - Real-time counters for total, OK, and NOT OK samples  
✅ **Categories** - Select defect type before capturing NOT OK samples  
✅ **Persistent** - Existing images loaded automatically on startup  
✅ **Keyboard shortcuts** - Fast labeling with arrow keys  

## 🎯 Workflow

1. Position object in camera view
2. (Optional) Select defect category if object is defective
3. Press OK or NOT OK button
4. Image is saved and appears in gallery
5. Repeat!

## 📊 Statistics Panel

- **Total Samples**: All captured images
- **OK Samples**: Good quality images (green)
- **NOT OK Samples**: Defective images (red)
- Gallery badges show quick counts

## 🔧 Defect Categories

Choose before capturing NOT OK samples:
- Surface Defect
- Crack
- Scratch
- Dent
- Discoloration
- Missing Part
- Contamination

Category name is included in the filename.

## ⌨️ Keyboard Shortcuts

| Action | Keys |
|--------|------|
| Capture OK | `→` or `Enter` |
| Capture NOT OK | `←` or `Backspace` |

Buttons only work when camera feed is active!

## 🐛 Troubleshooting

**Buttons are disabled?**
- Make sure camera is connected and active
- Verify you're on the Dataset page

**Images not saving?**
- Check console for error messages
- Verify write permissions in project folder

**Gallery not showing images?**
- Images should load automatically
- Check `storage/dataset/ok/` and `storage/dataset/not_ok/` folders

## 📝 Notes

- Images are saved as JPEG format
- Filename includes timestamp for uniqueness
- Gallery shows last 50 images
- All images persist between sessions

