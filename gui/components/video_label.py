"""Video display label component."""

import time
from collections import deque

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

        # FPS tracking — keep timestamps of recently displayed frames
        self._frame_timestamps: deque[float] = deque(maxlen=60)
        self._current_fps: float = 0.0

    @property
    def fps(self) -> float:
        """Return the current measured FPS."""
        return self._current_fps

    def _update_fps(self):
        """Recalculate FPS based on recent frame timestamps."""
        now = time.perf_counter()
        self._frame_timestamps.append(now)
        if len(self._frame_timestamps) >= 2:
            elapsed = self._frame_timestamps[-1] - self._frame_timestamps[0]
            if elapsed > 0:
                self._current_fps = (len(self._frame_timestamps) - 1) / elapsed

    def display_frame(self, frame):
        """
        Display a video frame.

        Args:
            frame: NumPy array representing the frame (BGR format)
        """
        if frame is None:
            return

        self._update_fps()

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

