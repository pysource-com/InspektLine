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
│   ├── classifier.py        # Transformer-based image classifier
│   ├── rfdetr_detector.py   # RF-DETR object detection & segmentation
│   └── annotate.py          # OpenCV drawing utilities (boxes, masks)
│
├── services/
│   ├── settings_service.py  # JSON-persisted application settings
│   ├── camera_service.py    # Camera lifecycle (open, read, close)
│   ├── inspection_service.py# Orchestrates camera + model inference (threaded)
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
│   │       └── detection.py # Detection parameters section (incl. RF-DETR)
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
CameraService.read_frame()        (background thread)
      │
      ▼
MainWindow (FrameBridge signal)    (main thread)
      │
      ├──► InspectionService.submit_frame()  →  inference thread
      │         │
      │         ▼
      │    RFDETRDetector / TransformerImageClassifier
      │         │
      │         ▼
      │    latest_detections  ◄── thread-safe read
      │         │
      │         ▼
      │    draw_detections() (OpenCV overlay)
      │         │
      ├──► CameraPage.video_label  →  display (annotated frame)
      │
      └──► DatasetService.process_frame()
```

## Detector Backends

Two detector backends are supported, selected via the **Model Type** dropdown on the Home page:

### Classifier (HuggingFace Transformers)
- Whole-image classification (e.g. "good" vs "defective")
- Load a HuggingFace model directory via folder picker
- Uses `TransformerImageClassifier` in `detector/classifier.py`

### RF-DETR (Roboflow)
- Object detection with bounding boxes + optional instance segmentation masks
- Load a fine-tuned `.pth` checkpoint via file picker
- Place a `classes.txt` (one class name per line) or `classes.json` (list of strings) next to the `.pth` file for automatic class label mapping
- Uses `RFDETRDetector` in `detector/rfdetr_detector.py`
- Model size (Base / Large), number of classes, and input resolution are configurable in Settings → Detection Parameters
- Annotations are rendered with OpenCV (`detector/annotate.py`) — coloured bounding boxes, labels, confidence scores, and optional semi-transparent segmentation masks

## Threaded Inference

Inference runs on a **dedicated background thread** managed by `InspectionService`:

1. The main-thread frame loop calls `submit_frame(frame)` — stores the latest frame under a lock
2. The inference thread wakes at the configured `detection_frequency`, grabs the latest frame, runs the detector, and stores results under a second lock
3. The main thread reads `latest_detections` (lock-free read of the latest list) and draws overlays before display
4. Only the most recent frame is kept — older un-processed frames are dropped so inference never queues up

## Service Layer

All business logic lives in `services/` — no Qt dependency.

- **SettingsService** — loads/saves `settings.json`, exposes typed dataclasses
- **CameraService** — owns `cv2.VideoCapture` lifecycle
- **InspectionService** — loads detector model, runs threaded inference on frames
- **DatasetService** — collects frames as video (`.mp4`) or images (`.png`) into timestamped session folders

## GUI Layer

The GUI is a thin orchestrator:

- **MainWindow** — creates services, starts frame timer, draws detection overlays, opens page dialogs
- **HomePage** — load model (classifier or RF-DETR), start/stop inspection, dataset collection
- **CameraPage** — live video feed with controls
- **SettingsPage** — camera device, confidence threshold, detection frequency, RF-DETR parameters
