"""Security settings section."""

from PySide6.QtWidgets import QCheckBox, QLineEdit, QComboBox
from gui.styles import StyleSheets
from .base import BaseSettingsSection


class SecuritySettings(BaseSettingsSection):
    """Security configuration section."""

    def __init__(self, parent=None):
        """Initialize security settings section."""
        super().__init__("Security Settings", parent)
        self._init_security_controls()

    def _init_security_controls(self):
        """Initialize all security control widgets."""
        # Enable Authentication
        self.authentication_enabled = QCheckBox("Enable user authentication")
        self.authentication_enabled.setChecked(True)
        self.authentication_enabled.setStyleSheet(StyleSheets.get_checkbox_style())
        self.authentication_enabled.stateChanged.connect(
            lambda state: self.emit_setting_changed("authentication_enabled", state)
        )
        self.main_layout.addWidget(self.authentication_enabled)

        # Session Timeout
        self.add_field_label("Session Timeout (minutes)", top_margin=15)

        self.session_timeout = QLineEdit("30")
        self.session_timeout.setStyleSheet(StyleSheets.get_input_style())
        self.session_timeout.setFixedHeight(45)
        self.session_timeout.textChanged.connect(
            lambda value: self.emit_setting_changed("session_timeout", value)
        )
        self.main_layout.addWidget(self.session_timeout)

        # Password Policy
        self.add_field_label("Password Policy", top_margin=15)

        self.password_policy_combo = QComboBox()
        self.password_policy_combo.addItems(["Basic", "Medium", "Strong", "Custom"])
        self.password_policy_combo.setCurrentText("Medium")
        self.password_policy_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.password_policy_combo.setFixedHeight(45)
        self.password_policy_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("password_policy", value)
        )
        self.main_layout.addWidget(self.password_policy_combo)

        # Two-Factor Authentication
        self.two_factor_auth = QCheckBox("Enable two-factor authentication (2FA)")
        self.two_factor_auth.setChecked(False)
        self.two_factor_auth.setStyleSheet(StyleSheets.get_checkbox_style())
        self.two_factor_auth.stateChanged.connect(
            lambda state: self.emit_setting_changed("two_factor_auth", state)
        )
        self.main_layout.addWidget(self.two_factor_auth)

        # Encryption
        self.data_encryption = QCheckBox("Enable data encryption at rest")
        self.data_encryption.setChecked(True)
        self.data_encryption.setStyleSheet(StyleSheets.get_checkbox_style())
        self.data_encryption.stateChanged.connect(
            lambda state: self.emit_setting_changed("data_encryption", state)
        )
        self.main_layout.addWidget(self.data_encryption)

        # Audit Log
        self.audit_logging = QCheckBox("Enable audit logging")
        self.audit_logging.setChecked(True)
        self.audit_logging.setStyleSheet(StyleSheets.get_checkbox_style())
        self.audit_logging.stateChanged.connect(
            lambda state: self.emit_setting_changed("audit_logging", state)
        )
        self.main_layout.addWidget(self.audit_logging)

    def get_settings(self) -> dict:
        """
        Get all current security settings.

        Returns:
            dict: Current security settings
        """
        return {
            "authentication_enabled": self.authentication_enabled.isChecked(),
            "session_timeout": self.session_timeout.text(),
            "password_policy": self.password_policy_combo.currentText(),
            "two_factor_auth": self.two_factor_auth.isChecked(),
            "data_encryption": self.data_encryption.isChecked(),
            "audit_logging": self.audit_logging.isChecked(),
        }

    def load_settings(self, settings: dict):
        """
        Load security settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        if "authentication_enabled" in settings:
            self.authentication_enabled.setChecked(settings["authentication_enabled"])

        if "session_timeout" in settings:
            self.session_timeout.setText(str(settings["session_timeout"]))

        if "password_policy" in settings:
            index = self.password_policy_combo.findText(settings["password_policy"])
            if index >= 0:
                self.password_policy_combo.setCurrentIndex(index)

        if "two_factor_auth" in settings:
            self.two_factor_auth.setChecked(settings["two_factor_auth"])

        if "data_encryption" in settings:
            self.data_encryption.setChecked(settings["data_encryption"])

        if "audit_logging" in settings:
            self.audit_logging.setChecked(settings["audit_logging"])

