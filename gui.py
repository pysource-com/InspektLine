import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QSlider, QFrame, QComboBox, QCheckBox,
                                QLineEdit, QScrollArea, QStackedWidget)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from camera.camera import Camera


class SidebarButton(QPushButton):
    """Custom sidebar button with icon."""

    def __init__(self, icon_text, parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #666;
                border: none;
                border-radius: 8px;
                font-size: 24px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #0066ff;
            }
            QPushButton:checked {
                background-color: #0066ff;
                color: #fff;
            }
        """)
        self.setCheckable(True)


class VideoDisplayWidget(QMainWindow):
    """Main application window with left sidebar and camera feed."""

    def __init__(self, camera_index=0, camera_type="usb-standard"):
        """
        Initialize the video display widget.

        Args:
            camera_index: Camera index (0 for default camera)
            camera_type: Type of camera ("usb-standard" or "intel-realsense")
        """
        super().__init__()
        self.camera_index = camera_index
        self.camera_type = camera_type
        self.camera = Camera()
        self.cap = None
        self.timer = None
        self.is_inspecting = False
        self.exposure_value = 50
        self.contrast_value = 75
        self.current_page = "camera"  # Track current page

        # Settings values
        self.brightness_value = 50
        self.saturation_value = 50
        self.confidence_threshold = 85
        self.min_defect_size = 10
        self.auto_focus_enabled = True
        self.stabilization_enabled = True
        self.resolution = "1920 x 1080 (Full HD)"
        self.frame_rate = "30 FPS"

        # Dataset collection values
        self.is_capturing = False
        self.total_samples = 0
        self.ok_samples = 0
        self.not_ok_samples = 0
        self.session_start_time = None
        self.selected_defect_category = "Surface Defect"
        self.recent_samples = []

        self.init_ui()
        self.start_video()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("InspektLine")
        self.setGeometry(100, 100, 1280, 800)

        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
            }
            QWidget {
                background-color: #0a0a0a;
                color: #ffffff;
            }
        """)

        # Create central widget with horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create left sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # Create stacked widget for different pages
        self.stacked_widget = QStackedWidget()

        # Create camera feed page
        camera_page = self.create_camera_page()
        self.stacked_widget.addWidget(camera_page)

        # Create dataset collection page
        dataset_page = self.create_dataset_collection_page()
        self.stacked_widget.addWidget(dataset_page)

        # Create settings page
        settings_page = self.create_settings_page()
        self.stacked_widget.addWidget(settings_page)

        main_layout.addWidget(self.stacked_widget, stretch=1)

    def create_camera_page(self):
        """Create the main camera feed page."""
        # Create main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Create header with title and controls
        header_layout = QHBoxLayout()

        # Camera feed title with LIVE badge
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        camera_icon = QLabel("📹")
        camera_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(camera_icon)

        title_label = QLabel("Camera Feed")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        title_layout.addWidget(title_label)

        live_badge = QLabel("LIVE")
        live_badge.setStyleSheet("""
            background-color: #00cc00;
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        """)
        title_layout.addWidget(live_badge)
        title_layout.addStretch()

        header_layout.addWidget(title_widget)
        header_layout.addStretch()

        # Camera control buttons
        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.setSpacing(10)

        zoom_in_btn = QPushButton("🔍")
        zoom_in_btn.setFixedSize(40, 40)
        zoom_in_btn.setStyleSheet(self.get_icon_button_style())
        control_buttons_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("🔎")
        zoom_out_btn.setFixedSize(40, 40)
        zoom_out_btn.setStyleSheet(self.get_icon_button_style())
        control_buttons_layout.addWidget(zoom_out_btn)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet(self.get_icon_button_style())
        refresh_btn.clicked.connect(self.refresh_camera)
        control_buttons_layout.addWidget(refresh_btn)

        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setFixedSize(40, 40)
        fullscreen_btn.setStyleSheet(self.get_icon_button_style())
        control_buttons_layout.addWidget(fullscreen_btn)

        header_layout.addLayout(control_buttons_layout)
        content_layout.addLayout(header_layout)

        # Create video display frame with corner brackets
        video_container = QWidget()
        video_container.setStyleSheet("""
            QWidget {
                background-color: #0f0f0f;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
            }
        """)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(10, 10, 10, 10)

        # Create label to display video frames
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000; border: none;")
        self.video_label.setMinimumSize(800, 480)
        video_layout.addWidget(self.video_label)

        content_layout.addWidget(video_container, stretch=1)

        # Bottom control panel
        bottom_panel = self.create_bottom_panel()
        content_layout.addWidget(bottom_panel)

        return content_widget

    def create_dataset_collection_page(self):
        """Create the dataset collection page."""
        main_widget = QWidget()
        main_outer_layout = QVBoxLayout(main_widget)
        main_outer_layout.setContentsMargins(20, 20, 20, 20)
        main_outer_layout.setSpacing(20)

        # Top header with title and buttons
        top_header = QHBoxLayout()

        page_title = QLabel("Dataset Collection")
        page_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #fff;")
        top_header.addWidget(page_title)

        top_header.addStretch()

        # Shortcuts button
        shortcuts_btn = QPushButton("⌨ Shortcuts (?)")
        shortcuts_btn.setFixedHeight(40)
        shortcuts_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        top_header.addWidget(shortcuts_btn)

        # Export Dataset button
        export_btn = QPushButton("⬇ Export Dataset")
        export_btn.setFixedHeight(40)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066ff;
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052cc;
            }
        """)
        top_header.addWidget(export_btn)

        main_outer_layout.addLayout(top_header)

        # Main content layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # Left panel - Statistics and Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)


        subtitle_label = QLabel("Label images for training data")
        subtitle_label.setStyleSheet("font-size: 14px; color: #999;")
        left_layout.addWidget(subtitle_label)

        # Session Statistics section
        stats_widget = self.create_session_statistics_widget()
        left_layout.addWidget(stats_widget)

        # Defect Category section
        defect_widget = self.create_defect_category_widget()
        left_layout.addWidget(defect_widget)

        # Recent Samples section
        recent_widget = self.create_recent_samples_widget()
        left_layout.addWidget(recent_widget)

        left_layout.addStretch()

        left_panel.setFixedWidth(400)
        main_layout.addWidget(left_panel)

        # Center/Right panel - Live Feed and Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)

        # Live Feed header
        feed_header = QHBoxLayout()

        feed_title_widget = QWidget()
        feed_title_layout = QHBoxLayout(feed_title_widget)
        feed_title_layout.setContentsMargins(0, 0, 0, 0)
        feed_title_layout.setSpacing(10)

        camera_icon = QLabel("📹")
        camera_icon.setStyleSheet("font-size: 24px;")
        feed_title_layout.addWidget(camera_icon)

        feed_label = QLabel("Live Feed")
        feed_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        feed_title_layout.addWidget(feed_label)

        # CAPTURING badge
        self.capturing_badge = QLabel("CAPTURING")
        self.capturing_badge.setStyleSheet("""
            background-color: #00cc00;
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        """)
        self.capturing_badge.setVisible(False)
        feed_title_layout.addWidget(self.capturing_badge)
        feed_title_layout.addStretch()

        feed_header.addWidget(feed_title_widget)
        feed_header.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet(self.get_icon_button_style())
        refresh_btn.clicked.connect(self.refresh_camera)
        feed_header.addWidget(refresh_btn)

        right_layout.addLayout(feed_header)

        # Live feed video display
        video_container = QWidget()
        video_container.setStyleSheet("""
            QWidget {
                background-color: #0f0f0f;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
            }
        """)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(10, 10, 10, 10)

        # Use the same video label from camera page
        self.dataset_video_label = QLabel()
        self.dataset_video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dataset_video_label.setStyleSheet("background-color: #000000; border: none;")
        self.dataset_video_label.setMinimumSize(800, 480)


        video_layout.addWidget(self.dataset_video_label)
        right_layout.addWidget(video_container, stretch=1)

        # Bottom buttons - OK and NOT OK
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # OK button
        self.ok_button = QPushButton("✓\nOK\nPress → or Enter")
        self.ok_button.setFixedHeight(120)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #00cc00;
                color: #000;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ff00;
            }
            QPushButton:pressed {
                background-color: #009900;
            }
            QPushButton:disabled {
                background-color: #004400;
                color: #666;
            }
        """)
        self.ok_button.clicked.connect(lambda: self.capture_sample("OK"))
        self.ok_button.setEnabled(False)
        buttons_layout.addWidget(self.ok_button, stretch=1)

        # NOT OK button
        self.not_ok_button = QPushButton("✕\nNOT OK\nPress ← or Backspace")
        self.not_ok_button.setFixedHeight(120)
        self.not_ok_button.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: #fff;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff3333;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }
            QPushButton:disabled {
                background-color: #440000;
                color: #666;
            }
        """)
        self.not_ok_button.clicked.connect(lambda: self.capture_sample("NOT_OK"))
        self.not_ok_button.setEnabled(False)
        buttons_layout.addWidget(self.not_ok_button, stretch=1)

        right_layout.addLayout(buttons_layout)

        main_layout.addWidget(right_panel, stretch=1)

        # Gallery panel on far right
        gallery_panel = self.create_collection_gallery_widget()
        gallery_panel.setFixedWidth(300)
        main_layout.addWidget(gallery_panel)

        # Add main content to outer layout
        main_outer_layout.addLayout(main_layout)

        return main_widget

    def create_session_statistics_widget(self):
        """Create session statistics widget."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Session Statistics")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        # Total Samples
        total_layout = QHBoxLayout()
        total_label = QLabel("Total Samples")
        total_label.setStyleSheet("color: #999; font-size: 14px;")
        total_layout.addWidget(total_label)
        total_layout.addStretch()
        self.total_samples_label = QLabel("0")
        self.total_samples_label.setStyleSheet("color: #fff; font-size: 18px; font-weight: bold;")
        total_layout.addWidget(self.total_samples_label)
        layout.addLayout(total_layout)

        # OK Samples
        ok_layout = QHBoxLayout()
        ok_label = QLabel("OK Samples")
        ok_label.setStyleSheet("color: #00cc00; font-size: 14px;")
        ok_layout.addWidget(ok_label)
        ok_layout.addStretch()
        self.ok_samples_label = QLabel("0")
        self.ok_samples_label.setStyleSheet("color: #00cc00; font-size: 18px; font-weight: bold;")
        ok_layout.addWidget(self.ok_samples_label)
        layout.addLayout(ok_layout)

        # NOT OK Samples
        not_ok_layout = QHBoxLayout()
        not_ok_label = QLabel("NOT OK Samples")
        not_ok_label.setStyleSheet("color: #ff0000; font-size: 14px;")
        not_ok_layout.addWidget(not_ok_label)
        not_ok_layout.addStretch()
        self.not_ok_samples_label = QLabel("0")
        self.not_ok_samples_label.setStyleSheet("color: #ff0000; font-size: 18px; font-weight: bold;")
        not_ok_layout.addWidget(self.not_ok_samples_label)
        layout.addLayout(not_ok_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #2a2a2a;")
        layout.addWidget(separator)

        # Session Duration
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Session Duration")
        duration_label.setStyleSheet("color: #999; font-size: 14px;")
        duration_layout.addWidget(duration_label)
        duration_layout.addStretch()
        self.duration_label = QLabel("0 min")
        self.duration_label.setStyleSheet("color: #fff; font-size: 14px;")
        duration_layout.addWidget(self.duration_label)
        layout.addLayout(duration_layout)

        # Rate
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate")
        rate_label.setStyleSheet("color: #999; font-size: 14px;")
        rate_layout.addWidget(rate_label)
        rate_layout.addStretch()
        self.rate_label = QLabel("0 samples/min")
        self.rate_label.setStyleSheet("color: #fff; font-size: 14px;")
        rate_layout.addWidget(self.rate_label)
        layout.addLayout(rate_layout)

        return widget

    def create_defect_category_widget(self):
        """Create defect category selection widget."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Defect Category")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        subtitle = QLabel("Select category before labeling NOT OK samples")
        subtitle.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(subtitle)

        self.defect_category_combo = QComboBox()
        self.defect_category_combo.addItems([
            "Surface Defect",
            "Crack",
            "Scratch",
            "Dent",
            "Discoloration",
            "Missing Part",
            "Contamination"
        ])
        self.defect_category_combo.setCurrentText(self.selected_defect_category)
        self.defect_category_combo.setStyleSheet(self.get_combobox_style())
        self.defect_category_combo.setFixedHeight(45)
        layout.addWidget(self.defect_category_combo)

        return widget

    def create_recent_samples_widget(self):
        """Create recent samples widget."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Recent Samples")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        # Placeholder for recent samples list
        self.recent_samples_list = QLabel("No samples collected yet")
        self.recent_samples_list.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
        self.recent_samples_list.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.recent_samples_list)

        return widget

    def create_collection_gallery_widget(self):
        """Create collection gallery widget."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Collection Gallery")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # OK count badge
        ok_badge = QLabel("OK: 0")
        ok_badge.setStyleSheet("""
            background-color: #00cc00;
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(ok_badge)

        # NG count badge
        ng_badge = QLabel("NG: 0")
        ng_badge.setStyleSheet("""
            background-color: #ff0000;
            color: #fff;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(ng_badge)

        layout.addLayout(header_layout)

        # Gallery content (placeholder)
        gallery_scroll = QScrollArea()
        gallery_scroll.setWidgetResizable(True)
        gallery_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0a0a0a;
                border: none;
                border-radius: 8px;
            }
        """)

        gallery_content = QLabel("Gallery thumbnails\nwill appear here")
        gallery_content.setStyleSheet("color: #666; padding: 40px;")
        gallery_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gallery_scroll.setWidget(gallery_content)

        layout.addWidget(gallery_scroll, stretch=1)

        return widget

    def capture_sample(self, label_type):
        """Capture a sample with the given label."""
        print(f"Capturing sample: {label_type}")

        # Update counters
        self.total_samples += 1
        if label_type == "OK":
            self.ok_samples += 1
        else:
            self.not_ok_samples += 1

        # Update UI
        self.update_dataset_statistics()


        # TODO: Save the actual frame from camera
        # This would integrate with the dataset module
        print(f"Total: {self.total_samples}, OK: {self.ok_samples}, NOT OK: {self.not_ok_samples}")

    def update_dataset_statistics(self):
        """Update dataset statistics labels."""
        self.total_samples_label.setText(str(self.total_samples))
        self.ok_samples_label.setText(str(self.ok_samples))
        self.not_ok_samples_label.setText(str(self.not_ok_samples))

    def create_settings_page(self):
        """Create the settings configuration page."""
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left settings menu
        settings_menu = self.create_settings_menu()
        main_layout.addWidget(settings_menu)

        # Right content area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #0a0a0a;
                border: none;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 5px;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(30)

        # Page title
        title_label = QLabel("Settings")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #fff;")
        content_layout.addWidget(title_label)

        subtitle_label = QLabel("Configure system preferences and parameters")
        subtitle_label.setStyleSheet("font-size: 14px; color: #999; margin-bottom: 20px;")
        content_layout.addWidget(subtitle_label)

        # Camera Configuration section
        camera_config_widget = self.create_camera_config_section()
        content_layout.addWidget(camera_config_widget)

        # Detection Parameters section
        detection_params_widget = self.create_detection_params_section()
        content_layout.addWidget(detection_params_widget)

        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area, stretch=1)

        return main_widget

    def create_settings_menu(self):
        """Create the left settings menu."""
        menu = QFrame()
        menu.setFixedWidth(280)
        menu.setStyleSheet("""
            QFrame {
                background-color: #0f0f0f;
                border-right: 1px solid #1a1a1a;
            }
        """)

        menu_layout = QVBoxLayout(menu)
        menu_layout.setContentsMargins(15, 20, 15, 20)
        menu_layout.setSpacing(5)

        # Create menu buttons
        menu_items = [
            ("📷", "Camera"),
            ("🔔", "Notifications"),
            ("💻", "System"),
            ("📡", "Network"),
            ("💾", "Database"),
            ("🔒", "Security"),
            ("👤", "User")
        ]

        for icon, text in menu_items:
            btn = self.create_settings_menu_button(icon, text, text == "Camera")
            menu_layout.addWidget(btn)

        menu_layout.addStretch()

        return menu

    def create_settings_menu_button(self, icon, text, is_active=False):
        """Create a settings menu button."""
        btn = QPushButton(f"{icon}  {text}")
        btn.setFixedHeight(45)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#0066ff' if is_active else 'transparent'};
                color: #fff;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 15px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {'#0052cc' if is_active else '#1a1a1a'};
            }}
        """)
        return btn

    def create_camera_config_section(self):
        """Create the Camera Configuration section."""
        section = QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 12px;
            }
        """)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(25, 25, 25, 25)
        section_layout.setSpacing(20)

        # Section title
        title = QLabel("Camera Configuration")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        section_layout.addWidget(title)

        # Camera Type selector
        camera_type_label = QLabel("Camera Type")
        camera_type_label.setStyleSheet("color: #999; font-size: 13px; margin-bottom: 8px;")
        section_layout.addWidget(camera_type_label)

        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems([
            "USB Webcam",
            "Intel RealSense"
        ])
        # Set current selection based on camera_type
        if self.camera_type == "intel-realsense":
            self.camera_type_combo.setCurrentText("Intel RealSense")
        else:
            self.camera_type_combo.setCurrentText("USB Webcam")

        self.camera_type_combo.setStyleSheet(self.get_combobox_style())
        self.camera_type_combo.setFixedHeight(45)
        self.camera_type_combo.currentTextChanged.connect(self.on_camera_type_changed)
        section_layout.addWidget(self.camera_type_combo)

        # Camera Device selector (for USB webcams)
        camera_device_label = QLabel("Camera Device")
        camera_device_label.setStyleSheet("color: #999; font-size: 13px; margin-bottom: 8px; margin-top: 10px;")
        section_layout.addWidget(camera_device_label)

        self.camera_device_combo = QComboBox()
        self.populate_camera_devices()
        self.camera_device_combo.setStyleSheet(self.get_combobox_style())
        self.camera_device_combo.setFixedHeight(45)
        self.camera_device_combo.currentIndexChanged.connect(self.on_camera_device_changed)
        section_layout.addWidget(self.camera_device_combo)

        # Resolution and Frame Rate row
        res_fps_layout = QHBoxLayout()
        res_fps_layout.setSpacing(20)

        # Resolution
        res_group = QVBoxLayout()
        res_label = QLabel("Resolution")
        res_label.setStyleSheet("color: #999; font-size: 13px; margin-bottom: 8px;")
        res_group.addWidget(res_label)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920 x 1080 (Full HD)",
            "1280 x 720 (HD)",
            "640 x 480 (VGA)"
        ])
        self.resolution_combo.setCurrentText(self.resolution)
        self.resolution_combo.setStyleSheet(self.get_combobox_style())
        self.resolution_combo.setFixedHeight(45)
        res_group.addWidget(self.resolution_combo)
        res_fps_layout.addLayout(res_group, stretch=1)

        # Frame Rate
        fps_group = QVBoxLayout()
        fps_label = QLabel("Frame Rate")
        fps_label.setStyleSheet("color: #999; font-size: 13px; margin-bottom: 8px;")
        fps_group.addWidget(fps_label)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS", "30 FPS", "15 FPS"])
        self.fps_combo.setCurrentText(self.frame_rate)
        self.fps_combo.setStyleSheet(self.get_combobox_style())
        self.fps_combo.setFixedHeight(45)
        fps_group.addWidget(self.fps_combo)
        res_fps_layout.addLayout(fps_group, stretch=1)

        section_layout.addLayout(res_fps_layout)

        # Exposure and Brightness sliders row
        exp_bright_layout = QHBoxLayout()
        exp_bright_layout.setSpacing(20)

        exposure_group = self.create_slider_group("Exposure", self.exposure_value)
        exp_bright_layout.addLayout(exposure_group, stretch=1)

        brightness_group = self.create_slider_group("Brightness", self.brightness_value)
        exp_bright_layout.addLayout(brightness_group, stretch=1)

        section_layout.addLayout(exp_bright_layout)

        # Contrast and Saturation sliders row
        con_sat_layout = QHBoxLayout()
        con_sat_layout.setSpacing(20)

        contrast_group = self.create_slider_group("Contrast", self.contrast_value)
        con_sat_layout.addLayout(contrast_group, stretch=1)

        saturation_group = self.create_slider_group("Saturation", self.saturation_value)
        con_sat_layout.addLayout(saturation_group, stretch=1)

        section_layout.addLayout(con_sat_layout)

        # Checkboxes
        self.autofocus_checkbox = QCheckBox("Enable auto-focus")
        self.autofocus_checkbox.setChecked(self.auto_focus_enabled)
        self.autofocus_checkbox.setStyleSheet(self.get_checkbox_style())
        section_layout.addWidget(self.autofocus_checkbox)

        self.stabilization_checkbox = QCheckBox("Enable image stabilization")
        self.stabilization_checkbox.setChecked(self.stabilization_enabled)
        self.stabilization_checkbox.setStyleSheet(self.get_checkbox_style())
        section_layout.addWidget(self.stabilization_checkbox)

        return section

    def create_detection_params_section(self):
        """Create the Detection Parameters section."""
        section = QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 12px;
            }
        """)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(25, 25, 25, 25)
        section_layout.setSpacing(20)

        # Section title
        title = QLabel("Detection Parameters")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        section_layout.addWidget(title)

        # Confidence Threshold
        conf_label = QLabel("Confidence Threshold (%)")
        conf_label.setStyleSheet("color: #999; font-size: 13px; margin-bottom: 8px;")
        section_layout.addWidget(conf_label)

        self.confidence_input = QLineEdit(str(self.confidence_threshold))
        self.confidence_input.setStyleSheet(self.get_input_style())
        self.confidence_input.setFixedHeight(50)
        section_layout.addWidget(self.confidence_input)

        # Minimum Defect Size
        defect_label = QLabel("Minimum Defect Size (px)")
        defect_label.setStyleSheet("color: #999; font-size: 13px; margin-bottom: 8px; margin-top: 10px;")
        section_layout.addWidget(defect_label)

        self.defect_size_input = QLineEdit(str(self.min_defect_size))
        self.defect_size_input.setStyleSheet(self.get_input_style())
        self.defect_size_input.setFixedHeight(50)
        section_layout.addWidget(self.defect_size_input)

        return section

    def create_slider_group(self, label_text, value):
        """Create a slider group with label and slider."""
        group = QVBoxLayout()

        label = QLabel(label_text)
        label.setStyleSheet("color: #999; font-size: 13px; margin-bottom: 8px;")
        group.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(value)
        slider.setStyleSheet(self.get_slider_style())
        group.addWidget(slider)

        return group

    def get_combobox_style(self):
        """Get stylesheet for combo boxes."""
        return """
            QComboBox {
                background-color: #1a1a1a;
                color: #fff;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
            }
            QComboBox:hover {
                border: 1px solid #3a3a3a;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #999;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #fff;
                selection-background-color: #0066ff;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                padding: 5px;
            }
        """

    def get_checkbox_style(self):
        """Get stylesheet for checkboxes."""
        return """
            QCheckBox {
                color: #fff;
                font-size: 14px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #3a3a3a;
                background-color: #1a1a1a;
            }
            QCheckBox::indicator:checked {
                background-color: #cc44ff;
                border: 2px solid #cc44ff;
                image: none;
            }
            QCheckBox::indicator:checked:after {
                content: "✓";
            }
        """

    def get_input_style(self):
        """Get stylesheet for text input fields."""
        return """
            QLineEdit {
                background-color: #1a1a1a;
                color: #fff;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #0066ff;
            }
        """

    def create_sidebar(self):
        """Create the left sidebar with navigation buttons."""
        sidebar = QFrame()
        sidebar.setFixedWidth(100)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #0f0f0f;
                border-right: 1px solid #1a1a1a;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        # Store buttons for group management
        self.sidebar_buttons = []

        # Camera button (active by default)
        camera_btn = SidebarButton("📷")
        camera_btn.setChecked(True)
        camera_btn.clicked.connect(lambda: self.switch_page(0, camera_btn))
        sidebar_layout.addWidget(camera_btn)
        self.sidebar_buttons.append(camera_btn)

        # Capture button - Dataset Collection
        capture_btn = SidebarButton("📸")
        capture_btn.clicked.connect(lambda: self.switch_page(1, capture_btn))
        sidebar_layout.addWidget(capture_btn)
        self.sidebar_buttons.append(capture_btn)

        # Database button
        database_btn = SidebarButton("💾")
        database_btn.clicked.connect(lambda: self.switch_page(0, database_btn))
        sidebar_layout.addWidget(database_btn)
        self.sidebar_buttons.append(database_btn)

        # Chart button
        chart_btn = SidebarButton("📊")
        chart_btn.clicked.connect(lambda: self.switch_page(0, chart_btn))
        sidebar_layout.addWidget(chart_btn)
        self.sidebar_buttons.append(chart_btn)

        # Document button
        document_btn = SidebarButton("📄")
        document_btn.clicked.connect(lambda: self.switch_page(0, document_btn))
        sidebar_layout.addWidget(document_btn)
        self.sidebar_buttons.append(document_btn)

        sidebar_layout.addStretch()

        # Settings button at bottom
        settings_btn = SidebarButton("⚙️")
        settings_btn.clicked.connect(lambda: self.switch_page(2, settings_btn))
        sidebar_layout.addWidget(settings_btn)
        self.sidebar_buttons.append(settings_btn)

        # Power button at very bottom
        power_btn = SidebarButton("⏻")
        power_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(power_btn)

        return sidebar

    def switch_page(self, page_index, clicked_button):
        """Switch to a different page in the stacked widget."""
        self.stacked_widget.setCurrentIndex(page_index)

        # Update button states
        for btn in self.sidebar_buttons:
            btn.setChecked(btn == clicked_button)

        # Enable/disable dataset capture buttons based on page
        if page_index == 1:  # Dataset collection page
            self.is_capturing = True
            self.capturing_badge.setVisible(True)
            self.ok_button.setEnabled(True)
            self.not_ok_button.setEnabled(True)
        else:
            self.is_capturing = False
            if hasattr(self, 'capturing_badge'):
                self.capturing_badge.setVisible(False)
            if hasattr(self, 'ok_button'):
                self.ok_button.setEnabled(False)
            if hasattr(self, 'not_ok_button'):
                self.not_ok_button.setEnabled(False)

    def create_bottom_panel(self):
        """Create the bottom control panel with sliders and buttons."""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 8px;
            }
        """)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 15, 20, 15)
        panel_layout.setSpacing(15)

        # Sliders row
        sliders_layout = QHBoxLayout()
        sliders_layout.setSpacing(30)

        # Exposure slider
        exposure_group = QVBoxLayout()
        exposure_label_layout = QHBoxLayout()
        exposure_label = QLabel("Exposure")
        exposure_label.setStyleSheet("color: #999; font-size: 14px;")
        exposure_label_layout.addWidget(exposure_label)
        exposure_auto = QLabel("Auto")
        exposure_auto.setStyleSheet("color: #999; font-size: 14px;")
        exposure_label_layout.addWidget(exposure_auto)
        exposure_label_layout.addStretch()
        exposure_group.addLayout(exposure_label_layout)

        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setMinimum(0)
        self.exposure_slider.setMaximum(100)
        self.exposure_slider.setValue(self.exposure_value)
        self.exposure_slider.setStyleSheet(self.get_slider_style())
        exposure_group.addWidget(self.exposure_slider)
        sliders_layout.addLayout(exposure_group, stretch=1)

        # Contrast slider
        contrast_group = QVBoxLayout()
        contrast_label_layout = QHBoxLayout()
        contrast_label = QLabel("Contrast")
        contrast_label.setStyleSheet("color: #999; font-size: 14px;")
        contrast_label_layout.addWidget(contrast_label)
        contrast_label_layout.addStretch()
        contrast_value_label = QLabel(f"{self.contrast_value}%")
        contrast_value_label.setStyleSheet("color: #999; font-size: 14px;")
        contrast_label_layout.addWidget(contrast_value_label)
        contrast_group.addLayout(contrast_label_layout)

        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(100)
        self.contrast_slider.setValue(self.contrast_value)
        self.contrast_slider.setStyleSheet(self.get_slider_style())
        self.contrast_slider.valueChanged.connect(
            lambda v: contrast_value_label.setText(f"{v}%")
        )
        contrast_group.addWidget(self.contrast_slider)
        sliders_layout.addLayout(contrast_group, stretch=1)

        panel_layout.addLayout(sliders_layout)

        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # Start Inspection button
        self.start_inspection_btn = QPushButton("▶ Start Inspection")
        self.start_inspection_btn.setFixedHeight(50)
        self.start_inspection_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066ff;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #0052cc;
            }
            QPushButton:pressed {
                background-color: #0047b3;
            }
        """)
        self.start_inspection_btn.clicked.connect(self.toggle_inspection)
        buttons_layout.addWidget(self.start_inspection_btn, stretch=2)

        # Capture button
        capture_btn = QPushButton("📷 Capture")
        capture_btn.setFixedHeight(50)
        capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        buttons_layout.addWidget(capture_btn)

        # Pause button
        pause_btn = QPushButton("⏸")
        pause_btn.setFixedSize(50, 50)
        pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        pause_btn.clicked.connect(self.toggle_pause)
        buttons_layout.addWidget(pause_btn)

        # Record button
        record_btn = QPushButton("⏺")
        record_btn.setFixedSize(50, 50)
        record_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ff4444;
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        buttons_layout.addWidget(record_btn)

        panel_layout.addLayout(buttons_layout)

        return panel

    def get_icon_button_style(self):
        """Get stylesheet for icon buttons."""
        return """
            QPushButton {
                background-color: #1a1a1a;
                color: #999;
                border: none;
                border-radius: 6px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #0a0a0a;
            }
        """

    def get_slider_style(self):
        """Get stylesheet for sliders."""
        return """
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #cc44ff;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #dd66ff;
            }
        """

    def toggle_inspection(self):
        """Toggle inspection mode."""
        self.is_inspecting = not self.is_inspecting
        if self.is_inspecting:
            self.start_inspection_btn.setText("⏹ Stop Inspection")
        else:
            self.start_inspection_btn.setText("▶ Start Inspection")

    def toggle_pause(self):
        """Toggle video pause."""
        if self.timer.isActive():
            self.stop_video()
        else:
            self.start_video()

    def refresh_camera(self):
        """Refresh camera connection."""
        print(f"Refreshing camera: switching to type={self.camera_type}, index={self.camera_index}")

        # Stop the timer first
        self.stop_video()

        # Release camera resources
        if self.cap is not None:
            try:
                print(f"Releasing camera of type: {type(self.cap)}")
                self.camera.release_cap(self.cap)
                print("Camera released successfully")
            except Exception as e:
                print(f"Error releasing camera: {e}")
            finally:
                self.cap = None

        # Use QTimer for non-blocking delay to ensure camera is fully released
        # Increased delay for RealSense cameras which need more time
        QTimer.singleShot(500, self.start_video)


    def on_camera_type_changed(self, text):
        """Handle camera type change."""
        # Map display text to camera type
        if text == "Intel RealSense":
            new_camera_type = "intel-realsense"
        else:
            new_camera_type = "usb-standard"

        # Only restart camera if type actually changed
        if new_camera_type != self.camera_type:
            self.camera_type = new_camera_type
            # Restart the camera with new type
            self.refresh_camera()

    def populate_camera_devices(self):
        """Populate the camera device dropdown with available cameras."""
        self.camera_device_combo.clear()

        try:
            # Get list of available cameras
            cameras = self.camera.get_cameras_list()

            if cameras:
                for cam in cameras:
                    self.camera_device_combo.addItem(f"Camera {cam['index']}: {cam['name']}", cam['index'])

                # Set current selection
                current_index = self.camera_device_combo.findData(self.camera_index)
                if current_index >= 0:
                    self.camera_device_combo.setCurrentIndex(current_index)
            else:
                # No cameras found, add default options
                self.camera_device_combo.addItem("Camera 0 (Default)", 0)
                self.camera_device_combo.addItem("Camera 1", 1)
        except Exception as e:
            # Fallback if camera enumeration fails
            print(f"Failed to enumerate cameras: {e}")
            self.camera_device_combo.addItem("Camera 0 (Default)", 0)
            self.camera_device_combo.addItem("Camera 1", 1)

    def on_camera_device_changed(self, index):
        """Handle camera device change."""
        new_camera_index = self.camera_device_combo.currentData()

        # Only restart camera if index actually changed
        if new_camera_index is not None and new_camera_index != self.camera_index:
            self.camera_index = new_camera_index
            # Restart the camera with new device
            self.refresh_camera()

    def start_video(self):
        """Start capturing and displaying video."""
        # Always try to load camera if cap is None
        if self.cap is None:
            try:
                print(f"Loading camera: index={self.camera_index}, type={self.camera_type}")
                self.cap = self.camera.load_cap(self.camera_index, self.camera_type)
                print(f"Camera loaded successfully")
            except Exception as e:
                print(f"Error: Could not open camera {self.camera_index} (type: {self.camera_type}): {e}")
                self.cap = None
                return

        # Set up timer to update frames
        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)

        # Start the timer if not already running
        if not self.timer.isActive():
            self.timer.start(30)  # Update every 30ms (~33 FPS)

    def stop_video(self):
        """Stop capturing and displaying video."""
        if self.timer is not None and self.timer.isActive():
            self.timer.stop()

    def update_frame(self):
        """Read and display the next video frame."""
        if self.cap is not None:
            ret, frame = self.camera.read_frame(self.cap)

            if ret:
                # Convert the frame from BGR (OpenCV) to RGB (Qt) using numpy
                frame_rgb = frame[..., ::-1].copy()

                # Get frame dimensions
                height, width, channels = frame_rgb.shape
                bytes_per_line = channels * width

                # Create QImage from frame data
                q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

                # Scale the image to fit the label while maintaining aspect ratio
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                # Display the frame
                self.video_label.setPixmap(scaled_pixmap)

                # Also update dataset video label if on dataset page
                if hasattr(self, 'dataset_video_label'):
                    scaled_pixmap_dataset = pixmap.scaled(
                        self.dataset_video_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.dataset_video_label.setPixmap(scaled_pixmap_dataset)

    def closeEvent(self, event):
        """Clean up when the window is closed."""
        self.stop_video()
        if self.cap is not None:
            self.camera.release_cap(self.cap)
        event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Dataset collection shortcuts
        if self.stacked_widget.currentIndex() == 1:  # Dataset page
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Right):
                if self.ok_button.isEnabled():
                    self.capture_sample("OK")
            elif event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Left):
                if self.not_ok_button.isEnabled():
                    self.capture_sample("NOT_OK")

        super().keyPressEvent(event)


def main():
    """Main function to run the video display application."""
    app = QApplication(sys.argv)

    # Use default camera (0) with USB standard camera or Intel RealSense
    # For USB camera: camera_type="usb-standard"
    # For Intel RealSense: camera_type="intel-realsense"
    window = VideoDisplayWidget(camera_index=0, camera_type="usb-standard")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

