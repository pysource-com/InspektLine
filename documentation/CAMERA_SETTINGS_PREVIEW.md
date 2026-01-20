# Camera Settings Live Preview

## Overview
The camera settings page now includes a **live preview** of the camera feed, positioned on the right side of the settings panel. This allows users to see the effects of their configuration changes in real-time.

## Layout Design

The settings page uses a modern **split-panel layout** following best practices:

```
┌─────────────────────────────────────────────────────────┐
│  Camera Configuration                                    │
├──────────────────────────┬──────────────────────────────┤
│                          │                              │
│  Camera Settings         │   Live Preview               │
│  ┌──────────────────┐    │   ┌────────────────────┐    │
│  │ Camera Type     ▼│    │   │                    │    │
│  └──────────────────┘    │   │   [Camera Feed]    │    │
│                          │   │                    │    │
│  ┌──────────────────┐    │   │                    │    │
│  │ Camera Device   ▼│    │   └────────────────────┘    │
│  └──────────────────┘    │   ● LIVE  FPS: 30  Res: HD  │
│                          │                              │
│  Resolution  │ FPS       │   Settings changes are       │
│  ┌─────┐    │ ┌─────┐   │   applied in real-time       │
│  │ HD ▼│    │ │30▼  │   │                              │
│  └─────┘    │ └─────┘   │                              │
│                          │                              │
│  ☑ Enable auto-focus     │                              │
│                          │                              │
│  Manual Focus            │                              │
│  ├─────●──────────┤ 128  │                              │
│                          │                              │
└──────────────────────────┴──────────────────────────────┘
```

## Features

### 1. **Split Panel Layout**
- **Left Panel (40-60% width)**: Contains all camera settings controls
- **Right Panel (40-60% width)**: Displays live camera preview
- Responsive design with min/max width constraints for optimal viewing

### 2. **Live Preview**
- Real-time camera feed display
- Updates at ~30 FPS
- Automatically starts when the settings page is shown
- Stops when switching to another page (resource-efficient)

### 3. **Preview Info Overlay**
- **LIVE indicator**: Green dot showing active feed
- **FPS counter**: Current frame rate
- **Resolution**: Current camera resolution (e.g., 1920×1080)

### 4. **Automatic Frame Management**
- Preview timer automatically starts on `showEvent()`
- Preview timer automatically stops on `hideEvent()`
- Prevents unnecessary CPU usage when settings page is not visible

## Implementation Details

### Key Components

1. **Split Layout Initialization** (`_init_split_layout`)
   - Creates horizontal layout with two containers
   - Settings container (left, flexible width)
   - Preview container (right, 400-600px)

2. **Preview Panel** (`_init_preview_panel`)
   - Video display label with proper aspect ratio scaling
   - Info overlay with live status indicators
   - Styled frame with rounded corners and borders

3. **Frame Update** (`_update_preview_frame`)
   - Gets current frame from parent window's camera
   - Converts BGR to RGB color space
   - Scales to fit preview area while maintaining aspect ratio
   - Updates FPS and resolution info

### Timer Management

```python
def start_preview(self):
    """Start the camera preview at ~30 FPS"""
    if self.preview_timer is None:
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self._update_preview_frame)
    
    if not self.preview_timer.isActive():
        self.preview_timer.start(33)  # 33ms = ~30 FPS

def stop_preview(self):
    """Stop the preview to save resources"""
    if self.preview_timer is not None and self.preview_timer.isActive():
        self.preview_timer.stop()
```

## Usage

### In the Application

When users navigate to Settings → Camera, they will see:
1. All camera controls on the left side
2. Live camera preview on the right side
3. Real-time feedback as they adjust settings

### Testing

Run the standalone test:
```bash
python test_camera_settings_preview.py
```

This test creates a minimal window with just the camera settings section, perfect for development and testing.

## Benefits

1. **Immediate Feedback**: Users can see the effect of settings changes instantly
2. **Better UX**: No need to switch between settings and camera pages
3. **Efficient**: Preview only runs when settings page is visible
4. **Professional Look**: Modern split-panel design common in professional applications

## Best Practices Applied

1. **Separation of Concerns**: Settings controls and preview are in separate containers
2. **Resource Management**: Preview timer starts/stops automatically
3. **Responsive Design**: Layout adapts to different window sizes
4. **Error Handling**: Graceful fallback if camera is unavailable
5. **Performance**: Preview updates at optimal ~30 FPS
6. **Visual Hierarchy**: Clear distinction between controls and preview

## Future Enhancements

Potential improvements:
- Add zoom controls to preview panel
- Snapshot button to capture current preview frame
- Picture-in-picture mode for settings adjustments
- Side-by-side comparison (before/after settings change)
- Recording preview with settings overlay

