# Dataset Collection Feature

## Overview
The dataset collection feature allows you to capture and label images from the camera feed for training machine learning models.

## Features Implemented

### 1. Image Capture and Storage
- **OK Button**: Captures and saves images labeled as "OK" (good samples)
- **NOT OK Button**: Captures and saves images labeled as "NOT OK" (defective samples)
- Images are saved to `storage/dataset/` directory:
  - OK samples: `storage/dataset/ok/`
  - NOT OK samples: `storage/dataset/not_ok/`

### 2. Filename Convention
- **OK samples**: `ok_YYYYMMDD_HHMMSS_mmm.jpg`
- **NOT OK samples**: `notok_[category]_YYYYMMDD_HHMMSS_mmm.jpg`
  - Category is automatically appended based on the selected defect category
  - Example: `notok_surface_defect_20260116_143022_456.jpg`

### 3. Gallery Display
- Right sidebar shows thumbnails of recently captured images
- Color-coded borders:
  - **Green border**: OK samples
  - **Red border**: NOT OK samples
- Displays last 50 captured images
- Auto-loads existing images on startup

### 4. Statistics Tracking
- **Total Samples**: Count of all captured images
- **OK Samples**: Count of OK images
- **NOT OK Samples**: Count of defective images
- **Session Duration**: Time spent collecting data
- **Capture Rate**: Samples per minute

### 5. Defect Categories
Select from predefined categories for NOT OK samples:
- Surface Defect
- Crack
- Scratch
- Dent
- Discoloration
- Missing Part
- Contamination

### 6. Keyboard Shortcuts
- **→ or Enter**: Capture OK sample
- **← or Backspace**: Capture NOT OK sample

## Usage Instructions

1. **Start the Application**
   ```bash
   python gui.py
   ```

2. **Navigate to Dataset Page**
   - Click the second icon in the left sidebar (folder icon)

3. **Select Defect Category** (for NOT OK samples)
   - Choose appropriate category from dropdown in left panel

4. **Capture Images**
   - Position object in camera view
   - Press **OK button** (or → key) for good samples
   - Press **NOT OK button** (or ← key) for defective samples

5. **Monitor Progress**
   - Statistics panel shows real-time counts
   - Gallery shows captured thumbnails
   - Badges show OK/NG counts

6. **Export Dataset**
   - Click "Export Dataset" button (feature coming soon)

## Technical Details

### Storage Structure
```
storage/
└── dataset/
    ├── ok/
    │   ├── ok_20260116_143022_456.jpg
    │   ├── ok_20260116_143025_789.jpg
    │   └── ...
    └── not_ok/
        ├── notok_surface_defect_20260116_143030_123.jpg
        ├── notok_crack_20260116_143035_456.jpg
        └── ...
```

### Frame Capture
- Current camera frame is stored in memory
- Frame is captured when button is pressed
- Uses OpenCV's `cv2.imwrite()` for saving
- Format: JPEG with default quality

### Load Existing Samples
- On page load, scans storage directories
- Loads up to 50 most recent images per category
- Updates statistics and gallery automatically

## Implementation Files

- **gui/pages/dataset_page.py**: Main dataset page UI and logic
- **gui.py**: Main application with frame capture
- **storage/dataset/**: Image storage directory (auto-created)

## Future Enhancements

1. Export dataset in various formats (YOLO, COCO, Pascal VOC)
2. Dataset augmentation integration
3. Annotation tools for bounding boxes
4. Dataset statistics and distribution charts
5. Batch operations (delete, move, relabel)
6. Dataset validation and quality checks

## Troubleshooting

### Buttons are Disabled
- Ensure camera is active and feeding frames
- Check that you're on the Dataset page
- Verify camera permissions

### Images Not Saving
- Check write permissions in project directory
- Verify storage path exists
- Check console for error messages

### Gallery Not Updating
- Refresh the page by switching pages and back
- Check if images exist in storage folders
- Verify file permissions

## Testing

Run the test script:
```bash
python test_dataset.py
```

This will:
1. Check storage directory structure
2. Count existing samples
3. Launch the GUI for manual testing

