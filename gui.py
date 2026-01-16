import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QSlider, QFrame)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from camera.camera import Camera


class SidebarButton(QPushButton):
    """Custom sidebar button with icon."""

    def __init__(self, icon_text, parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #666;
                border: none;
                border-radius: 8px;
                font-size: 24px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #0066ff;
            }
            QPushButton:checked {
                background-color: #0066ff;
                color: #fff;
            }
        """)
        self.setCheckable(True)


class VideoDisplayWidget(QMainWindow):
    """Main application window with left sidebar and camera feed."""

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
        self.is_inspecting = False
        self.exposure_value = 50
        self.contrast_value = 75

        self.init_ui()
        self.start_video()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("InspektLine")
        self.setGeometry(100, 100, 1280, 800)

        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
            }
            QWidget {
                background-color: #0a0a0a;
                color: #ffffff;
            }
        """)

        # Create central widget with horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create left sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # Create main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Create header with title and controls
        header_layout = QHBoxLayout()

        # Camera feed title with LIVE badge
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        camera_icon = QLabel("📹")
        camera_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(camera_icon)

        title_label = QLabel("Camera Feed")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        title_layout.addWidget(title_label)

        live_badge = QLabel("LIVE")
        live_badge.setStyleSheet("""
            background-color: #00cc00;
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        """)
        title_layout.addWidget(live_badge)
        title_layout.addStretch()

        header_layout.addWidget(title_widget)
        header_layout.addStretch()

        # Camera control buttons
        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.setSpacing(10)

        zoom_in_btn = QPushButton("🔍")
        zoom_in_btn.setFixedSize(40, 40)
        zoom_in_btn.setStyleSheet(self.get_icon_button_style())
        control_buttons_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("🔎")
        zoom_out_btn.setFixedSize(40, 40)
        zoom_out_btn.setStyleSheet(self.get_icon_button_style())
        control_buttons_layout.addWidget(zoom_out_btn)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet(self.get_icon_button_style())
        refresh_btn.clicked.connect(self.refresh_camera)
        control_buttons_layout.addWidget(refresh_btn)

        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setFixedSize(40, 40)
        fullscreen_btn.setStyleSheet(self.get_icon_button_style())
        control_buttons_layout.addWidget(fullscreen_btn)

        header_layout.addLayout(control_buttons_layout)
        content_layout.addLayout(header_layout)

        # Create video display frame with corner brackets
        video_container = QWidget()
        video_container.setStyleSheet("""
            QWidget {
                background-color: #0f0f0f;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
            }
        """)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(10, 10, 10, 10)

        # Create label to display video frames
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000; border: none;")
        self.video_label.setMinimumSize(800, 480)
        video_layout.addWidget(self.video_label)

        content_layout.addWidget(video_container, stretch=1)

        # Bottom control panel
        bottom_panel = self.create_bottom_panel()
        content_layout.addWidget(bottom_panel)

        main_layout.addWidget(content_widget, stretch=1)

    def create_sidebar(self):
        """Create the left sidebar with navigation buttons."""
        sidebar = QFrame()
        sidebar.setFixedWidth(100)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #0f0f0f;
                border-right: 1px solid #1a1a1a;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        # Camera button (active by default)
        camera_btn = SidebarButton("📷")
        camera_btn.setChecked(True)
        sidebar_layout.addWidget(camera_btn)

        # Capture button
        capture_btn = SidebarButton("📸")
        sidebar_layout.addWidget(capture_btn)

        # Database button
        database_btn = SidebarButton("💾")
        sidebar_layout.addWidget(database_btn)

        # Chart button
        chart_btn = SidebarButton("📊")
        sidebar_layout.addWidget(chart_btn)

        # Document button
        document_btn = SidebarButton("📄")
        sidebar_layout.addWidget(document_btn)

        sidebar_layout.addStretch()

        # Settings button at bottom
        settings_btn = SidebarButton("⚙️")
        sidebar_layout.addWidget(settings_btn)

        # Power button at very bottom
        power_btn = SidebarButton("⏻")
        power_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(power_btn)

        return sidebar

    def create_bottom_panel(self):
        """Create the bottom control panel with sliders and buttons."""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 8px;
            }
        """)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 15, 20, 15)
        panel_layout.setSpacing(15)

        # Sliders row
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(30)

        # Exposure slider
        exposure_group = QVBoxLayout()
        exposure_label_layout = QHBoxLayout()
        exposure_label = QLabel("Exposure")
        exposure_label.setStyleSheet("color: #999; font-size: 14px;")
        exposure_label_layout.addWidget(exposure_label)
        exposure_auto = QLabel("Auto")
        exposure_auto.setStyleSheet("color: #999; font-size: 14px;")
        exposure_label_layout.addWidget(exposure_auto)
        exposure_label_layout.addStretch()
        exposure_group.addLayout(exposure_label_layout)

        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setMinimum(0)
        self.exposure_slider.setMaximum(100)
        self.exposure_slider.setValue(self.exposure_value)
        self.exposure_slider.setStyleSheet(self.get_slider_style())
        exposure_group.addWidget(self.exposure_slider)
        sliders_layout.addLayout(exposure_group, stretch=1)

        # Contrast slider
        contrast_group = QVBoxLayout()
        contrast_label_layout = QHBoxLayout()
        contrast_label = QLabel("Contrast")
        contrast_label.setStyleSheet("color: #999; font-size: 14px;")
        contrast_label_layout.addWidget(contrast_label)
        contrast_label_layout.addStretch()
        contrast_value_label = QLabel(f"{self.contrast_value}%")
        contrast_value_label.setStyleSheet("color: #999; font-size: 14px;")
        contrast_label_layout.addWidget(contrast_value_label)
        contrast_group.addLayout(contrast_label_layout)

        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(100)
        self.contrast_slider.setValue(self.contrast_value)
        self.contrast_slider.setStyleSheet(self.get_slider_style())
        self.contrast_slider.valueChanged.connect(
            lambda v: contrast_value_label.setText(f"{v}%")
        )
        contrast_group.addWidget(self.contrast_slider)
        sliders_layout.addLayout(contrast_group, stretch=1)

        panel_layout.addLayout(sliders_layout)

        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # Start Inspection button
        self.start_inspection_btn = QPushButton("▶ Start Inspection")
        self.start_inspection_btn.setFixedHeight(50)
        self.start_inspection_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066ff;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #0052cc;
            }
            QPushButton:pressed {
                background-color: #0047b3;
            }
        """)
        self.start_inspection_btn.clicked.connect(self.toggle_inspection)
        buttons_layout.addWidget(self.start_inspection_btn, stretch=2)

        # Capture button
        capture_btn = QPushButton("📷 Capture")
        capture_btn.setFixedHeight(50)
        capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        buttons_layout.addWidget(capture_btn)

        # Pause button
        pause_btn = QPushButton("⏸")
        pause_btn.setFixedSize(50, 50)
        pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        pause_btn.clicked.connect(self.toggle_pause)
        buttons_layout.addWidget(pause_btn)

        # Record button
        record_btn = QPushButton("⏺")
        record_btn.setFixedSize(50, 50)
        record_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ff4444;
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        buttons_layout.addWidget(record_btn)

        panel_layout.addLayout(buttons_layout)

        return panel

    def get_icon_button_style(self):
        """Get stylesheet for icon buttons."""
        return """
            QPushButton {
                background-color: #1a1a1a;
                color: #999;
                border: none;
                border-radius: 6px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #0a0a0a;
            }
        """

    def get_slider_style(self):
        """Get stylesheet for sliders."""
        return """
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #cc44ff;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #dd66ff;
            }
        """

    def toggle_inspection(self):
        """Toggle inspection mode."""
        self.is_inspecting = not self.is_inspecting
        if self.is_inspecting:
            self.start_inspection_btn.setText("⏹ Stop Inspection")
        else:
            self.start_inspection_btn.setText("▶ Start Inspection")

    def toggle_pause(self):
        """Toggle video pause."""
        if self.timer.isActive():
            self.stop_video()
        else:
            self.start_video()

    def refresh_camera(self):
        """Refresh camera connection."""
        self.stop_video()
        if self.cap is not None:
            self.camera.release_cap(self.cap)
            self.cap = None
        self.start_video()

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
                q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

                # Scale the image to fit the label while maintaining aspect ratio
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
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

