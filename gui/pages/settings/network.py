"""Network settings section."""

from PySide6.QtWidgets import QCheckBox, QLineEdit, QComboBox
from gui.styles import StyleSheets
from .base import BaseSettingsSection


class NetworkSettings(BaseSettingsSection):
    """Network configuration section."""

    def __init__(self, parent=None):
        """Initialize network settings section."""
        super().__init__("Network Configuration", parent)
        self._init_network_controls()

    def _init_network_controls(self):
        """Initialize all network control widgets."""
        # Enable Remote Access
        self.remote_access = QCheckBox("Enable remote access")
        self.remote_access.setChecked(False)
        self.remote_access.setStyleSheet(StyleSheets.get_checkbox_style())
        self.remote_access.stateChanged.connect(
            lambda state: self.emit_setting_changed("remote_access", state)
        )
        self.main_layout.addWidget(self.remote_access)

        # API Port
        self.add_field_label("API Port", top_margin=15)

        self.api_port = QLineEdit("8080")
        self.api_port.setStyleSheet(StyleSheets.get_input_style())
        self.api_port.setFixedHeight(45)
        self.api_port.textChanged.connect(
            lambda value: self.emit_setting_changed("api_port", value)
        )
        self.main_layout.addWidget(self.api_port)

        # Streaming Port
        self.add_field_label("Streaming Port", top_margin=10)

        self.streaming_port = QLineEdit("8081")
        self.streaming_port.setStyleSheet(StyleSheets.get_input_style())
        self.streaming_port.setFixedHeight(45)
        self.streaming_port.textChanged.connect(
            lambda value: self.emit_setting_changed("streaming_port", value)
        )
        self.main_layout.addWidget(self.streaming_port)

        # Connection Protocol
        self.add_field_label("Connection Protocol", top_margin=15)

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["HTTP", "HTTPS", "WebSocket", "gRPC"])
        self.protocol_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.protocol_combo.setFixedHeight(45)
        self.protocol_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("protocol", value)
        )
        self.main_layout.addWidget(self.protocol_combo)

        # Proxy Settings
        self.use_proxy = QCheckBox("Use proxy server")
        self.use_proxy.setChecked(False)
        self.use_proxy.setStyleSheet(StyleSheets.get_checkbox_style())
        self.use_proxy.stateChanged.connect(
            lambda state: self.emit_setting_changed("use_proxy", state)
        )
        self.main_layout.addWidget(self.use_proxy)

    def get_settings(self) -> dict:
        """
        Get all current network settings.

        Returns:
            dict: Current network settings
        """
        return {
            "remote_access": self.remote_access.isChecked(),
            "api_port": self.api_port.text(),
            "streaming_port": self.streaming_port.text(),
            "protocol": self.protocol_combo.currentText(),
            "use_proxy": self.use_proxy.isChecked(),
        }

    def load_settings(self, settings: dict):
        """
        Load network settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        if "remote_access" in settings:
            self.remote_access.setChecked(settings["remote_access"])

        if "api_port" in settings:
            self.api_port.setText(str(settings["api_port"]))

        if "streaming_port" in settings:
            self.streaming_port.setText(str(settings["streaming_port"]))

        if "protocol" in settings:
            index = self.protocol_combo.findText(settings["protocol"])
            if index >= 0:
                self.protocol_combo.setCurrentIndex(index)

        if "use_proxy" in settings:
            self.use_proxy.setChecked(settings["use_proxy"])

