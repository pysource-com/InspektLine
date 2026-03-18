"""Detection parameters settings section."""

from PySide6.QtWidgets import QLineEdit
from gui.styles import StyleSheets
from .base import BaseSettingsSection


class DetectionSettings(BaseSettingsSection):
    """Detection parameters configuration section."""

    def __init__(self, parent=None):
        """Initialize detection settings section."""
        super().__init__("Detection Parameters", parent)
        self._init_detection_controls()

    def _init_detection_controls(self):
        """Initialize all detection control widgets."""
        # Confidence Threshold
        self.add_field_label("Confidence Threshold (%)")

        self.confidence_input = QLineEdit("85")
        self.confidence_input.setStyleSheet(StyleSheets.get_input_style())
        self.confidence_input.setFixedHeight(50)
        self.confidence_input.textChanged.connect(
            lambda value: self.emit_setting_changed("confidence_threshold", value)
        )
        self.main_layout.addWidget(self.confidence_input)

        # Minimum Defect Size
        self.add_field_label("Minimum Defect Size (px)", top_margin=10)

        self.defect_size_input = QLineEdit("10")
        self.defect_size_input.setStyleSheet(StyleSheets.get_input_style())
        self.defect_size_input.setFixedHeight(50)
        self.defect_size_input.textChanged.connect(
            lambda value: self.emit_setting_changed("min_defect_size", value)
        )
        self.main_layout.addWidget(self.defect_size_input)

        # --- Model parameters ---
        self.add_field_label("Number of Classes", top_margin=10)

        self.num_classes_input = QLineEdit("1")
        self.num_classes_input.setStyleSheet(StyleSheets.get_input_style())
        self.num_classes_input.setFixedHeight(50)
        self.num_classes_input.textChanged.connect(
            lambda value: self.emit_setting_changed("num_classes", value)
        )
        self.main_layout.addWidget(self.num_classes_input)

        self.add_field_label("Model Input Resolution", top_margin=10)

        self.model_resolution_input = QLineEdit("560")
        self.model_resolution_input.setStyleSheet(StyleSheets.get_input_style())
        self.model_resolution_input.setFixedHeight(50)
        self.model_resolution_input.textChanged.connect(
            lambda value: self.emit_setting_changed("model_resolution", value)
        )
        self.main_layout.addWidget(self.model_resolution_input)

    def get_settings(self) -> dict:
        """
        Get all current detection settings.

        Returns:
            dict: Current detection settings
        """
        return {
            "confidence_threshold": self.confidence_input.text(),
            "min_defect_size": self.defect_size_input.text(),
            "num_classes": self.num_classes_input.text(),
            "model_resolution": self.model_resolution_input.text(),
        }

    def load_settings(self, settings: dict):
        """
        Load detection settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        if "confidence_threshold" in settings:
            self.confidence_input.setText(str(settings["confidence_threshold"]))

        if "min_defect_size" in settings:
            self.defect_size_input.setText(str(settings["min_defect_size"]))

        if "num_classes" in settings:
            self.num_classes_input.setText(str(settings["num_classes"]))

        if "model_resolution" in settings:
            self.model_resolution_input.setText(str(settings["model_resolution"]))

