"""Notifications settings section."""

from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit
from gui.styles import StyleSheets
from .base import BaseSettingsSection


class NotificationsSettings(BaseSettingsSection):
    """Notifications configuration section."""

    def __init__(self, parent=None):
        """Initialize notifications settings section."""
        super().__init__("Notifications", parent)
        self._init_notification_controls()

    def _init_notification_controls(self):
        """Initialize all notification control widgets."""
        # Enable Notifications
        self.notifications_enabled = QCheckBox("Enable notifications")
        self.notifications_enabled.setChecked(True)
        self.notifications_enabled.setStyleSheet(StyleSheets.get_checkbox_style())
        self.notifications_enabled.stateChanged.connect(
            lambda state: self.emit_setting_changed("notifications_enabled", state)
        )
        self.main_layout.addWidget(self.notifications_enabled)

        # Sound Alerts
        self.sound_alerts = QCheckBox("Enable sound alerts")
        self.sound_alerts.setChecked(True)
        self.sound_alerts.setStyleSheet(StyleSheets.get_checkbox_style())
        self.sound_alerts.stateChanged.connect(
            lambda state: self.emit_setting_changed("sound_alerts", state)
        )
        self.main_layout.addWidget(self.sound_alerts)

        # Email Notifications
        self.add_field_label("Email Notifications", top_margin=15)

        self.email_enabled = QCheckBox("Enable email notifications")
        self.email_enabled.setChecked(False)
        self.email_enabled.setStyleSheet(StyleSheets.get_checkbox_style())
        self.email_enabled.stateChanged.connect(
            lambda state: self.emit_setting_changed("email_enabled", state)
        )
        self.main_layout.addWidget(self.email_enabled)

        # Email Address
        self.add_field_label("Email Address", top_margin=10)

        self.email_address = QLineEdit()
        self.email_address.setPlaceholderText("Enter email address")
        self.email_address.setStyleSheet(StyleSheets.get_input_style())
        self.email_address.setFixedHeight(45)
        self.email_address.textChanged.connect(
            lambda value: self.emit_setting_changed("email_address", value)
        )
        self.main_layout.addWidget(self.email_address)

        # Notification Priority
        self.add_field_label("Defect Detection Priority", top_margin=15)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["All Defects", "Critical Only", "High & Critical", "Custom"])
        self.priority_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.priority_combo.setFixedHeight(45)
        self.priority_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("notification_priority", value)
        )
        self.main_layout.addWidget(self.priority_combo)

    def get_settings(self) -> dict:
        """
        Get all current notification settings.

        Returns:
            dict: Current notification settings
        """
        return {
            "notifications_enabled": self.notifications_enabled.isChecked(),
            "sound_alerts": self.sound_alerts.isChecked(),
            "email_enabled": self.email_enabled.isChecked(),
            "email_address": self.email_address.text(),
            "notification_priority": self.priority_combo.currentText(),
        }

    def load_settings(self, settings: dict):
        """
        Load notification settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        if "notifications_enabled" in settings:
            self.notifications_enabled.setChecked(settings["notifications_enabled"])

        if "sound_alerts" in settings:
            self.sound_alerts.setChecked(settings["sound_alerts"])

        if "email_enabled" in settings:
            self.email_enabled.setChecked(settings["email_enabled"])

        if "email_address" in settings:
            self.email_address.setText(settings["email_address"])

        if "notification_priority" in settings:
            index = self.priority_combo.findText(settings["notification_priority"])
            if index >= 0:
                self.priority_combo.setCurrentIndex(index)

