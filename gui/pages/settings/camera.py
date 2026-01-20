"""Camera settings section."""

from PySide6.QtWidgets import (QComboBox, QCheckBox, QSlider, QLabel,
                                QHBoxLayout, QVBoxLayout, QWidget, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from gui.styles import StyleSheets, DarkTheme
from .base import BaseSettingsSection


class CameraSettings(BaseSettingsSection):
    """Camera configuration settings section."""

    def __init__(self, parent=None):
        """Initialize camera settings section."""
        super().__init__("Camera Configuration", parent)

        # Camera feed related
        self.preview_label = None
        self.preview_timer = None

        self._init_split_layout()
        self._init_camera_controls()
        self._init_preview_panel()

    def _init_split_layout(self):
        """Initialize split layout for settings and preview."""
        # Create horizontal layout to hold settings and preview side by side
        self.split_layout = QHBoxLayout()
        self.split_layout.setSpacing(20)

        # Left panel for settings (will contain the existing main_layout)
        self.settings_container = QWidget()
        self.settings_container.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
        """)
        self.settings_layout = QVBoxLayout(self.settings_container)
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_layout.setSpacing(20)

        # Move the main_layout content to settings_layout
        # We'll use settings_layout as the new container for controls
        self.split_layout.addWidget(self.settings_container, stretch=1)

        # Right panel for preview (will be initialized later)
        self.preview_container = QWidget()
        self.preview_container.setMinimumWidth(400)
        self.preview_container.setMaximumWidth(600)
        self.split_layout.addWidget(self.preview_container, stretch=1)

        # Add split layout to main layout
        self.main_layout.addLayout(self.split_layout)

    def _init_camera_controls(self):
        """Initialize all camera control widgets."""
        # Add section subtitle
        subtitle = QLabel("Camera Settings")
        subtitle.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff; margin-bottom: 5px;")
        self.settings_layout.addWidget(subtitle)

        # Camera Type
        self._add_settings_label("Camera Type")

        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems(["USB Webcam", "Intel RealSense"])
        self.camera_type_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_type_combo.setFixedHeight(45)
        self.camera_type_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("camera_type", value)
        )
        self.settings_layout.addWidget(self.camera_type_combo)

        # Camera Device
        self._add_settings_label("Camera Device", top_margin=10)

        self.camera_device_combo = QComboBox()
        self.camera_device_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_device_combo.setFixedHeight(45)
        self.camera_device_combo.currentIndexChanged.connect(
            lambda value: self.emit_setting_changed("camera_device", value)
        )
        self.settings_layout.addWidget(self.camera_device_combo)

        # Resolution and Frame Rate row
        self._create_resolution_fps_controls()

        # Autofocus
        self._create_autofocus_control()

        # Manual Focus
        self._create_manual_focus_control()

        # Add spacer to push content to top
        self.settings_layout.addStretch()

    def _add_settings_label(self, text: str, top_margin: int = 0) -> QLabel:
        """
        Add a field label to settings panel.

        Args:
            text: Label text
            top_margin: Top margin in pixels

        Returns:
            QLabel: The created label
        """
        label = QLabel(text)
        style = f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px;"
        if top_margin > 0:
            style += f" margin-top: {top_margin}px;"
        label.setStyleSheet(style)
        self.settings_layout.addWidget(label)
        return label


    def _create_resolution_fps_controls(self):
        """Create resolution and FPS controls in a horizontal layout."""
        res_fps_layout = QHBoxLayout()
        res_fps_layout.setSpacing(20)

        # Resolution
        res_group = QVBoxLayout()
        res_label = QLabel("Resolution")
        res_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px;"
        )
        res_group.addWidget(res_label)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920 x 1080 (Full HD)",
            "1280 x 720 (HD)",
            "640 x 480 (VGA)"
        ])
        self.resolution_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.resolution_combo.setFixedHeight(45)
        self.resolution_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("resolution", value)
        )
        res_group.addWidget(self.resolution_combo)
        res_fps_layout.addLayout(res_group, stretch=1)

        # Frame Rate
        fps_group = QVBoxLayout()
        fps_label = QLabel("Frame Rate")
        fps_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px;"
        )
        fps_group.addWidget(fps_label)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS", "30 FPS", "15 FPS"])
        self.fps_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.fps_combo.setFixedHeight(45)
        self.fps_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("fps", value)
        )
        fps_group.addWidget(self.fps_combo)
        res_fps_layout.addLayout(fps_group, stretch=1)

        self.settings_layout.addLayout(res_fps_layout)

    def _create_autofocus_control(self):
        """Create autofocus checkbox control."""
        self.autofocus_checkbox = QCheckBox("Enable auto-focus")
        self.autofocus_checkbox.setChecked(False)  # Disabled by default
        self.autofocus_checkbox.setStyleSheet(StyleSheets.get_checkbox_style())
        self.autofocus_checkbox.stateChanged.connect(self._on_autofocus_changed)
        self.settings_layout.addWidget(self.autofocus_checkbox)

    def _create_manual_focus_control(self):
        """Create manual focus slider control."""
        self._add_settings_label("Manual Focus", top_margin=15)

        focus_control_layout = QHBoxLayout()
        focus_control_layout.setSpacing(15)

        self.manual_focus_slider = QSlider(Qt.Orientation.Horizontal)
        self.manual_focus_slider.setMinimum(0)
        self.manual_focus_slider.setMaximum(255)
        self.manual_focus_slider.setValue(128)
        self.manual_focus_slider.setStyleSheet(StyleSheets.get_slider_style())
        self.manual_focus_slider.setEnabled(True)  # Enabled by default since autofocus is off
        self.manual_focus_slider.valueChanged.connect(
            lambda value: self.emit_setting_changed("manual_focus", value)
        )
        focus_control_layout.addWidget(self.manual_focus_slider, stretch=1)

        self.focus_value_label = QLabel("128")
        self.focus_value_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; min-width: 35px;"
        )
        self.manual_focus_slider.valueChanged.connect(
            lambda v: self.focus_value_label.setText(str(v))
        )
        focus_control_layout.addWidget(self.focus_value_label)

        self.settings_layout.addLayout(focus_control_layout)

        # Info text
        info_label = QLabel("Note: Manual focus is only available when auto-focus is disabled")
        info_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; "
            f"font-style: italic; margin-top: 5px;"
        )
        info_label.setWordWrap(True)
        self.settings_layout.addWidget(info_label)

    def _init_preview_panel(self):
        """Initialize the camera preview panel."""
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(10)

        # Preview header
        preview_header = QLabel("Live Preview")
        preview_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff; margin-bottom: 5px;")
        preview_layout.addWidget(preview_header)

        # Preview frame container
        preview_frame = QFrame()
        preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
            }}
        """)
        preview_frame_layout = QVBoxLayout(preview_frame)
        preview_frame_layout.setContentsMargins(10, 10, 10, 10)
        preview_frame_layout.setSpacing(8)

        # Video preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: #000000;
                border-radius: 4px;
                min-height: 300px;
            }}
        """)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setScaledContents(False)
        preview_frame_layout.addWidget(self.preview_label, stretch=1)

        # Preview info overlay
        info_overlay = QWidget()
        info_overlay.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(0, 0, 0, 180);
                border-radius: 6px;
            }}
        """)
        info_overlay.setMaximumHeight(35)

        info_layout = QHBoxLayout(info_overlay)
        info_layout.setContentsMargins(12, 6, 12, 6)
        info_layout.setSpacing(15)

        # LIVE indicator
        self.live_indicator = QLabel("●")
        self.live_indicator.setStyleSheet(f"color: {DarkTheme.SUCCESS}; font-size: 14px;")
        info_layout.addWidget(self.live_indicator)

        live_text = QLabel("LIVE")
        live_text.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 11px; font-weight: bold;")
        info_layout.addWidget(live_text)

        info_layout.addStretch()

        # FPS display
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 10px;")
        info_layout.addWidget(fps_label)

        self.preview_fps_label = QLabel("--")
        self.preview_fps_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 11px; font-weight: bold;")
        info_layout.addWidget(self.preview_fps_label)

        # Resolution display
        res_label = QLabel("Res:")
        res_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 10px; margin-left: 10px;")
        info_layout.addWidget(res_label)

        self.preview_res_label = QLabel("--")
        self.preview_res_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 11px; font-weight: bold;")
        info_layout.addWidget(self.preview_res_label)

        preview_frame_layout.addWidget(info_overlay)
        preview_layout.addWidget(preview_frame, stretch=1)

        # Info text
        info_text = QLabel("Settings changes are applied in real-time to the camera feed above.")
        info_text.setStyleSheet(f"""
            color: {DarkTheme.TEXT_SECONDARY}; 
            font-size: 11px; 
            font-style: italic; 
            margin-top: 8px;
        """)
        info_text.setWordWrap(True)
        preview_layout.addWidget(info_text)

        preview_layout.addStretch()

    def _on_autofocus_changed(self, state):
        """
        Handle autofocus checkbox toggle.

        Args:
            state: Checkbox state
        """
        is_autofocus_enabled = state == Qt.CheckState.Checked.value
        # Enable manual focus slider only when autofocus is disabled
        self.manual_focus_slider.setEnabled(not is_autofocus_enabled)
        self.emit_setting_changed("autofocus", is_autofocus_enabled)

    def get_settings(self) -> dict:
        """
        Get all current camera settings.

        Returns:
            dict: Current camera settings
        """
        return {
            "camera_type": self.camera_type_combo.currentText(),
            "camera_device": self.camera_device_combo.currentIndex(),
            "resolution": self.resolution_combo.currentText(),
            "fps": self.fps_combo.currentText(),
            "autofocus": self.autofocus_checkbox.isChecked(),
            "manual_focus": self.manual_focus_slider.value(),
        }

    def load_settings(self, settings: dict):
        """
        Load camera settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        if "camera_type" in settings:
            index = self.camera_type_combo.findText(settings["camera_type"])
            if index >= 0:
                self.camera_type_combo.setCurrentIndex(index)

        if "camera_device" in settings:
            self.camera_device_combo.setCurrentIndex(settings["camera_device"])

        if "resolution" in settings:
            index = self.resolution_combo.findText(settings["resolution"])
            if index >= 0:
                self.resolution_combo.setCurrentIndex(index)

        if "fps" in settings:
            index = self.fps_combo.findText(settings["fps"])
            if index >= 0:
                self.fps_combo.setCurrentIndex(index)

        if "autofocus" in settings:
            self.autofocus_checkbox.setChecked(settings["autofocus"])

        if "manual_focus" in settings:
            self.manual_focus_slider.setValue(settings["manual_focus"])

    def update_camera_devices(self, devices: list):
        """
        Update the list of available camera devices.

        Args:
            devices: List of device names/IDs
        """
        current = self.camera_device_combo.currentIndex()
        self.camera_device_combo.clear()
        self.camera_device_combo.addItems([str(d) for d in devices])
        if current < len(devices):
            self.camera_device_combo.setCurrentIndex(current)

    def start_preview(self):
        """Start the camera preview timer."""
        if self.preview_timer is None:
            self.preview_timer = QTimer()
            self.preview_timer.timeout.connect(self._update_preview_frame)

        if not self.preview_timer.isActive():
            self.preview_timer.start(33)  # ~30 FPS

    def stop_preview(self):
        """Stop the camera preview timer."""
        if self.preview_timer is not None and self.preview_timer.isActive():
            self.preview_timer.stop()

    def _update_preview_frame(self):
        """Update the preview with the latest camera frame."""
        # Get frame from parent window's camera
        if not self.parent_window or not hasattr(self.parent_window, 'get_current_frame'):
            return

        frame = self.parent_window.get_current_frame()
        if frame is None:
            return

        try:
            # Convert BGR to RGB
            frame_rgb = frame[..., ::-1].copy()

            # Get frame dimensions
            height, width, channels = frame_rgb.shape
            bytes_per_line = channels * width

            # Update resolution label (only once per unique size)
            if not hasattr(self, '_last_preview_size') or self._last_preview_size != (width, height):
                self._last_preview_size = (width, height)
                self.preview_res_label.setText(f"{width}×{height}")

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
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Display the frame
            self.preview_label.setPixmap(scaled_pixmap)

            # Update FPS (calculate from parent if available)
            if hasattr(self.parent_window, 'camera_fps_value'):
                fps_text = self.parent_window.camera_fps_value.text()
                self.preview_fps_label.setText(fps_text)

        except Exception as e:
            print(f"Error updating preview frame: {e}")

    def showEvent(self, event):
        """Handle widget show event to start preview."""
        super().showEvent(event)
        self.start_preview()

    def hideEvent(self, event):
        """Handle widget hide event to stop preview."""
        super().hideEvent(event)
        self.stop_preview()


