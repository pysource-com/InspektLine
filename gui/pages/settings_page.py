"""Settings page — camera selection only."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QFrame, QComboBox)
from PySide6.QtCore import Signal
from gui.styles import DarkTheme, StyleSheets


class SettingsPage(QWidget):
    """Minimal settings configuration page.

    Receives services via constructor injection from MainWindow._open_dialog().
    """

    # Signal when settings dialog should close
    close_requested = Signal()

    # Mapping between UI display names and internal camera type identifiers
    CAMERA_TYPE_MAP = {
        "USB Webcam": "usb-standard",
        "Intel RealSense": "intel-realsense",
        "Daheng GigE": "daheng-gige",
    }
    CAMERA_TYPE_REVERSE = {v: k for k, v in CAMERA_TYPE_MAP.items()}

    def __init__(self, settings_service=None, camera_service=None,
                 inspection_service=None, parent=None, **kwargs):
        super().__init__(parent)
        self._settings = settings_service
        self._camera = camera_service
        self._parent_window = parent
        self.init_ui()

    def init_ui(self):
        """Initialize the settings page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(25)

        # Header with title and close button
        header = self._create_header()
        main_layout.addWidget(header)

        # Camera Selection section
        camera_section = self._create_camera_section()
        main_layout.addWidget(camera_section)

        # Spacer
        main_layout.addStretch()

        # Done button at bottom right
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.done_button = QPushButton("Done")
        self.done_button.setFixedSize(100, 40)
        self.done_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
        """)
        self.done_button.clicked.connect(self._on_done_clicked)
        button_layout.addWidget(self.done_button)

        main_layout.addLayout(button_layout)

    def _create_header(self):
        """Create header with title and close button."""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Title and subtitle
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff;")
        title_layout.addWidget(title)

        subtitle = QLabel("Select camera type and device")
        subtitle.setStyleSheet(f"font-size: 13px; color: {DarkTheme.TEXT_SECONDARY};")
        title_layout.addWidget(subtitle)

        header_layout.addWidget(title_container)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("\u00d7")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DarkTheme.TEXT_SECONDARY};
                border: none;
                font-size: 24px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                color: {DarkTheme.TEXT_PRIMARY};
            }}
        """)
        close_btn.clicked.connect(self._on_close_clicked)
        header_layout.addWidget(close_btn)

        return header

    def _create_section_title(self, text):
        """Create a section title label."""
        label = QLabel(text)
        label.setStyleSheet("font-size: 14px; font-weight: 600; color: #fff; margin-bottom: 8px;")
        return label

    def _create_card(self):
        """Create a styled card container."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        return card

    def _create_camera_section(self):
        """Create camera selection section with type and device dropdowns."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section title
        layout.addWidget(self._create_section_title("Camera Selection"))

        # Card
        card = self._create_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(12)

        # ---- Camera Type ----
        type_label = QLabel("Camera Type")
        type_label.setStyleSheet(f"font-size: 12px; color: {DarkTheme.TEXT_SECONDARY};")
        card_layout.addWidget(type_label)

        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems(list(self.CAMERA_TYPE_MAP.keys()))
        self.camera_type_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_type_combo.setFixedHeight(45)
        card_layout.addWidget(self.camera_type_combo)

        # Select current type from settings
        if self._settings:
            display = self.CAMERA_TYPE_REVERSE.get(
                self._settings.camera.camera_type, "USB Webcam"
            )
            idx = self.camera_type_combo.findText(display)
            if idx >= 0:
                self.camera_type_combo.setCurrentIndex(idx)

        # ---- Camera Device ----
        device_label = QLabel("Camera Device")
        device_label.setStyleSheet(
            f"font-size: 12px; color: {DarkTheme.TEXT_SECONDARY}; margin-top: 6px;"
        )
        card_layout.addWidget(device_label)

        self.camera_device_combo = QComboBox()
        self.camera_device_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_device_combo.setFixedHeight(45)
        card_layout.addWidget(self.camera_device_combo)

        # Status label (shown when no devices found)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; "
            f"font-style: italic; margin-top: 4px;"
        )
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        card_layout.addWidget(self.status_label)

        # Refresh button
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
        self.refresh_btn.clicked.connect(self._populate_camera_devices)
        card_layout.addWidget(self.refresh_btn)

        layout.addWidget(card)

        # Wire type change → re-enumerate devices
        self.camera_type_combo.currentIndexChanged.connect(
            lambda _: self._populate_camera_devices()
        )

        # Initial population
        self._populate_camera_devices()

        return container

    def _populate_camera_devices(self):
        """Populate camera device dropdown by enumerating devices for the selected type."""
        internal_type = self.CAMERA_TYPE_MAP.get(
            self.camera_type_combo.currentText(), "usb-standard"
        )

        devices = []
        if self._camera is not None:
            try:
                devices = self._camera.get_cameras_list(internal_type)
            except Exception as exc:
                print(f"[SettingsPage] Enumeration error: {exc}")

        self.camera_device_combo.blockSignals(True)
        self.camera_device_combo.clear()

        if devices:
            for dev in devices:
                self.camera_device_combo.addItem(
                    dev.get("name", f"Device {dev['index']}"),
                    userData=dev["index"],
                )
            self.status_label.hide()

            # Re-select the previously saved index if it exists
            if self._settings:
                saved_idx = self._settings.camera.camera_index
                for i in range(self.camera_device_combo.count()):
                    if self.camera_device_combo.itemData(i) == saved_idx:
                        self.camera_device_combo.setCurrentIndex(i)
                        break
        else:
            self.camera_device_combo.addItem("No devices found")
            self.status_label.setText(
                "No cameras detected for this type. Check connections and drivers."
            )
            self.status_label.show()

        self.camera_device_combo.blockSignals(False)

    def _on_close_clicked(self):
        """Handle close button click."""
        self.close_requested.emit()
        if self.parent() and hasattr(self.parent(), 'close'):
            self.parent().close()

    def _on_done_clicked(self):
        """Handle done button click — save and close."""
        self._save_settings()
        self._on_close_clicked()

    def _save_settings(self):
        """Persist current UI state back to SettingsService."""
        if not self._settings:
            return

        changed = False

        # Camera type
        new_type = self.CAMERA_TYPE_MAP.get(
            self.camera_type_combo.currentText(), "usb-standard"
        )
        if new_type != self._settings.camera.camera_type:
            self._settings.camera.camera_type = new_type
            changed = True

        # Camera device index (stored as userData on the combo item)
        device_data = self.camera_device_combo.currentData()
        new_index = device_data if device_data is not None else 0
        if new_index != self._settings.camera.camera_index:
            self._settings.camera.camera_index = new_index
            changed = True

        self._settings.save()

        if changed and self._parent_window and hasattr(self._parent_window, "refresh_camera"):
            self._parent_window.refresh_camera()
