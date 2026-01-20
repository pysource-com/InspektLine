"""Settings page with modular architecture."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QScrollArea, QFrame, QStackedWidget)
from PySide6.QtCore import Qt
from gui.styles import DarkTheme
from gui.pages.settings import (
    CameraSettings, DetectionSettings, NotificationsSettings,
    SystemSettings, NetworkSettings, DatabaseSettings,
    SecuritySettings, UserSettings
)


class SettingsPage(QWidget):
    """Settings configuration page with modular sections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # Store references to setting sections
        self.sections = {}
        self.current_section = "camera"

        # Menu buttons reference
        self.menu_buttons = {}

        self.init_ui()

    def init_ui(self):
        """Initialize the settings page UI."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left menu
        left_menu = self.create_settings_menu()
        main_layout.addWidget(left_menu)

        # Right content with stacked widget for different sections
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {DarkTheme.BG_PRIMARY};
                border: none;
            }}
        """)

        # Create all setting sections
        self.create_all_sections()

        main_layout.addWidget(self.content_stack, stretch=1)

    def create_settings_menu(self):
        """Create the left settings menu."""
        menu = QFrame()
        menu.setFixedWidth(280)
        menu.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-right: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)

        menu_layout = QVBoxLayout(menu)
        menu_layout.setContentsMargins(15, 20, 15, 20)
        menu_layout.setSpacing(5)

        # Menu items configuration
        menu_items = [
            ("📷", "Camera", "camera", True),
            ("🔍", "Detection", "detection", False),
            ("🔔", "Notifications", "notifications", False),
            ("💻", "System", "system", False),
            ("📡", "Network", "network", False),
            ("💾", "Database", "database", False),
            ("🔒", "Security", "security", False),
            ("👤", "User", "user", False)
        ]

        for icon, text, section_id, is_active in menu_items:
            btn = self.create_menu_button(icon, text, section_id, is_active)
            self.menu_buttons[section_id] = btn
            menu_layout.addWidget(btn)

        menu_layout.addStretch()

        return menu

    def create_menu_button(self, icon, text, section_id, is_active=False):
        """Create a settings menu button."""
        btn = QPushButton(f"{icon}  {text}")
        btn.setFixedHeight(45)
        btn.setCheckable(True)
        btn.setChecked(is_active)

        self._update_button_style(btn, is_active)

        # Connect to section switcher
        btn.clicked.connect(lambda: self.switch_section(section_id))

        return btn

    def _update_button_style(self, btn, is_active):
        """Update button style based on active state."""
        bg_color = DarkTheme.PRIMARY if is_active else "transparent"
        hover_color = DarkTheme.PRIMARY_HOVER if is_active else DarkTheme.BG_INPUT
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {DarkTheme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 15px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)

    def switch_section(self, section_id):
        """
        Switch to a different settings section.

        Args:
            section_id: ID of the section to display
        """
        # Update active button
        for btn_id, btn in self.menu_buttons.items():
            is_active = btn_id == section_id
            btn.setChecked(is_active)
            self._update_button_style(btn, is_active)

        # Switch content
        if section_id in self.sections:
            self.content_stack.setCurrentWidget(self.sections[section_id])
            self.current_section = section_id

    def create_all_sections(self):
        """Create all settings sections."""
        sections_config = [
            ("camera", "Camera", CameraSettings),
            ("detection", "Detection Parameters", DetectionSettings),
            ("notifications", "Notifications", NotificationsSettings),
            ("system", "System", SystemSettings),
            ("network", "Network", NetworkSettings),
            ("database", "Database", DatabaseSettings),
            ("security", "Security", SecuritySettings),
            ("user", "User Profile", UserSettings),
        ]

        for section_id, title, section_class in sections_config:
            page = self.create_section_page(section_id, title, section_class)
            self.sections[section_id] = page
            self.content_stack.addWidget(page)

    def create_section_page(self, section_id, title, section_class):
        """
        Create a section page with scroll area.

        Args:
            section_id: Section identifier
            title: Section title
            section_class: Class to instantiate for the section

        Returns:
            QWidget: The section page
        """
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {DarkTheme.BG_PRIMARY};
                border: none;
            }}
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(30)

        # Title
        page_title = QLabel(title)
        page_title.setStyleSheet("font-size: 32px; font-weight: bold; color: #fff;")
        content_layout.addWidget(page_title)

        # Subtitle
        subtitle = QLabel(f"Configure {title.lower()} settings")
        subtitle.setStyleSheet(
            f"font-size: 14px; color: {DarkTheme.TEXT_SECONDARY}; margin-bottom: 20px;"
        )
        content_layout.addWidget(subtitle)

        # Section content
        section_widget = section_class(self.parent_window)
        content_layout.addWidget(section_widget)

        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        return scroll_area

    # Legacy compatibility methods for backward compatibility with existing code
    @property
    def camera_type_combo(self):
        """Get camera type combo box."""
        return self.sections.get("camera").widget().findChild(CameraSettings).camera_type_combo if "camera" in self.sections else None

    @property
    def camera_device_combo(self):
        """Get camera device combo box."""
        return self.sections.get("camera").widget().findChild(CameraSettings).camera_device_combo if "camera" in self.sections else None

    @property
    def resolution_combo(self):
        """Get resolution combo box."""
        return self.sections.get("camera").widget().findChild(CameraSettings).resolution_combo if "camera" in self.sections else None

    @property
    def fps_combo(self):
        """Get FPS combo box."""
        return self.sections.get("camera").widget().findChild(CameraSettings).fps_combo if "camera" in self.sections else None

    @property
    def autofocus_checkbox(self):
        """Get autofocus checkbox."""
        return self.sections.get("camera").widget().findChild(CameraSettings).autofocus_checkbox if "camera" in self.sections else None

    @property
    def manual_focus_slider(self):
        """Get manual focus slider."""
        return self.sections.get("camera").widget().findChild(CameraSettings).manual_focus_slider if "camera" in self.sections else None

    @property
    def focus_value_label(self):
        """Get focus value label."""
        return self.sections.get("camera").widget().findChild(CameraSettings).focus_value_label if "camera" in self.sections else None

    @property
    def confidence_input(self):
        """Get confidence input."""
        return self.sections.get("detection").widget().findChild(DetectionSettings).confidence_input if "detection" in self.sections else None

    @property
    def defect_size_input(self):
        """Get defect size input."""
        return self.sections.get("detection").widget().findChild(DetectionSettings).defect_size_input if "detection" in self.sections else None

    def get_all_settings(self) -> dict:
        """
        Get all settings from all sections.

        Returns:
            dict: All settings organized by section
        """
        all_settings = {}
        for section_id, section_widget in self.sections.items():
            settings_widget = section_widget.widget().findChildren(QWidget)[0]
            if hasattr(settings_widget, 'get_settings'):
                all_settings[section_id] = settings_widget.get_settings()
        return all_settings

    def load_all_settings(self, settings: dict):
        """
        Load settings into all sections.

        Args:
            settings: Dictionary of settings organized by section
        """
        for section_id, section_settings in settings.items():
            if section_id in self.sections:
                section_widget = self.sections[section_id].widget().findChildren(QWidget)[0]
                if hasattr(section_widget, 'load_settings'):
                    section_widget.load_settings(section_settings)

