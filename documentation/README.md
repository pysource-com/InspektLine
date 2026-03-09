# InspektLine

A minimal real-time visual defect inspection system using computer vision and deep learning.

## Features

- Real-time defect detection using transformer-based image classification
- Support for USB cameras and Intel RealSense D435i
- Simple model loading — bring your own trained model
- Configurable confidence threshold and detection frequency

## Prerequisites

- Python 3.10+
- NVIDIA GPU with CUDA 12.6 support (recommended)
- USB camera or Intel RealSense D435i
- Windows OS

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/InspektLine.git
cd InspektLine
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

## Usage

1. **Load Model** — click "Load Model" on the home page and select a model directory.
2. **Start Inspection** — click "Start Inspection" to begin real-time defect detection.
3. **Camera Feed** — open the camera feed window to view the live stream.
4. **Settings** — configure camera device, confidence threshold, and detection frequency.

## Troubleshooting

### CUDA Not Available

- Ensure the latest NVIDIA drivers are installed
- Verify CUDA 12.6 is installed
- Check GPU compatibility with PyTorch

### Camera Not Detected

- Verify camera drivers are installed
- Check camera index in Settings
- For RealSense cameras, ensure the Intel RealSense SDK is installed

## License

See [LICENSE](../LICENSE) file for details.
