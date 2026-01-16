"""Video display label component."""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap


class VideoLabel(QLabel):
    """Custom label for displaying video frames."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #000000; border: none;")
        self.setMinimumSize(800, 480)

    def display_frame(self, frame):
        """
        Display a video frame.

        Args:
            frame: NumPy array representing the frame (BGR format)
        """
        if frame is None:
            return

        # Convert BGR to RGB
        frame_rgb = frame[..., ::-1].copy()

        # Get frame dimensions
        height, width, channels = frame_rgb.shape
        bytes_per_line = channels * width

        # Create QImage from frame data
        q_image = QImage(
            frame_rgb.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        # Scale to fit while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Display the frame
        self.setPixmap(scaled_pixmap)

