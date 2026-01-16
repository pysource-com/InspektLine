"""Sidebar button component."""

from PySide6.QtWidgets import QPushButton
from gui.styles import DarkTheme


class SidebarButton(QPushButton):
    """Custom sidebar button with icon."""

    def __init__(self, icon_text, parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_DISABLED};
                border: none;
                border-radius: 8px;
                font-size: 24px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
                color: {DarkTheme.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {DarkTheme.PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {DarkTheme.PRIMARY};
                color: {DarkTheme.TEXT_PRIMARY};
            }}
        """)
        self.setCheckable(True)

