"""Camera feed page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton)
from PySide6.QtCore import Qt
from gui.components import VideoLabel
from gui.styles import StyleSheets, DarkTheme


class CameraPage(QWidget):
    """Main camera feed page with controls.

    Receives services via constructor injection from MainWindow._open_dialog().
    """

    def __init__(self, settings_service=None, camera_service=None,
                 dataset_service=None, inspection_service=None,
                 db=None, parent=None):
        super().__init__(parent)
        self._settings = settings_service
        self._camera = camera_service
        self._inspection = inspection_service
        self._parent_window = parent
        self.init_ui()

    def init_ui(self):
        """Initialize the camera page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_layout = self.create_header()
        layout.addLayout(header_layout)

        video_container = self.create_video_container()
        layout.addWidget(video_container, stretch=1)

        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_header(self):
        """Create the page header with title and controls."""
        header_layout = QHBoxLayout()

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
        live_badge.setStyleSheet(f"""
            background-color: {DarkTheme.SUCCESS};
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

        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.setSpacing(10)

        zoom_in_btn = QPushButton("🔍")
        zoom_in_btn.setFixedSize(40, 40)
        zoom_in_btn.setStyleSheet(StyleSheets.get_icon_button_style())
        control_buttons_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("🔎")
        zoom_out_btn.setFixedSize(40, 40)
        zoom_out_btn.setStyleSheet(StyleSheets.get_icon_button_style())
        control_buttons_layout.addWidget(zoom_out_btn)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet(StyleSheets.get_icon_button_style())
        if self._parent_window and hasattr(self._parent_window, "refresh_camera"):
            refresh_btn.clicked.connect(self._parent_window.refresh_camera)
        control_buttons_layout.addWidget(refresh_btn)

        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setFixedSize(40, 40)
        fullscreen_btn.setStyleSheet(StyleSheets.get_icon_button_style())
        control_buttons_layout.addWidget(fullscreen_btn)

        header_layout.addLayout(control_buttons_layout)
        return header_layout

    def create_video_container(self):
        """Create the video display container."""
        video_container = QWidget()
        video_container.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
            }}
        """)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(10, 10, 10, 10)

        self.video_label = VideoLabel()
        video_layout.addWidget(self.video_label)

        info_overlay = self.create_info_overlay()
        video_layout.addWidget(info_overlay)

        return video_container

    def create_info_overlay(self):
        """Create an info overlay showing frame details."""
        overlay = QWidget()
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 180); border-radius: 6px;")
        overlay.setMaximumHeight(40)

        overlay_layout = QHBoxLayout(overlay)
        overlay_layout.setContentsMargins(15, 8, 15, 8)
        overlay_layout.setSpacing(20)

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"color: {DarkTheme.SUCCESS}; font-size: 16px;")
        overlay_layout.addWidget(self.status_indicator)

        status_text = QLabel("Connected")
        status_text.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(status_text)

        overlay_layout.addStretch()

        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px;")
        overlay_layout.addWidget(fps_label)

        self.fps_value = QLabel("30")
        self.fps_value.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(self.fps_value)

        res_label = QLabel("Resolution:")
        res_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; margin-left: 15px;")
        overlay_layout.addWidget(res_label)

        self.resolution_value = QLabel("1920×1080")
        self.resolution_value.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(self.resolution_value)

        return overlay

    def create_bottom_panel(self):
        """Create the bottom control panel with buttons."""
        panel = QWidget()
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 8px;
            }}
        """)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 15, 20, 15)
        panel_layout.setSpacing(15)

        buttons_layout = self.create_button_row()
        panel_layout.addLayout(buttons_layout)

        return panel

    def create_button_row(self):
        """Create the bottom button row."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        start_btn = QPushButton("▶ Start Inspection")
        start_btn.setFixedHeight(50)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {DarkTheme.PRIMARY_PRESSED};
            }}
        """)
        if self._parent_window and hasattr(self._parent_window, "toggle_inspection"):
            start_btn.clicked.connect(self._parent_window.toggle_inspection)
        buttons_layout.addWidget(start_btn, stretch=2)

        capture_btn = self.create_control_button("📷 Capture")
        buttons_layout.addWidget(capture_btn)

        pause_btn = self.create_control_button("⏸", is_square=True)
        if self._parent_window and hasattr(self._parent_window, "toggle_pause"):
            pause_btn.clicked.connect(self._parent_window.toggle_pause)
        buttons_layout.addWidget(pause_btn)

        record_btn = self.create_control_button("⏺", is_square=True, color=DarkTheme.ERROR)
        buttons_layout.addWidget(record_btn)

        return buttons_layout

    def create_control_button(self, text, is_square=False, color=None):
        """Create a control button."""
        btn = QPushButton(text)
        if is_square:
            btn.setFixedSize(50, 50)
        else:
            btn.setFixedHeight(50)

        text_color = color if color else "white"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_HOVER};
                color: {text_color};
                border: none;
                border-radius: 8px;
                font-size: {'18px' if is_square else '14px'};
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {DarkTheme.BG_INPUT};
            }}
        """)
        return btn

