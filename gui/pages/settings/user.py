"""User settings section."""

from PySide6.QtWidgets import QLineEdit, QComboBox, QPushButton, QLabel
from gui.styles import StyleSheets, DarkTheme
from .base import BaseSettingsSection


class UserSettings(BaseSettingsSection):
    """User profile configuration section."""

    def __init__(self, parent=None):
        """Initialize user settings section."""
        super().__init__("User Profile", parent)
        self._init_user_controls()

    def _init_user_controls(self):
        """Initialize all user control widgets."""
        # Username
        self.add_field_label("Username")

        self.username = QLineEdit("admin")
        self.username.setStyleSheet(StyleSheets.get_input_style())
        self.username.setFixedHeight(45)
        self.username.textChanged.connect(
            lambda value: self.emit_setting_changed("username", value)
        )
        self.main_layout.addWidget(self.username)

        # Full Name
        self.add_field_label("Full Name", top_margin=10)

        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Enter full name")
        self.full_name.setStyleSheet(StyleSheets.get_input_style())
        self.full_name.setFixedHeight(45)
        self.full_name.textChanged.connect(
            lambda value: self.emit_setting_changed("full_name", value)
        )
        self.main_layout.addWidget(self.full_name)

        # Email
        self.add_field_label("Email", top_margin=10)

        self.email = QLineEdit()
        self.email.setPlaceholderText("user@example.com")
        self.email.setStyleSheet(StyleSheets.get_input_style())
        self.email.setFixedHeight(45)
        self.email.textChanged.connect(
            lambda value: self.emit_setting_changed("user_email", value)
        )
        self.main_layout.addWidget(self.email)

        # Role
        self.add_field_label("Role", top_margin=15)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Administrator", "Operator", "Supervisor", "Viewer"])
        self.role_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.role_combo.setFixedHeight(45)
        self.role_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("user_role", value)
        )
        self.main_layout.addWidget(self.role_combo)

        # Change Password Section
        password_label = QLabel("Change Password")
        password_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #fff; margin-top: 20px;"
        )
        self.main_layout.addWidget(password_label)

        # Current Password
        self.add_field_label("Current Password", top_margin=10)

        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password.setPlaceholderText("Enter current password")
        self.current_password.setStyleSheet(StyleSheets.get_input_style())
        self.current_password.setFixedHeight(45)
        self.main_layout.addWidget(self.current_password)

        # New Password
        self.add_field_label("New Password", top_margin=10)

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText("Enter new password")
        self.new_password.setStyleSheet(StyleSheets.get_input_style())
        self.new_password.setFixedHeight(45)
        self.main_layout.addWidget(self.new_password)

        # Confirm Password
        self.add_field_label("Confirm Password", top_margin=10)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setPlaceholderText("Confirm new password")
        self.confirm_password.setStyleSheet(StyleSheets.get_input_style())
        self.confirm_password.setFixedHeight(45)
        self.main_layout.addWidget(self.confirm_password)

        # Update Password Button
        self.update_password_btn = QPushButton("Update Password")
        self.update_password_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
        """)
        self.update_password_btn.setFixedHeight(45)
        self.update_password_btn.clicked.connect(self._update_password)
        self.main_layout.addWidget(self.update_password_btn)

    def _update_password(self):
        """Handle password update."""
        # Placeholder for password update logic
        if self.new_password.text() == self.confirm_password.text():
            self.emit_setting_changed("password_update", {
                "current": self.current_password.text(),
                "new": self.new_password.text()
            })
            # Clear password fields
            self.current_password.clear()
            self.new_password.clear()
            self.confirm_password.clear()

    def get_settings(self) -> dict:
        """
        Get all current user settings.

        Returns:
            dict: Current user settings
        """
        return {
            "username": self.username.text(),
            "full_name": self.full_name.text(),
            "user_email": self.email.text(),
            "user_role": self.role_combo.currentText(),
        }

    def load_settings(self, settings: dict):
        """
        Load user settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        if "username" in settings:
            self.username.setText(settings["username"])

        if "full_name" in settings:
            self.full_name.setText(settings["full_name"])

        if "user_email" in settings:
            self.email.setText(settings["user_email"])

        if "user_role" in settings:
            index = self.role_combo.findText(settings["user_role"])
            if index >= 0:
                self.role_combo.setCurrentIndex(index)

