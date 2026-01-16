"""Stylesheet definitions for UI components."""

from .themes import DarkTheme


class StyleSheets:
    """Collection of reusable stylesheets."""

    @staticmethod
    def get_icon_button_style():
        """Get stylesheet for icon buttons."""
        return f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_SECONDARY};
                border: none;
                border-radius: 6px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
                color: {DarkTheme.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {DarkTheme.BG_PRESSED};
            }}
        """

    @staticmethod
    def get_slider_style():
        """Get stylesheet for sliders."""
        return f"""
            QSlider::groove:horizontal {{
                background: {DarkTheme.BG_HOVER};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {DarkTheme.ACCENT_PURPLE};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {DarkTheme.ACCENT_PURPLE_HOVER};
            }}
        """

    @staticmethod
    def get_combobox_style():
        """Get stylesheet for combo boxes."""
        return f"""
            QComboBox {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
            }}
            QComboBox:hover {{
                border: 1px solid {DarkTheme.BG_HOVER};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {DarkTheme.TEXT_SECONDARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                selection-background-color: {DarkTheme.PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 5px;
            }}
        """

    @staticmethod
    def get_checkbox_style():
        """Get stylesheet for checkboxes."""
        return f"""
            QCheckBox {{
                color: {DarkTheme.TEXT_PRIMARY};
                font-size: 14px;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {DarkTheme.BG_HOVER};
                background-color: {DarkTheme.BG_INPUT};
            }}
            QCheckBox::indicator:checked {{
                background-color: {DarkTheme.ACCENT_PURPLE};
                border: 2px solid {DarkTheme.ACCENT_PURPLE};
                image: none;
            }}
        """

    @staticmethod
    def get_input_style():
        """Get stylesheet for text input fields."""
        return f"""
            QLineEdit {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {DarkTheme.PRIMARY};
            }}
        """

