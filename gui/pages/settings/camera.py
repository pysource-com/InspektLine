"""Camera settings section."""

from PySide6.QtWidgets import QComboBox, QCheckBox, QSlider, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from gui.styles import StyleSheets, DarkTheme
from .base import BaseSettingsSection


class CameraSettings(BaseSettingsSection):
    """Camera configuration settings section."""

    def __init__(self, parent=None):
        """Initialize camera settings section."""
        super().__init__("Camera Configuration", parent)
        self._init_camera_controls()

    def _init_camera_controls(self):
        """Initialize all camera control widgets."""
        # Camera Type
        self.add_field_label("Camera Type")

        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems(["USB Webcam", "Intel RealSense"])
        self.camera_type_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_type_combo.setFixedHeight(45)
        self.camera_type_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("camera_type", value)
        )
        self.main_layout.addWidget(self.camera_type_combo)

        # Camera Device
        self.add_field_label("Camera Device", top_margin=10)

        self.camera_device_combo = QComboBox()
        self.camera_device_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_device_combo.setFixedHeight(45)
        self.camera_device_combo.currentIndexChanged.connect(
            lambda value: self.emit_setting_changed("camera_device", value)
        )
        self.main_layout.addWidget(self.camera_device_combo)

        # Resolution and Frame Rate row
        self._create_resolution_fps_controls()

        # Autofocus
        self._create_autofocus_control()

        # Manual Focus
        self._create_manual_focus_control()

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

        self.main_layout.addLayout(res_fps_layout)

    def _create_autofocus_control(self):
        """Create autofocus checkbox control."""
        self.autofocus_checkbox = QCheckBox("Enable auto-focus")
        self.autofocus_checkbox.setChecked(False)  # Disabled by default
        self.autofocus_checkbox.setStyleSheet(StyleSheets.get_checkbox_style())
        self.autofocus_checkbox.stateChanged.connect(self._on_autofocus_changed)
        self.main_layout.addWidget(self.autofocus_checkbox)

    def _create_manual_focus_control(self):
        """Create manual focus slider control."""
        self.add_field_label("Manual Focus", top_margin=15)

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

        self.main_layout.addLayout(focus_control_layout)

        # Info text
        info_label = QLabel("Note: Manual focus is only available when auto-focus is disabled")
        info_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; "
            f"font-style: italic; margin-top: 5px;"
        )
        info_label.setWordWrap(True)
        self.main_layout.addWidget(info_label)

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

