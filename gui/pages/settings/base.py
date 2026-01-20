"""Base class for settings sections."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal
from gui.styles import DarkTheme


class BaseSettingsSection(QWidget):
    """Base class for all settings sections with common functionality."""

    # Signals for settings changes
    settings_changed = Signal(str, object)  # (setting_name, value)

    def __init__(self, title: str, parent=None):
        """
        Initialize the base settings section.

        Args:
            title: Section title
            parent: Parent widget
        """
        super().__init__(parent)
        self.section_title = title
        self.parent_window = parent
        self._setup_section_ui()

    def _setup_section_ui(self):
        """Setup the section container with consistent styling."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(20)

        # Add section title
        title = QLabel(self.section_title)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        self.main_layout.addWidget(title)

    def add_field_label(self, text: str, top_margin: int = 0) -> QLabel:
        """
        Add a field label with consistent styling.

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
        self.main_layout.addWidget(label)
        return label

    def emit_setting_changed(self, setting_name: str, value):
        """
        Emit a signal when a setting changes.

        Args:
            setting_name: Name of the setting
            value: New value
        """
        self.settings_changed.emit(setting_name, value)

        # Also call parent window handler if available
        handler_name = f"on_{setting_name}_changed"
        if self.parent_window and hasattr(self.parent_window, handler_name):
            handler = getattr(self.parent_window, handler_name)
            handler(value)

    def get_settings(self) -> dict:
        """
        Get all current settings as a dictionary.

        Returns:
            dict: Current settings
        """
        raise NotImplementedError("Subclasses must implement get_settings()")

    def load_settings(self, settings: dict):
        """
        Load settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        raise NotImplementedError("Subclasses must implement load_settings()")

