"""Settings page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QComboBox, QCheckBox, QLineEdit,
                                QSlider, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from gui.styles import StyleSheets, DarkTheme


class SettingsPage(QWidget):
    """Settings configuration page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # Initialize UI elements
        self.camera_type_combo = None
        self.camera_device_combo = None
        self.resolution_combo = None
        self.fps_combo = None
        self.autofocus_checkbox = None
        self.stabilization_checkbox = None
        self.confidence_input = None
        self.defect_size_input = None

        self.init_ui()

    def init_ui(self):
        """Initialize the settings page UI."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left menu
        left_menu = self.create_settings_menu()
        main_layout.addWidget(left_menu)

        # Right content
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
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #fff;")
        content_layout.addWidget(title)

        subtitle = QLabel("Configure system preferences and parameters")
        subtitle.setStyleSheet(f"font-size: 14px; color: {DarkTheme.TEXT_SECONDARY}; margin-bottom: 20px;")
        content_layout.addWidget(subtitle)

        # Camera Configuration
        camera_config = self.create_camera_config_section()
        content_layout.addWidget(camera_config)

        # Detection Parameters
        detection_params = self.create_detection_params_section()
        content_layout.addWidget(detection_params)

        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area, stretch=1)

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

        # Menu items
        menu_items = [
            ("📷", "Camera", True),
            ("🔔", "Notifications", False),
            ("💻", "System", False),
            ("📡", "Network", False),
            ("💾", "Database", False),
            ("🔒", "Security", False),
            ("👤", "User", False)
        ]

        for icon, text, is_active in menu_items:
            btn = self.create_menu_button(icon, text, is_active)
            menu_layout.addWidget(btn)

        menu_layout.addStretch()

        return menu

    def create_menu_button(self, icon, text, is_active=False):
        """Create a settings menu button."""
        btn = QPushButton(f"{icon}  {text}")
        btn.setFixedHeight(45)
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
        return btn

    def create_camera_config_section(self):
        """Create the Camera Configuration section."""
        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Title
        title = QLabel("Camera Configuration")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        # Camera Type
        camera_type_label = QLabel("Camera Type")
        camera_type_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(camera_type_label)

        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems(["USB Webcam", "Intel RealSense"])
        self.camera_type_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_type_combo.setFixedHeight(45)
        if self.parent_window:
            self.camera_type_combo.currentTextChanged.connect(self.parent_window.on_camera_type_changed)
        layout.addWidget(self.camera_type_combo)

        # Camera Device
        camera_device_label = QLabel("Camera Device")
        camera_device_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px; margin-top: 10px;")
        layout.addWidget(camera_device_label)

        self.camera_device_combo = QComboBox()
        self.camera_device_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_device_combo.setFixedHeight(45)
        if self.parent_window:
            self.camera_device_combo.currentIndexChanged.connect(self.parent_window.on_camera_device_changed)
        layout.addWidget(self.camera_device_combo)

        # Resolution and Frame Rate
        res_fps_layout = QHBoxLayout()
        res_fps_layout.setSpacing(20)

        # Resolution
        res_group = QVBoxLayout()
        res_label = QLabel("Resolution")
        res_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px;")
        res_group.addWidget(res_label)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920 x 1080 (Full HD)",
            "1280 x 720 (HD)",
            "640 x 480 (VGA)"
        ])
        self.resolution_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.resolution_combo.setFixedHeight(45)
        res_group.addWidget(self.resolution_combo)
        res_fps_layout.addLayout(res_group, stretch=1)

        # Frame Rate
        fps_group = QVBoxLayout()
        fps_label = QLabel("Frame Rate")
        fps_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px;")
        fps_group.addWidget(fps_label)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS", "30 FPS", "15 FPS"])
        self.fps_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.fps_combo.setFixedHeight(45)
        fps_group.addWidget(self.fps_combo)
        res_fps_layout.addLayout(fps_group, stretch=1)

        layout.addLayout(res_fps_layout)

        # Sliders
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(20)

        exposure_group = self.create_slider_group("Exposure", 50)
        sliders_layout.addLayout(exposure_group, stretch=1)

        brightness_group = self.create_slider_group("Brightness", 50)
        sliders_layout.addLayout(brightness_group, stretch=1)

        layout.addLayout(sliders_layout)

        sliders_layout2 = QHBoxLayout()
        sliders_layout2.setSpacing(20)

        contrast_group = self.create_slider_group("Contrast", 75)
        sliders_layout2.addLayout(contrast_group, stretch=1)

        saturation_group = self.create_slider_group("Saturation", 50)
        sliders_layout2.addLayout(saturation_group, stretch=1)

        layout.addLayout(sliders_layout2)

        # Checkboxes
        self.autofocus_checkbox = QCheckBox("Enable auto-focus")
        self.autofocus_checkbox.setChecked(True)
        self.autofocus_checkbox.setStyleSheet(StyleSheets.get_checkbox_style())
        layout.addWidget(self.autofocus_checkbox)

        self.stabilization_checkbox = QCheckBox("Enable image stabilization")
        self.stabilization_checkbox.setChecked(True)
        self.stabilization_checkbox.setStyleSheet(StyleSheets.get_checkbox_style())
        layout.addWidget(self.stabilization_checkbox)

        return section

    def create_detection_params_section(self):
        """Create the Detection Parameters section."""
        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Title
        title = QLabel("Detection Parameters")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        # Confidence Threshold
        conf_label = QLabel("Confidence Threshold (%)")
        conf_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(conf_label)

        self.confidence_input = QLineEdit("85")
        self.confidence_input.setStyleSheet(StyleSheets.get_input_style())
        self.confidence_input.setFixedHeight(50)
        layout.addWidget(self.confidence_input)

        # Minimum Defect Size
        defect_label = QLabel("Minimum Defect Size (px)")
        defect_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px; margin-top: 10px;")
        layout.addWidget(defect_label)

        self.defect_size_input = QLineEdit("10")
        self.defect_size_input.setStyleSheet(StyleSheets.get_input_style())
        self.defect_size_input.setFixedHeight(50)
        layout.addWidget(self.defect_size_input)

        return section

    def create_slider_group(self, label_text, value):
        """Create a slider group."""
        group = QVBoxLayout()

        label = QLabel(label_text)
        label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 8px;")
        group.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(value)
        slider.setStyleSheet(StyleSheets.get_slider_style())
        group.addWidget(slider)

        return group

