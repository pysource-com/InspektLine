"""Camera settings section — camera type and device selection only."""

from PySide6.QtWidgets import QComboBox, QLabel, QPushButton
from gui.styles import StyleSheets, DarkTheme
from .base import BaseSettingsSection


class CameraSettings(BaseSettingsSection):
    """Camera configuration settings section.

    Provides two controls:
    1. Camera Type  — USB Webcam / Intel RealSense / Daheng GigE
    2. Camera Device — dynamically enumerated list for the selected type.
    """

    # Mapping between UI display names and internal camera type identifiers
    CAMERA_TYPE_MAP = {
        "USB Webcam": "usb-standard",
        "Intel RealSense": "intel-realsense",
        "Daheng GigE": "daheng-gige",
    }
    CAMERA_TYPE_REVERSE = {v: k for k, v in CAMERA_TYPE_MAP.items()}

    def __init__(self, parent=None):
        super().__init__("Camera Configuration", parent)
        self._camera_service = None
        self._init_controls()

    # ---- public API --------------------------------------------------------

    def set_camera_service(self, camera_service):
        """Inject camera service for device enumeration."""
        self._camera_service = camera_service
        self._refresh_device_list()

    # ---- UI setup ----------------------------------------------------------

    def _init_controls(self):
        """Build the two combo-box controls."""
        # -- Camera Type -----------------------------------------------------
        type_label = QLabel("Camera Type")
        type_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 4px;"
        )
        self.main_layout.addWidget(type_label)

        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems(list(self.CAMERA_TYPE_MAP.keys()))
        self.camera_type_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_type_combo.setFixedHeight(45)
        self.camera_type_combo.currentTextChanged.connect(self._on_type_changed)
        self.main_layout.addWidget(self.camera_type_combo)

        # -- Camera Device ---------------------------------------------------
        device_label = QLabel("Camera Device")
        device_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; "
            f"margin-top: 12px; margin-bottom: 4px;"
        )
        self.main_layout.addWidget(device_label)

        self.camera_device_combo = QComboBox()
        self.camera_device_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_device_combo.setFixedHeight(45)
        self.camera_device_combo.currentIndexChanged.connect(
            lambda idx: self.emit_setting_changed("camera_device", idx)
        )
        self.main_layout.addWidget(self.camera_device_combo)

        # -- Status label (shown when no devices found) ----------------------
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; "
            f"font-style: italic; margin-top: 6px;"
        )
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        self.main_layout.addWidget(self.status_label)

        # -- Refresh button --------------------------------------------------
        self.refresh_btn = QPushButton("Refresh devices")
        self.refresh_btn.setFixedHeight(36)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DarkTheme.PRIMARY};
                border: 1px solid {DarkTheme.PRIMARY};
                border-radius: 6px;
                font-size: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
            }}
        """)
        self.refresh_btn.clicked.connect(self._refresh_device_list)
        self.main_layout.addWidget(self.refresh_btn)

        # Push everything to the top
        self.main_layout.addStretch()

    # ---- slots / helpers ---------------------------------------------------

    def _on_type_changed(self, display_name: str):
        """Handle camera type combo change."""
        internal_type = self.CAMERA_TYPE_MAP.get(display_name, "usb-standard")
        self.emit_setting_changed("camera_type", internal_type)
        self._refresh_device_list()

    def _refresh_device_list(self):
        """Re-enumerate devices for the currently selected camera type."""
        internal_type = self.CAMERA_TYPE_MAP.get(
            self.camera_type_combo.currentText(), "usb-standard"
        )

        devices = []
        if self._camera_service is not None:
            try:
                devices = self._camera_service.get_cameras_list(internal_type)
            except Exception as exc:
                print(f"[CameraSettings] Enumeration error: {exc}")

        self.camera_device_combo.blockSignals(True)
        self.camera_device_combo.clear()

        if devices:
            for dev in devices:
                self.camera_device_combo.addItem(
                    dev.get("name", f"Device {dev['index']}"),
                    userData=dev["index"],
                )
            self.status_label.hide()
        else:
            self.camera_device_combo.addItem("No devices found")
            self.status_label.setText(
                "No cameras detected for this type. "
                "Check connections and drivers."
            )
            self.status_label.show()

        self.camera_device_combo.blockSignals(False)

    # ---- settings persistence helpers --------------------------------------

    def get_settings(self) -> dict:
        """Return current widget state as a dict."""
        device_data = self.camera_device_combo.currentData()
        return {
            "camera_type": self.CAMERA_TYPE_MAP.get(
                self.camera_type_combo.currentText(), "usb-standard"
            ),
            "camera_device": device_data if device_data is not None else 0,
        }

    def load_settings(self, settings: dict):
        """Populate widgets from a dict (e.g. from SettingsService)."""
        if "camera_type" in settings:
            display = self.CAMERA_TYPE_REVERSE.get(
                settings["camera_type"], settings["camera_type"]
            )
            idx = self.camera_type_combo.findText(display)
            if idx >= 0:
                self.camera_type_combo.setCurrentIndex(idx)

        if "camera_device" in settings:
            for i in range(self.camera_device_combo.count()):
                if self.camera_device_combo.itemData(i) == settings["camera_device"]:
                    self.camera_device_combo.setCurrentIndex(i)
                    break
