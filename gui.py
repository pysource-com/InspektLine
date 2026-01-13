import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
import numpy as np
from camera.camera import Camera


class VideoDisplayWidget(QMainWindow):
    """Simple class that loads and displays a video in real-time using PySide6."""

    def __init__(self, camera_index=0, camera_type="usb-standard"):
        """
        Initialize the video display widget.

        Args:
            camera_index: Camera index (0 for default camera)
            camera_type: Type of camera ("usb-standard" or "intel-realsense")
        """
        super().__init__()
        self.camera_index = camera_index
        self.camera_type = camera_type
        self.camera = Camera()
        self.cap = None
        self.timer = None

        self.init_ui()
        self.start_video()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Video Display")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create label to display video frames
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_label)

        # Create control buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_video)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_video)
        button_layout.addWidget(self.stop_button)

        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)
        button_layout.addWidget(self.quit_button)

        layout.addLayout(button_layout)

    def start_video(self):
        """Start capturing and displaying video."""
        if self.cap is None:
            try:
                self.cap = self.camera.load_cap(self.camera_index, self.camera_type)
            except Exception as e:
                print(f"Error: Could not open camera {self.camera_index}: {e}")
                return

        # Set up timer to update frames
        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)

        self.timer.start(30)  # Update every 30ms (~33 FPS)

    def stop_video(self):
        """Stop capturing and displaying video."""
        if self.timer is not None:
            self.timer.stop()

    def update_frame(self):
        """Read and display the next video frame."""
        if self.cap is not None:
            ret, frame = self.camera.read_frame(self.cap)

            if ret:
                # Convert the frame from BGR (OpenCV) to RGB (Qt) using numpy
                frame_rgb = frame[..., ::-1].copy()

                # Get frame dimensions
                height, width, channels = frame_rgb.shape
                bytes_per_line = channels * width

                # Create QImage from frame data
                q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)

                # Scale the image to fit the label while maintaining aspect ratio
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                # Display the frame
                self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        """Clean up when the window is closed."""
        self.stop_video()
        if self.cap is not None:
            self.camera.release_cap(self.cap)
        event.accept()


def main():
    """Main function to run the video display application."""
    app = QApplication(sys.argv)

    # Use default camera (0) with USB standard camera or Intel RealSense
    # For USB camera: camera_type="usb-standard"
    # For Intel RealSense: camera_type="intel-realsense"
    window = VideoDisplayWidget(camera_index=0, camera_type="usb-standard")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

