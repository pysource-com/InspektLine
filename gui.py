import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QSlider, QFrame, QComboBox, QCheckBox,
                                QLineEdit, QScrollArea, QStackedWidget)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from camera.camera import Camera
from gui.pages.settings_page import SettingsPage
from gui.pages.home_page import HomePage
from gui.pages.annotator_page import AnnotatorPage
from gui.pages.training_page import TrainingPage
from database.project_db import ProjectDatabase


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
        self.current_page = "home"  # Track current page
        self.current_frame = None  # Store the current frame for dataset capture

        # Database
        self.db = ProjectDatabase()

        # Page indices for stacked widget
        self.PAGE_HOME = 0
        self.PAGE_CAMERA = 1
        self.PAGE_DATASET = 2
        self.PAGE_ANNOTATE = 3
        self.PAGE_TRAIN = 4
        self.PAGE_SETTINGS = 5

        # Camera info tracking
        self.frame_count = 0
        self.fps_update_counter = 0
        self.fps_update_interval = 10  # Update FPS display every N frames

        # Settings values
        self.confidence_threshold = 85
        self.min_defect_size = 10
        self.auto_focus_enabled = False  # Disabled by default, manual focus enabled
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
        self.gallery_items = []
        self.gallery_loaded = False

        self.init_ui()
        self.start_video()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("InspektLine - Visual Inspection System")
        self.setGeometry(100, 100, 1400, 900)

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

        # PAGE 0: Home page (default)
        self.home_page = HomePage(parent=self)
        self.home_page.navigate_to_capture.connect(lambda: self.switch_to_page(self.PAGE_DATASET))
        self.home_page.navigate_to_annotate.connect(lambda: self.switch_to_page(self.PAGE_ANNOTATE))
        self.home_page.navigate_to_train.connect(lambda: self.switch_to_page(self.PAGE_TRAIN))
        self.home_page.navigate_to_settings.connect(lambda: self.switch_to_page(self.PAGE_SETTINGS))
        self.home_page.navigate_to_dataset.connect(lambda: self.switch_to_page(self.PAGE_DATASET))
        self.stacked_widget.addWidget(self.home_page)

        # PAGE 1: Camera feed page
        camera_page = self.create_camera_page()
        self.stacked_widget.addWidget(camera_page)

        # PAGE 2: Dataset collection page
        dataset_page = self.create_dataset_collection_page()
        self.stacked_widget.addWidget(dataset_page)

        # PAGE 3: Annotator page
        self.annotator_page = AnnotatorPage(parent=self)
        self.annotator_page.navigate_back.connect(lambda: self.switch_to_page(self.PAGE_HOME))
        self.stacked_widget.addWidget(self.annotator_page)

        # PAGE 4: Training page
        self.training_page = TrainingPage(parent=self)
        self.training_page.navigate_back.connect(lambda: self.switch_to_page(self.PAGE_HOME))
        self.stacked_widget.addWidget(self.training_page)

        # PAGE 5: Settings page
        settings_page = self.create_settings_page()
        self.stacked_widget.addWidget(settings_page)

        # Set HomePage as default
        self.stacked_widget.setCurrentIndex(self.PAGE_HOME)

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

        # Create video display frame with info overlay
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
        video_layout.setSpacing(10)

        # Create label to display video frames
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000; border: none;")
        self.video_label.setMinimumSize(800, 480)
        video_layout.addWidget(self.video_label)

        # Add info overlay at the bottom
        info_overlay = self.create_camera_info_overlay()
        video_layout.addWidget(info_overlay)

        content_layout.addWidget(video_container, stretch=1)

        # Bottom control panel
        bottom_panel = self.create_bottom_panel()
        content_layout.addWidget(bottom_panel)

        return content_widget

    def create_camera_info_overlay(self):
        """Create an info overlay showing camera feed details."""
        overlay = QWidget()
        overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 6px;
            }
        """)
        overlay.setMaximumHeight(40)

        overlay_layout = QHBoxLayout(overlay)
        overlay_layout.setContentsMargins(15, 8, 15, 8)
        overlay_layout.setSpacing(20)

        # Connection status indicator
        self.camera_status_indicator = QLabel("●")
        self.camera_status_indicator.setStyleSheet("color: #00cc00; font-size: 16px;")
        overlay_layout.addWidget(self.camera_status_indicator)

        self.camera_status_text = QLabel("Connected")
        self.camera_status_text.setStyleSheet("color: #fff; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(self.camera_status_text)

        overlay_layout.addStretch()

        # FPS counter
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet("color: #999; font-size: 11px;")
        overlay_layout.addWidget(fps_label)

        self.camera_fps_value = QLabel("30")
        self.camera_fps_value.setStyleSheet("color: #fff; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(self.camera_fps_value)

        # Resolution info
        res_label = QLabel("Resolution:")
        res_label.setStyleSheet("color: #999; font-size: 11px; margin-left: 15px;")
        overlay_layout.addWidget(res_label)

        self.camera_resolution_value = QLabel("...")
        self.camera_resolution_value.setStyleSheet("color: #fff; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(self.camera_resolution_value)

        # Frame counter for debugging
        frame_label = QLabel("Frame:")
        frame_label.setStyleSheet("color: #999; font-size: 11px; margin-left: 15px;")
        overlay_layout.addWidget(frame_label)

        self.camera_frame_counter = QLabel("0")
        self.camera_frame_counter.setStyleSheet("color: #fff; font-size: 12px; font-weight: bold;")
        overlay_layout.addWidget(self.camera_frame_counter)

        return overlay

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

        # OK count badge - store reference
        self.gallery_ok_badge = QLabel("OK: 0")
        self.gallery_ok_badge.setStyleSheet("""
            background-color: #00cc00;
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.gallery_ok_badge)

        # NG count badge - store reference
        self.gallery_ng_badge = QLabel("NG: 0")
        self.gallery_ng_badge.setStyleSheet("""
            background-color: #ff0000;
            color: #fff;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.gallery_ng_badge)

        layout.addLayout(header_layout)

        # Gallery content with proper container
        gallery_scroll = QScrollArea()
        gallery_scroll.setWidgetResizable(True)
        gallery_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0a0a0a;
                border: none;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: #0a0a0a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #2a2a2a;
                border-radius: 4px;
            }
        """)

        # Create a widget to hold the gallery items
        self.gallery_content = QWidget()
        self.gallery_layout = QVBoxLayout(self.gallery_content)
        self.gallery_layout.setContentsMargins(10, 10, 10, 10)
        self.gallery_layout.setSpacing(10)
        self.gallery_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Initial empty message
        self.gallery_empty_label = QLabel("Gallery thumbnails\nwill appear here")
        self.gallery_empty_label.setStyleSheet("color: #666; padding: 40px;")
        self.gallery_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gallery_layout.addWidget(self.gallery_empty_label)

        # Initialize gallery items list
        self.gallery_items = []

        gallery_scroll.setWidget(self.gallery_content)

        layout.addWidget(gallery_scroll, stretch=1)

        return widget

    def capture_sample(self, label_type):
        """Capture a sample with the given label."""
        import cv2
        from datetime import datetime
        from pathlib import Path

        if self.current_frame is None:
            print("Cannot capture: no frame available")
            return

        print(f"Capturing sample: {label_type}")

        # Setup storage paths
        storage_path = Path("storage/dataset")
        ok_path = storage_path / "ok"
        not_ok_path = storage_path / "not_ok"

        # Create directories if they don't exist
        ok_path.mkdir(parents=True, exist_ok=True)
        not_ok_path.mkdir(parents=True, exist_ok=True)

        # Generate timestamp filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        # Save based on label type
        if label_type == "OK":
            save_path = ok_path / f"ok_{timestamp}.jpg"
            self.ok_samples += 1
        else:  # NOT_OK
            save_path = not_ok_path / f"notok_{timestamp}.jpg"
            self.not_ok_samples += 1

        # Save the image
        cv2.imwrite(str(save_path), self.current_frame)
        self.total_samples += 1

        # Add to database
        self.db.add_image(str(save_path))

        print(f"Saved sample: {save_path}")

        # Update UI
        self.update_dataset_statistics()

        # Update gallery badges
        self.update_gallery_badges()

        # Add to gallery display
        self.add_to_gallery(save_path, label_type)

        print(f"Total: {self.total_samples}, OK: {self.ok_samples}, NOT OK: {self.not_ok_samples}")

    def update_dataset_statistics(self):
        """Update dataset statistics labels."""
        self.total_samples_label.setText(str(self.total_samples))
        self.ok_samples_label.setText(str(self.ok_samples))
        self.not_ok_samples_label.setText(str(self.not_ok_samples))

    def update_gallery_badges(self):
        """Update the gallery badge counters."""
        if hasattr(self, 'gallery_ok_badge'):
            self.gallery_ok_badge.setText(f"OK: {self.ok_samples}")
        if hasattr(self, 'gallery_ng_badge'):
            self.gallery_ng_badge.setText(f"NG: {self.not_ok_samples}")

    def add_to_gallery(self, image_path, label_type):
        """Add a thumbnail to the gallery."""
        from pathlib import Path

        # Remove empty label if this is the first image
        if len(self.gallery_items) == 0 and hasattr(self, 'gallery_empty_label'):
            if self.gallery_empty_label is not None:
                self.gallery_empty_label.deleteLater()
                self.gallery_empty_label = None

        # Create thumbnail widget
        thumbnail_widget = QWidget()
        thumbnail_widget.setFixedHeight(100)
        thumbnail_widget.setStyleSheet(f"""
            QWidget {{
                background-color: #1a1a1a;
                border-radius: 8px;
                border: 2px solid {'#00cc00' if label_type == 'OK' else '#cc0000'};
            }}
        """)

        thumb_layout = QHBoxLayout(thumbnail_widget)
        thumb_layout.setContentsMargins(8, 8, 8, 8)
        thumb_layout.setSpacing(10)

        # Load and display thumbnail image
        pixmap = QPixmap(str(image_path))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(84, 84, Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
            image_label = QLabel()
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_layout.addWidget(image_label)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Label type
        label_widget = QLabel(label_type)
        label_widget.setStyleSheet(f"""
            color: {'#00cc00' if label_type == 'OK' else '#cc0000'};
            font-weight: bold;
            font-size: 12px;
        """)
        info_layout.addWidget(label_widget)

        # Filename
        filename = Path(image_path).name
        filename_label = QLabel(filename[:20] + "..." if len(filename) > 20 else filename)
        filename_label.setStyleSheet("color: #999; font-size: 10px;")
        info_layout.addWidget(filename_label)

        info_layout.addStretch()
        thumb_layout.addLayout(info_layout)

        # Add to layout at the top (most recent first)
        self.gallery_layout.insertWidget(0, thumbnail_widget)
        self.gallery_items.append(thumbnail_widget)

        # Limit gallery to last 50 items
        if len(self.gallery_items) > 50:
            old_widget = self.gallery_items.pop(0)
            old_widget.deleteLater()

    def load_existing_samples(self):
        """Load existing samples from storage folder."""
        from pathlib import Path

        storage_path = Path("storage/dataset")
        ok_path = storage_path / "ok"
        not_ok_path = storage_path / "not_ok"

        # Lists to hold all files with their timestamps
        all_files = []

        # Load OK samples
        if ok_path.exists():
            ok_files = list(ok_path.glob("*.jpg"))
            for img_path in ok_files:
                all_files.append((img_path.stat().st_mtime, img_path, "OK"))
                self.ok_samples += 1
                self.total_samples += 1

        # Load NOT OK samples
        if not_ok_path.exists():
            notok_files = list(not_ok_path.glob("*.jpg"))
            for img_path in notok_files:
                all_files.append((img_path.stat().st_mtime, img_path, "NOT_OK"))
                self.not_ok_samples += 1
                self.total_samples += 1

        # Sort by modification time (most recent first) and take last 50
        all_files.sort(reverse=True, key=lambda x: x[0])
        recent_files = all_files[:50]

        # Add to gallery (reverse order so oldest of the 50 is at bottom)
        for _, img_path, label_type in reversed(recent_files):
            self.add_to_gallery(img_path, label_type)

        # Update statistics and badges
        self.update_dataset_statistics()
        self.update_gallery_badges()

        print(f"Loaded {len(recent_files)} existing samples from storage")

    def create_settings_page(self):
        """Create the settings configuration page using modular architecture."""
        # Use the new modular SettingsPage with camera preview support
        return SettingsPage(parent=self)

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

        # Autofocus checkbox
        self.autofocus_checkbox = QCheckBox("Enable auto-focus")
        self.autofocus_checkbox.setChecked(self.auto_focus_enabled)
        self.autofocus_checkbox.setStyleSheet(self.get_checkbox_style())
        self.autofocus_checkbox.stateChanged.connect(self.on_autofocus_changed)
        self.autofocus_checkbox.stateChanged.connect(self._on_autofocus_toggled)
        section_layout.addWidget(self.autofocus_checkbox)

        # Manual Focus slider
        manual_focus_label = QLabel("Manual Focus")
        manual_focus_label.setStyleSheet("color: #999; font-size: 13px; margin-top: 15px; margin-bottom: 8px;")
        section_layout.addWidget(manual_focus_label)

        focus_control_layout = QHBoxLayout()
        focus_control_layout.setSpacing(15)

        self.manual_focus_slider = QSlider(Qt.Orientation.Horizontal)
        self.manual_focus_slider.setMinimum(0)
        self.manual_focus_slider.setMaximum(255)
        self.manual_focus_slider.setValue(128)
        self.manual_focus_slider.setStyleSheet(self.get_slider_style())
        self.manual_focus_slider.setEnabled(not self.auto_focus_enabled)  # Enabled when autofocus is off
        self.manual_focus_slider.valueChanged.connect(self.on_manual_focus_changed)
        focus_control_layout.addWidget(self.manual_focus_slider, stretch=1)

        self.focus_value_label = QLabel("128")
        self.focus_value_label.setStyleSheet("color: #999; font-size: 13px; min-width: 35px;")
        self.manual_focus_slider.valueChanged.connect(lambda v: self.focus_value_label.setText(str(v)))
        focus_control_layout.addWidget(self.focus_value_label)

        section_layout.addLayout(focus_control_layout)

        # Info text
        info_label = QLabel("Note: Manual focus is only available when auto-focus is disabled")
        info_label.setStyleSheet("color: #999; font-size: 11px; font-style: italic; margin-top: 5px;")
        info_label.setWordWrap(True)
        section_layout.addWidget(info_label)

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

        # Home button (active by default)
        home_btn = SidebarButton("🏠")
        home_btn.setChecked(True)
        home_btn.setToolTip("Home")
        home_btn.clicked.connect(lambda: self.switch_to_page(self.PAGE_HOME, home_btn))
        sidebar_layout.addWidget(home_btn)
        self.sidebar_buttons.append(home_btn)

        # Camera button - Live Feed
        camera_btn = SidebarButton("📷")
        camera_btn.setToolTip("Live Camera")
        camera_btn.clicked.connect(lambda: self.switch_to_page(self.PAGE_CAMERA, camera_btn))
        sidebar_layout.addWidget(camera_btn)
        self.sidebar_buttons.append(camera_btn)

        # Capture button - Dataset Collection
        capture_btn = SidebarButton("📸")
        capture_btn.setToolTip("Collect Images")
        capture_btn.clicked.connect(lambda: self.switch_to_page(self.PAGE_DATASET, capture_btn))
        sidebar_layout.addWidget(capture_btn)
        self.sidebar_buttons.append(capture_btn)

        # Annotate button
        annotate_btn = SidebarButton("🏷️")
        annotate_btn.setToolTip("Annotate Dataset")
        annotate_btn.clicked.connect(lambda: self.switch_to_page(self.PAGE_ANNOTATE, annotate_btn))
        sidebar_layout.addWidget(annotate_btn)
        self.sidebar_buttons.append(annotate_btn)

        # Train button
        train_btn = SidebarButton("🧠")
        train_btn.setToolTip("Train Model")
        train_btn.clicked.connect(lambda: self.switch_to_page(self.PAGE_TRAIN, train_btn))
        sidebar_layout.addWidget(train_btn)
        self.sidebar_buttons.append(train_btn)

        sidebar_layout.addStretch()

        # Settings button at bottom
        settings_btn = SidebarButton("⚙️")
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(lambda: self.switch_to_page(self.PAGE_SETTINGS, settings_btn))
        sidebar_layout.addWidget(settings_btn)
        self.sidebar_buttons.append(settings_btn)

        # Power button at very bottom
        power_btn = SidebarButton("⏻")
        power_btn.setToolTip("Exit")
        power_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(power_btn)

        return sidebar

    def switch_to_page(self, page_index, clicked_button=None):
        """Switch to a different page in the stacked widget."""
        self.stacked_widget.setCurrentIndex(page_index)

        # Update button states
        if clicked_button:
            for btn in self.sidebar_buttons:
                btn.setChecked(btn == clicked_button)

        # Enable/disable dataset capture buttons based on page
        if page_index == self.PAGE_DATASET:  # Dataset collection page
            self.is_capturing = True
            if hasattr(self, 'capturing_badge'):
                self.capturing_badge.setVisible(True)
            if hasattr(self, 'ok_button'):
                self.ok_button.setEnabled(True)
            if hasattr(self, 'not_ok_button'):
                self.not_ok_button.setEnabled(True)

            # Load existing images on first visit to dataset page
            if not self.gallery_loaded:
                self.load_existing_samples()
                self.gallery_loaded = True
        else:
            self.is_capturing = False
            if hasattr(self, 'capturing_badge'):
                self.capturing_badge.setVisible(False)
            if hasattr(self, 'ok_button'):
                self.ok_button.setEnabled(False)
            if hasattr(self, 'not_ok_button'):
                self.not_ok_button.setEnabled(False)

        # Refresh home page when navigating to it
        if page_index == self.PAGE_HOME and hasattr(self, 'home_page'):
            self.home_page.refresh_state()

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

    def on_autofocus_changed(self, state):
        """Handle autofocus checkbox state change."""
        enabled = state == Qt.CheckState.Checked.value
        if self.cap is not None:
            success = self.camera.set_autofocus(self.cap, enabled)
            if not success:
                print(f"Warning: Could not {'enable' if enabled else 'disable'} autofocus")
        else:
            print("Camera is not initialized")

    def _on_autofocus_toggled(self, state):
        """Handle autofocus checkbox toggle to enable/disable manual focus slider."""
        is_autofocus_enabled = state == Qt.CheckState.Checked.value
        # Enable manual focus slider only when autofocus is disabled
        if hasattr(self, 'manual_focus_slider'):
            self.manual_focus_slider.setEnabled(not is_autofocus_enabled)

    def on_manual_focus_changed(self, value):
        """Handle manual focus slider value change."""
        if self.cap is not None:
            success = self.camera.set_manual_focus(self.cap, value)
            if not success:
                print(f"Warning: Could not set manual focus to {value}")
        else:
            print("Camera is not initialized")

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
                # Store the current frame for dataset capture
                self.current_frame = frame.copy()

                # Increment frame counter
                self.frame_count += 1

                # Update camera info overlay
                if hasattr(self, 'camera_frame_counter'):
                    self.camera_frame_counter.setText(str(self.frame_count))

                # Update resolution info (only once or when changed)
                if hasattr(self, 'camera_resolution_value') and self.frame_count == 1:
                    height, width = frame.shape[:2]
                    self.camera_resolution_value.setText(f"{width}×{height}")

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

                # Enable dataset capture buttons if they exist and are on dataset page
                if hasattr(self, 'ok_button') and hasattr(self, 'not_ok_button'):
                    if self.stacked_widget.currentIndex() == 1:  # Dataset page
                        self.ok_button.setEnabled(True)
                        self.not_ok_button.setEnabled(True)
            else:
                # Update status indicator to show disconnection
                if hasattr(self, 'camera_status_indicator'):
                    self.camera_status_indicator.setStyleSheet("color: #ff0000; font-size: 16px;")
                if hasattr(self, 'camera_status_text'):
                    self.camera_status_text.setText("Disconnected")

    def get_current_frame(self):
        """Get the current camera frame."""
        return self.current_frame

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

