"""Test script for camera settings with live preview."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer
from gui.pages.settings.camera import CameraSettings
from camera.camera import Camera


class TestWindow(QMainWindow):
    """Test window for camera settings with preview."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Settings Preview Test")
        self.setGeometry(100, 100, 1400, 800)

        # Initialize camera
        self.camera = Camera()
        self.cap = None
        self.current_frame = None

        # Create camera settings widget
        self.camera_settings = CameraSettings(parent=self)
        self.setCentralWidget(self.camera_settings)

        # Connect settings changes
        self.camera_settings.settings_changed.connect(self.on_setting_changed)

        # Start camera
        self.start_camera()

        # Update camera frame
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~33 FPS

        # Mock FPS label for display
        self.camera_fps_value = type('obj', (object,), {'text': lambda: "30"})()

    def start_camera(self):
        """Start the camera."""
        try:
            self.cap = self.camera.get_camera_capture(0, "usb-standard")
            print("Camera started successfully")
        except Exception as e:
            print(f"Error starting camera: {e}")

    def update_frame(self):
        """Update the current frame from camera."""
        if self.cap:
            ret, frame = self.camera.read_frame(self.cap)
            if ret:
                self.current_frame = frame

    def get_current_frame(self):
        """Get the current camera frame."""
        return self.current_frame

    def on_setting_changed(self, setting_name, value):
        """Handle setting changes."""
        print(f"Setting changed: {setting_name} = {value}")

    def closeEvent(self, event):
        """Clean up on close."""
        self.timer.stop()
        if self.cap:
            self.camera.release_cap(self.cap)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

