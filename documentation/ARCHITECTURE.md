# InspektLine Architecture

## Overview

InspektLine is a minimal real-time visual defect inspection system.
It captures frames from a camera, runs inference through a loaded model,
and displays results live.

## Structure

```
InspektLine/
├── main.py                  # Entry point — bootstraps services + GUI
├── config.py                # Application constants
├── requirements.txt
│
├── camera/
│   ├── camera.py            # Camera abstraction (USB / RealSense)
│   └── intel_realsense.py   # Intel RealSense adapter
│
├── detector/
│   └── classifier.py        # Transformer-based image classifier
│
├── services/
│   ├── settings_service.py  # JSON-persisted application settings
│   ├── camera_service.py    # Camera lifecycle (open, read, close)
│   ├── inspection_service.py# Orchestrates camera + model inference
│   └── dataset_service.py   # Dataset collection (video / image capture)
│
├── gui/
│   ├── main_window.py       # Main window — wires services to pages
│   ├── components/
│   │   ├── sidebar_button.py
│   │   └── video_label.py   # Displays camera frames (QLabel)
│   ├── pages/
│   │   ├── home_page.py     # Load model + start/stop inspection
│   │   ├── camera_page.py   # Live camera feed viewer
│   │   ├── settings_page.py # Camera device, confidence, frequency
│   │   └── settings/
│   │       ├── base.py      # Base settings section widget
│   │       ├── camera.py    # Camera settings section
│   │       └── detection.py # Detection parameters section
│   └── styles/
│       ├── themes.py        # DarkTheme colour palette
│       └── stylesheets.py   # Reusable Qt stylesheets
│
└── storage/
    └── settings.json        # Persisted user settings
```

## Data Flow

```
Camera Hardware
      │ frames
      ▼
CameraService.read_frame()
      │
      ▼
MainWindow (QTimer @ 30ms)
      │
      ├──► CameraPage.video_label  →  display
      │
      └──► InspectionService.inspect_frame()  →  results
```

## Service Layer

All business logic lives in `services/` — no Qt dependency.

- **SettingsService** — loads/saves `settings.json`, exposes typed dataclasses
- **CameraService** — owns `cv2.VideoCapture` lifecycle
- **InspectionService** — loads a transformer model, runs inference on frames
- **DatasetService** — collects frames as video (`.mp4`) or images (`.png`) into timestamped session folders

## GUI Layer

The GUI is a thin orchestrator:

- **MainWindow** — creates services, starts frame timer, opens page dialogs
- **HomePage** — load model, start/stop inspection
- **CameraPage** — live video feed with controls
- **SettingsPage** — camera device, confidence threshold, detection frequency
