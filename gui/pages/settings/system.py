"""System settings section."""

from PySide6.QtWidgets import QCheckBox, QComboBox
from gui.styles import StyleSheets
from .base import BaseSettingsSection


class SystemSettings(BaseSettingsSection):
    """System configuration section."""

    def __init__(self, parent=None):
        """Initialize system settings section."""
        super().__init__("System Configuration", parent)
        self._init_system_controls()

    def _init_system_controls(self):
        """Initialize all system control widgets."""
        # Language
        self.add_field_label("Language")

        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Deutsch", "Français", "Español", "Italiano"])
        self.language_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.language_combo.setFixedHeight(45)
        self.language_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("language", value)
        )
        self.main_layout.addWidget(self.language_combo)

        # Theme
        self.add_field_label("Theme", top_margin=15)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto"])
        self.theme_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.theme_combo.setFixedHeight(45)
        self.theme_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("theme", value)
        )
        self.main_layout.addWidget(self.theme_combo)

        # Auto-start
        self.auto_start = QCheckBox("Launch on system startup")
        self.auto_start.setChecked(False)
        self.auto_start.setStyleSheet(StyleSheets.get_checkbox_style())
        self.auto_start.stateChanged.connect(
            lambda state: self.emit_setting_changed("auto_start", state)
        )
        self.main_layout.addWidget(self.auto_start)

        # Auto-save
        self.auto_save = QCheckBox("Auto-save inspection results")
        self.auto_save.setChecked(True)
        self.auto_save.setStyleSheet(StyleSheets.get_checkbox_style())
        self.auto_save.stateChanged.connect(
            lambda state: self.emit_setting_changed("auto_save", state)
        )
        self.main_layout.addWidget(self.auto_save)

        # Log Level
        self.add_field_label("Log Level", top_margin=15)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["Debug", "Info", "Warning", "Error", "Critical"])
        self.log_level_combo.setCurrentText("Info")
        self.log_level_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.log_level_combo.setFixedHeight(45)
        self.log_level_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("log_level", value)
        )
        self.main_layout.addWidget(self.log_level_combo)

    def get_settings(self) -> dict:
        """
        Get all current system settings.

        Returns:
            dict: Current system settings
        """
        return {
            "language": self.language_combo.currentText(),
            "theme": self.theme_combo.currentText(),
            "auto_start": self.auto_start.isChecked(),
            "auto_save": self.auto_save.isChecked(),
            "log_level": self.log_level_combo.currentText(),
        }

    def load_settings(self, settings: dict):
        """
        Load system settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        if "language" in settings:
            index = self.language_combo.findText(settings["language"])
            if index >= 0:
                self.language_combo.setCurrentIndex(index)

        if "theme" in settings:
            index = self.theme_combo.findText(settings["theme"])
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)

        if "auto_start" in settings:
            self.auto_start.setChecked(settings["auto_start"])

        if "auto_save" in settings:
            self.auto_save.setChecked(settings["auto_save"])

        if "log_level" in settings:
            index = self.log_level_combo.findText(settings["log_level"])
            if index >= 0:
                self.log_level_combo.setCurrentIndex(index)

