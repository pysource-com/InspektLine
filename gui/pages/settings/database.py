"""Database settings section."""

from PySide6.QtWidgets import QCheckBox, QLineEdit, QComboBox, QPushButton
from gui.styles import StyleSheets, DarkTheme
from .base import BaseSettingsSection


class DatabaseSettings(BaseSettingsSection):
    """Database configuration section."""

    def __init__(self, parent=None):
        """Initialize database settings section."""
        super().__init__("Database Configuration", parent)
        self._init_database_controls()

    def _init_database_controls(self):
        """Initialize all database control widgets."""
        # Database Type
        self.add_field_label("Database Type")

        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["SQLite", "PostgreSQL", "MySQL", "MongoDB"])
        self.db_type_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.db_type_combo.setFixedHeight(45)
        self.db_type_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("db_type", value)
        )
        self.main_layout.addWidget(self.db_type_combo)

        # Database Path/Host
        self.add_field_label("Database Path/Host", top_margin=15)

        self.db_host = QLineEdit("localhost")
        self.db_host.setStyleSheet(StyleSheets.get_input_style())
        self.db_host.setFixedHeight(45)
        self.db_host.textChanged.connect(
            lambda value: self.emit_setting_changed("db_host", value)
        )
        self.main_layout.addWidget(self.db_host)

        # Database Port
        self.add_field_label("Port", top_margin=10)

        self.db_port = QLineEdit("5432")
        self.db_port.setStyleSheet(StyleSheets.get_input_style())
        self.db_port.setFixedHeight(45)
        self.db_port.textChanged.connect(
            lambda value: self.emit_setting_changed("db_port", value)
        )
        self.main_layout.addWidget(self.db_port)

        # Auto-backup
        self.auto_backup = QCheckBox("Enable automatic backups")
        self.auto_backup.setChecked(True)
        self.auto_backup.setStyleSheet(StyleSheets.get_checkbox_style())
        self.auto_backup.stateChanged.connect(
            lambda state: self.emit_setting_changed("auto_backup", state)
        )
        self.main_layout.addWidget(self.auto_backup)

        # Backup Interval
        self.add_field_label("Backup Interval", top_margin=15)

        self.backup_interval_combo = QComboBox()
        self.backup_interval_combo.addItems(["Hourly", "Daily", "Weekly", "Monthly"])
        self.backup_interval_combo.setCurrentText("Daily")
        self.backup_interval_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.backup_interval_combo.setFixedHeight(45)
        self.backup_interval_combo.currentTextChanged.connect(
            lambda value: self.emit_setting_changed("backup_interval", value)
        )
        self.main_layout.addWidget(self.backup_interval_combo)

        # Test Connection Button
        self.test_connection_btn = QPushButton("Test Database Connection")
        self.test_connection_btn.setStyleSheet(f"""
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
        self.test_connection_btn.setFixedHeight(45)
        self.test_connection_btn.clicked.connect(self._test_connection)
        self.main_layout.addWidget(self.test_connection_btn)

    def _test_connection(self):
        """Test database connection."""
        # Placeholder for connection test logic
        self.emit_setting_changed("test_connection", True)

    def get_settings(self) -> dict:
        """
        Get all current database settings.

        Returns:
            dict: Current database settings
        """
        return {
            "db_type": self.db_type_combo.currentText(),
            "db_host": self.db_host.text(),
            "db_port": self.db_port.text(),
            "auto_backup": self.auto_backup.isChecked(),
            "backup_interval": self.backup_interval_combo.currentText(),
        }

    def load_settings(self, settings: dict):
        """
        Load database settings from a dictionary.

        Args:
            settings: Settings dictionary
        """
        if "db_type" in settings:
            index = self.db_type_combo.findText(settings["db_type"])
            if index >= 0:
                self.db_type_combo.setCurrentIndex(index)

        if "db_host" in settings:
            self.db_host.setText(settings["db_host"])

        if "db_port" in settings:
            self.db_port.setText(str(settings["db_port"]))

        if "auto_backup" in settings:
            self.auto_backup.setChecked(settings["auto_backup"])

        if "backup_interval" in settings:
            index = self.backup_interval_combo.findText(settings["backup_interval"])
            if index >= 0:
                self.backup_interval_combo.setCurrentIndex(index)

