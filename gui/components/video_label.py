"""Video display label component with optional ROI polygon drawing."""

import time
from collections import deque
from typing import List, Tuple, Optional

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QImage, QPixmap, QMouseEvent, QPainter, QPen, QColor, QPolygonF


class VideoLabel(QLabel):
    """Custom label for displaying video frames.

    Supports an interactive "draw ROI" mode where the user clicks to
    place polygon vertices.  Right-click (or double-click) closes the
    polygon and emits :pyattr:`roi_polygon_drawn`.
    """

    # Emitted when the user finishes drawing a polygon.
    # Carries a list of (x, y) tuples in **frame** (pixel) coordinates.
    roi_polygon_drawn = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #000000; border: none;")
        self.setMinimumSize(800, 480)
        self.setMouseTracking(True)  # track mouse for live preview line

        # FPS tracking — keep timestamps of recently displayed frames
        self._frame_timestamps: deque[float] = deque(maxlen=60)
        self._current_fps: float = 0.0

        # Current frame dimensions (needed for coordinate mapping)
        self._frame_w: int = 0
        self._frame_h: int = 0

        # Cached scaled pixmap geometry (updated each display_frame)
        self._pixmap_rect: Optional[tuple] = None  # (x_off, y_off, pw, ph)

        # ROI drawing state
        self._draw_mode: bool = False
        self._roi_points_widget: List[QPointF] = []  # vertices in widget coords
        self._mouse_pos: Optional[QPointF] = None  # live cursor position

    # ---- public API --------------------------------------------------------

    @property
    def fps(self) -> float:
        """Return the current measured FPS."""
        return self._current_fps

    @property
    def draw_roi_mode(self) -> bool:
        return self._draw_mode

    @draw_roi_mode.setter
    def draw_roi_mode(self, enabled: bool) -> None:
        self._draw_mode = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self._roi_points_widget.clear()
            self._mouse_pos = None
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._roi_points_widget.clear()
            self._mouse_pos = None

    # ---- FPS ---------------------------------------------------------------

    def _update_fps(self):
        """Recalculate FPS based on recent frame timestamps."""
        now = time.perf_counter()
        self._frame_timestamps.append(now)
        if len(self._frame_timestamps) >= 2:
            elapsed = self._frame_timestamps[-1] - self._frame_timestamps[0]
            if elapsed > 0:
                self._current_fps = (len(self._frame_timestamps) - 1) / elapsed

    # ---- frame display -----------------------------------------------------

    def display_frame(self, frame):
        """Display a video frame (BGR numpy array)."""
        if frame is None:
            return

        self._update_fps()

        import cv2
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        height, width, channels = frame_rgb.shape
        self._frame_w = width
        self._frame_h = height
        bytes_per_line = channels * width

        q_image = QImage(
            frame_rgb.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

        # Cache the offset / size so we can map mouse coords → frame coords
        pw, ph = scaled_pixmap.width(), scaled_pixmap.height()
        x_off = (self.width() - pw) // 2
        y_off = (self.height() - ph) // 2
        self._pixmap_rect = (x_off, y_off, pw, ph)

        # If we are in draw mode, paint the in-progress polygon on top
        if self._draw_mode and self._roi_points_widget:
            painter = QPainter(scaled_pixmap)
            self._paint_roi_overlay(painter, x_off, y_off, pw, ph)
            painter.end()

        self.setPixmap(scaled_pixmap)

    # ---- coordinate mapping ------------------------------------------------

    def _widget_to_frame(self, pos: QPointF) -> Optional[Tuple[int, int]]:
        """Map a widget coordinate to the original frame pixel coordinate."""
        if self._pixmap_rect is None or self._frame_w == 0:
            return None

        x_off, y_off, pw, ph = self._pixmap_rect

        # Position relative to the scaled pixmap
        rx = pos.x() - x_off
        ry = pos.y() - y_off

        if rx < 0 or ry < 0 or rx >= pw or ry >= ph:
            return None  # outside the video area

        # Scale to original frame size
        fx = int(rx / pw * self._frame_w)
        fy = int(ry / ph * self._frame_h)

        return (
            max(0, min(fx, self._frame_w - 1)),
            max(0, min(fy, self._frame_h - 1)),
        )

    # ---- ROI overlay painting (on the pixmap, in widget coords) -----------

    def _paint_roi_overlay(self, painter: QPainter, x_off: int, y_off: int,
                           pw: int, ph: int):
        """Draw the in-progress polygon vertices and edges."""
        pen = QPen(QColor(0, 255, 255), 2)
        painter.setPen(pen)

        # Translate widget points to pixmap-local coords
        pts = []
        for wp in self._roi_points_widget:
            px = wp.x() - x_off
            py = wp.y() - y_off
            pts.append(QPointF(px, py))

        # Draw lines between consecutive vertices
        for i in range(len(pts) - 1):
            painter.drawLine(pts[i], pts[i + 1])

        # Draw a "rubber-band" line from the last vertex to the cursor
        if self._mouse_pos is not None and pts:
            mp = QPointF(self._mouse_pos.x() - x_off,
                         self._mouse_pos.y() - y_off)
            dash_pen = QPen(QColor(0, 255, 255, 150), 1, Qt.PenStyle.DashLine)
            painter.setPen(dash_pen)
            painter.drawLine(pts[-1], mp)
            painter.setPen(pen)

        # Draw vertex dots
        painter.setBrush(QColor(0, 255, 255))
        for p in pts:
            painter.drawEllipse(p, 4, 4)

    # ---- mouse events (ROI drawing) ---------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._draw_mode:
            return super().mousePressEvent(event)

        pos = event.position()

        if event.button() == Qt.MouseButton.RightButton:
            # Close the polygon
            self._finish_polygon()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # Verify the click is inside the video area
            frame_pt = self._widget_to_frame(pos)
            if frame_pt is None:
                return
            self._roi_points_widget.append(pos)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if not self._draw_mode:
            return super().mouseDoubleClickEvent(event)
        # Double-click also closes the polygon
        self._finish_polygon()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._draw_mode:
            self._mouse_pos = event.position()
        super().mouseMoveEvent(event)

    def _finish_polygon(self) -> None:
        """Close the polygon and emit the signal."""
        if len(self._roi_points_widget) < 3:
            # Need at least 3 vertices
            self._roi_points_widget.clear()
            return

        # Convert all widget points to frame coordinates
        frame_points: List[Tuple[int, int]] = []
        for wp in self._roi_points_widget:
            fp = self._widget_to_frame(wp)
            if fp is not None:
                frame_points.append(fp)

        # Exit draw mode
        self._draw_mode = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._roi_points_widget.clear()
        self._mouse_pos = None

        if len(frame_points) >= 3:
            self.roi_polygon_drawn.emit(frame_points)


