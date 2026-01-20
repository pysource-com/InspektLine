"""Camera feed page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton)
from PySide6.QtCore import Qt
from gui.components import VideoLabel
from gui.styles import StyleSheets, DarkTheme


class CameraPage(QWidget):
    """Main camera feed page with controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()

    def init_ui(self):
        """Initialize the camera page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = self.create_header()
        layout.addLayout(header_layout)

        # Video display
        video_container = self.create_video_container()
        layout.addWidget(video_container, stretch=1)

        # Bottom control panel
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_header(self):
        """Create the page header with title and controls."""
        header_layout = QHBoxLayout()

        # Title with LIVE badge
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

        # Control buttons
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
        if self.parent_window:
            refresh_btn.clicked.connect(self.parent_window.refresh_camera)
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

        # Create video label
        self.video_label = VideoLabel()
        video_layout.addWidget(self.video_label)

        # Add info overlay at the bottom
        info_overlay = self.create_info_overlay()
        video_layout.addWidget(info_overlay)

        return video_container

    def create_info_overlay(self):
        """Create an info overlay showing frame details."""
        overlay = QWidget()
        overlay.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(0, 0, 0, 180);
                border-radius: 6px;
            }}
        """)
        overlay.setMaximumHeight(40)

        overlay_layout = QHBoxLayout(overlay)
        overlay_layout.setContentsMargins(15, 8, 15, 8)
        overlay_layout.setSpacing(20)

        # Connection status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"color: {DarkTheme.SUCCESS}; font-size: 16px;")
        overlay_layout.addWidget(self.status_indicator)

        status_text = QLabel("Connected")
        status_text.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(status_text)

        overlay_layout.addStretch()

        # FPS counter
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px;")
        overlay_layout.addWidget(fps_label)

        self.fps_value = QLabel("30")
        self.fps_value.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(self.fps_value)

        # Resolution info
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


        # Buttons row
        buttons_layout = self.create_button_row()
        panel_layout.addLayout(buttons_layout)

        return panel


    def create_button_row(self):
        """Create the bottom button row."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # Start Inspection button
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
        if self.parent_window:
            start_btn.clicked.connect(self.parent_window.toggle_inspection)
        buttons_layout.addWidget(start_btn, stretch=2)

        # Capture button
        capture_btn = self.create_control_button("📷 Capture")
        buttons_layout.addWidget(capture_btn)

        # Pause button
        pause_btn = self.create_control_button("⏸", is_square=True)
        if self.parent_window:
            pause_btn.clicked.connect(self.parent_window.toggle_pause)
        buttons_layout.addWidget(pause_btn)

        # Record button
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

