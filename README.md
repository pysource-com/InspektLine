# InspektLine
A software to identify defects on a production line using computer vision and deep learning.

## Features
- Real-time defect detection using transformer-based image classification
- Support for Intel RealSense D435i cameras
- Dataset capture and augmentation tools
- Model training capabilities with PyTorch

## Prerequisites
- Python 3.8 or higher
- NVIDIA GPU with CUDA 12.6 support (recommended for training and inference)
- Intel RealSense D435i camera (optional, for live detection)
- Windows OS (currently optimized for Windows)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/InspektLine.git
cd InspektLine
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- **PyTorch** with CUDA 12.6 support for GPU acceleration
- **Transformers** (Hugging Face) for deep learning models
- **OpenCV** for image processing
- **Intel RealSense SDK** (pyrealsense2) for camera integration
- **Matplotlib** for visualization
- **datasets** library for dataset management
- **pywin32** for Windows-specific functionality

### 4. Install Intel RealSense SDK (Optional)
If you're using an Intel RealSense D435i camera:
1. Download and install the [Intel RealSense SDK](https://github.com/IntelRealSense/librealsense/releases)
2. Connect your RealSense camera and verify it's detected

### 5. Verify Installation
```bash
python test.py
```

## Quick Start

### Configure Camera Settings
Edit `config.py` to set your camera index:
```python
CAMERA_INDEX = 0  # Change to your camera index
```

### Run the Application
```bash
python main.py
```

## Usage

### Capture Dataset
Use the dataset capture tool to collect images for training:
```bash
python dataset/capture.py
```

### Train a Model
Train your custom defect detection model:
```bash
python trainer/trainer.py
```

### Run Defect Detection
Start the real-time defect detection:
```bash
python main.py
```

## Troubleshooting

### CUDA Not Available
If PyTorch doesn't detect your GPU:
- Ensure you have the latest NVIDIA drivers installed
- Verify CUDA 12.6 is installed
- Check GPU compatibility with PyTorch

### Camera Not Detected
- Verify camera drivers are installed
- Check camera index in `config.py`
- For RealSense cameras, ensure the Intel RealSense SDK is properly installed

### Module Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify your virtual environment is activated

## License
See [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

