"""Settings page with minimal, focused UI."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QFrame, QComboBox, QSlider)
from PySide6.QtCore import Qt, Signal
from gui.styles import DarkTheme, StyleSheets


class SettingsPage(QWidget):
    """Minimal settings configuration page."""

    # Signal when settings dialog should close
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
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

        # Active Detection Model section
        model_section = self._create_model_section()
        main_layout.addWidget(model_section)

        # Detection Settings section
        detection_section = self._create_detection_section()
        main_layout.addWidget(detection_section)

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

        subtitle = QLabel("Configure inspection parameters")
        subtitle.setStyleSheet(f"font-size: 13px; color: {DarkTheme.TEXT_SECONDARY};")
        title_layout.addWidget(subtitle)

        header_layout.addWidget(title_container)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("×")
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
        """Create camera selection section."""
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
        card_layout.setSpacing(10)

        # Camera Device label
        device_label = QLabel("Camera Device")
        device_label.setStyleSheet(f"font-size: 12px; color: {DarkTheme.TEXT_SECONDARY};")
        card_layout.addWidget(device_label)

        # Camera device dropdown
        self.camera_device_combo = QComboBox()
        self.camera_device_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_device_combo.setFixedHeight(45)
        self._populate_camera_devices()
        card_layout.addWidget(self.camera_device_combo)

        layout.addWidget(card)
        return container

    def _populate_camera_devices(self):
        """Populate camera device dropdown with available cameras."""
        # Try to detect cameras, fallback to generic options
        try:
            import cv2
            cameras = []
            for i in range(5):  # Check first 5 indices
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Try to get camera name (platform specific)
                    cameras.append(f"Camera {i}")
                    cap.release()

            if cameras:
                self.camera_device_combo.addItems(cameras)
            else:
                self.camera_device_combo.addItems(["No camera detected"])
        except Exception:
            self.camera_device_combo.addItems(["Logitech Webcam C920"])

    def _create_model_section(self):
        """Create active detection model section."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section title
        layout.addWidget(self._create_section_title("Active Detection Model"))

        # Card
        card = self._create_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 30, 20, 30)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Brain icon placeholder
        icon_label = QLabel("🧠")
        icon_label.setStyleSheet("font-size: 36px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)

        # No models text
        no_model_label = QLabel("No models trained yet")
        no_model_label.setStyleSheet(f"font-size: 14px; color: {DarkTheme.TEXT_SECONDARY};")
        no_model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(no_model_label)

        # Hint text
        hint_label = QLabel("Train your first model in Dataset & Training")
        hint_label.setStyleSheet(f"font-size: 12px; color: {DarkTheme.TEXT_DISABLED};")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(hint_label)

        layout.addWidget(card)
        return container

    def _create_detection_section(self):
        """Create detection settings section."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section title
        layout.addWidget(self._create_section_title("Detection Settings"))

        # Card
        card = self._create_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(15)

        # Confidence Threshold
        threshold_container = QWidget()
        threshold_layout = QVBoxLayout(threshold_container)
        threshold_layout.setContentsMargins(0, 0, 0, 0)
        threshold_layout.setSpacing(8)

        threshold_label = QLabel("Confidence Threshold")
        threshold_label.setStyleSheet(f"font-size: 12px; color: {DarkTheme.TEXT_SECONDARY};")
        threshold_layout.addWidget(threshold_label)

        # Slider with value labels
        slider_container = QWidget()
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(5)

        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setMinimum(50)
        self.confidence_slider.setMaximum(99)
        self.confidence_slider.setValue(85)
        self.confidence_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: {DarkTheme.BG_INPUT};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {DarkTheme.PRIMARY};
                border: 2px solid white;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {DarkTheme.PRIMARY};
                border-radius: 3px;
            }}
        """)
        slider_layout.addWidget(self.confidence_slider)

        # Value labels row
        labels_layout = QHBoxLayout()
        labels_layout.setContentsMargins(0, 0, 0, 0)

        min_label = QLabel("50%")
        min_label.setStyleSheet(f"font-size: 11px; color: {DarkTheme.TEXT_DISABLED};")
        labels_layout.addWidget(min_label)

        self.threshold_value_label = QLabel("85%")
        self.threshold_value_label.setStyleSheet(f"font-size: 11px; color: {DarkTheme.TEXT_SECONDARY};")
        self.threshold_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels_layout.addWidget(self.threshold_value_label)

        max_label = QLabel("99%")
        max_label.setStyleSheet(f"font-size: 11px; color: {DarkTheme.TEXT_DISABLED};")
        max_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        labels_layout.addWidget(max_label)

        slider_layout.addLayout(labels_layout)
        threshold_layout.addWidget(slider_container)

        # Connect slider to update label
        self.confidence_slider.valueChanged.connect(
            lambda v: self.threshold_value_label.setText(f"{v}%")
        )

        card_layout.addWidget(threshold_container)

        # Detection Frequency
        frequency_container = QWidget()
        frequency_layout = QVBoxLayout(frequency_container)
        frequency_layout.setContentsMargins(0, 0, 0, 0)
        frequency_layout.setSpacing(8)

        frequency_label = QLabel("Detection Frequency")
        frequency_label.setStyleSheet(f"font-size: 12px; color: {DarkTheme.TEXT_SECONDARY};")
        frequency_layout.addWidget(frequency_label)

        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems([
            "Every 0.5 seconds",
            "Every 1 second",
            "Every 1.5 seconds",
            "Every 2 seconds",
            "Every 3 seconds",
            "Continuous"
        ])
        self.frequency_combo.setCurrentText("Every 1.5 seconds")
        self.frequency_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.frequency_combo.setFixedHeight(45)
        frequency_layout.addWidget(self.frequency_combo)

        card_layout.addWidget(frequency_container)

        layout.addWidget(card)
        return container

    def _on_close_clicked(self):
        """Handle close button click."""
        self.close_requested.emit()
        # Close parent dialog if available
        if self.parent() and hasattr(self.parent(), 'close'):
            self.parent().close()

    def _on_done_clicked(self):
        """Handle done button click."""
        # Save settings if needed
        self._save_settings()
        self._on_close_clicked()

    def _save_settings(self):
        """Save current settings."""
        if self.parent_window:
            # Update parent window's confidence threshold
            self.parent_window.confidence_threshold = self.confidence_slider.value()

            # Update camera device if changed
            if hasattr(self.parent_window, 'camera_index'):
                new_index = self.camera_device_combo.currentIndex()
                if new_index != self.parent_window.camera_index:
                    self.parent_window.camera_index = new_index
                    if hasattr(self.parent_window, 'refresh_camera'):
                        self.parent_window.refresh_camera()

    def get_settings(self) -> dict:
        """Get all current settings."""
        return {
            "camera_device": self.camera_device_combo.currentIndex(),
            "confidence_threshold": self.confidence_slider.value(),
            "detection_frequency": self.frequency_combo.currentText(),
        }

    def load_settings(self, settings: dict):
        """Load settings from a dictionary."""
        if "camera_device" in settings:
            self.camera_device_combo.setCurrentIndex(settings["camera_device"])
        if "confidence_threshold" in settings:
            self.confidence_slider.setValue(int(settings["confidence_threshold"]))
        if "detection_frequency" in settings:
            self.frequency_combo.setCurrentText(settings["detection_frequency"])
