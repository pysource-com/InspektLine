"""Dataset collection page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QComboBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from gui.components import VideoLabel
from gui.styles import StyleSheets, DarkTheme


class DatasetPage(QWidget):
    """Dataset collection page for labeling training data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # Initialize UI elements that will be referenced
        self.capturing_badge = None
        self.ok_button = None
        self.not_ok_button = None
        self.dataset_video_label = None
        self.total_samples_label = None
        self.ok_samples_label = None
        self.not_ok_samples_label = None
        self.defect_category_combo = None

        self.init_ui()

    def init_ui(self):
        """Initialize the dataset collection page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Top header
        header = self.create_header()
        main_layout.addLayout(header)

        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left panel
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel)

        # Center panel
        center_panel = self.create_center_panel()
        content_layout.addWidget(center_panel, stretch=1)

        # Right panel
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel)

        main_layout.addLayout(content_layout)

    def create_header(self):
        """Create the page header."""
        header_layout = QHBoxLayout()

        title = QLabel("Dataset Collection")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #fff;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Shortcuts button
        shortcuts_btn = QPushButton("⌨ Shortcuts (?)")
        shortcuts_btn.setFixedHeight(40)
        shortcuts_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_HOVER};
                color: {DarkTheme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
            }}
        """)
        header_layout.addWidget(shortcuts_btn)

        # Export button
        export_btn = QPushButton("⬇ Export Dataset")
        export_btn.setFixedHeight(40)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
        """)
        header_layout.addWidget(export_btn)

        return header_layout

    def create_left_panel(self):
        """Create the left statistics panel."""
        panel = QWidget()
        panel.setFixedWidth(400)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        subtitle = QLabel("Label images for training data")
        subtitle.setStyleSheet(f"font-size: 14px; color: {DarkTheme.TEXT_SECONDARY};")
        layout.addWidget(subtitle)

        # Statistics widget
        stats_widget = self.create_statistics_widget()
        layout.addWidget(stats_widget)

        # Defect category widget
        defect_widget = self.create_defect_category_widget()
        layout.addWidget(defect_widget)

        # Recent samples
        recent_widget = self.create_recent_samples_widget()
        layout.addWidget(recent_widget)

        layout.addStretch()

        return panel

    def create_center_panel(self):
        """Create the center video feed panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Feed header
        feed_header = QHBoxLayout()

        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        camera_icon = QLabel("📹")
        camera_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(camera_icon)

        feed_label = QLabel("Live Feed")
        feed_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        title_layout.addWidget(feed_label)

        self.capturing_badge = QLabel("CAPTURING")
        self.capturing_badge.setStyleSheet(f"""
            background-color: {DarkTheme.SUCCESS};
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        """)
        self.capturing_badge.setVisible(False)
        title_layout.addWidget(self.capturing_badge)
        title_layout.addStretch()

        feed_header.addWidget(title_widget)
        feed_header.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet(StyleSheets.get_icon_button_style())
        if self.parent_window:
            refresh_btn.clicked.connect(self.parent_window.refresh_camera)
        feed_header.addWidget(refresh_btn)

        layout.addLayout(feed_header)

        # Video display
        video_container = QWidget()
        video_container.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
            }}
        """)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(10, 10, 10, 10)

        self.dataset_video_label = VideoLabel()
        video_layout.addWidget(self.dataset_video_label)

        layout.addWidget(video_container, stretch=1)

        # Capture buttons
        buttons_layout = self.create_capture_buttons()
        layout.addLayout(buttons_layout)

        return panel

    def create_right_panel(self):
        """Create the right gallery panel."""
        panel = QWidget()
        panel.setFixedWidth(300)
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Collection Gallery")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Badges
        ok_badge = QLabel("OK: 0")
        ok_badge.setStyleSheet(f"""
            background-color: {DarkTheme.SUCCESS};
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(ok_badge)

        ng_badge = QLabel("NG: 0")
        ng_badge.setStyleSheet(f"""
            background-color: {DarkTheme.ERROR};
            color: #fff;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(ng_badge)

        layout.addLayout(header_layout)

        # Gallery content
        gallery_scroll = QScrollArea()
        gallery_scroll.setWidgetResizable(True)
        gallery_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {DarkTheme.BG_PRIMARY};
                border: none;
                border-radius: 8px;
            }}
        """)

        gallery_content = QLabel("Gallery thumbnails\nwill appear here")
        gallery_content.setStyleSheet(f"color: {DarkTheme.TEXT_DISABLED}; padding: 40px;")
        gallery_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gallery_scroll.setWidget(gallery_content)

        layout.addWidget(gallery_scroll, stretch=1)

        return panel

    def create_statistics_widget(self):
        """Create session statistics widget."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Session Statistics")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        # Total Samples
        self.total_samples_label = self.create_stat_row("Total Samples", "0")
        layout.addLayout(self.total_samples_label)

        # OK Samples
        self.ok_samples_label = self.create_stat_row("OK Samples", "0", DarkTheme.SUCCESS)
        layout.addLayout(self.ok_samples_label)

        # NOT OK Samples
        self.not_ok_samples_label = self.create_stat_row("NOT OK Samples", "0", DarkTheme.ERROR)
        layout.addLayout(self.not_ok_samples_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {DarkTheme.BORDER_SECONDARY};")
        layout.addWidget(separator)

        # Duration and rate
        duration_layout = self.create_stat_row("Session Duration", "0 min")
        layout.addLayout(duration_layout)

        rate_layout = self.create_stat_row("Rate", "0 samples/min")
        layout.addLayout(rate_layout)

        return widget

    def create_stat_row(self, label_text, value_text, color=None):
        """Create a statistics row."""
        layout = QHBoxLayout()

        label = QLabel(label_text)
        label_color = color if color else DarkTheme.TEXT_SECONDARY
        label.setStyleSheet(f"color: {label_color}; font-size: 14px;")
        layout.addWidget(label)
        layout.addStretch()

        value = QLabel(value_text)
        value_color = color if color else DarkTheme.TEXT_PRIMARY
        value.setStyleSheet(f"color: {value_color}; font-size: 18px; font-weight: bold;")
        layout.addWidget(value)

        return layout

    def create_defect_category_widget(self):
        """Create defect category selection widget."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Defect Category")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        subtitle = QLabel("Select category before labeling NOT OK samples")
        subtitle.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(subtitle)

        self.defect_category_combo = QComboBox()
        self.defect_category_combo.addItems([
            "Surface Defect", "Crack", "Scratch", "Dent",
            "Discoloration", "Missing Part", "Contamination"
        ])
        self.defect_category_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.defect_category_combo.setFixedHeight(45)
        layout.addWidget(self.defect_category_combo)

        return widget

    def create_recent_samples_widget(self):
        """Create recent samples widget."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Recent Samples")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(title)

        recent_list = QLabel("No samples collected yet")
        recent_list.setStyleSheet(f"color: {DarkTheme.TEXT_DISABLED}; font-size: 14px; padding: 20px;")
        recent_list.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(recent_list)

        return widget

    def create_capture_buttons(self):
        """Create OK and NOT OK capture buttons."""
        layout = QHBoxLayout()
        layout.setSpacing(20)

        # OK button
        self.ok_button = QPushButton("✓\nOK\nPress → or Enter")
        self.ok_button.setFixedHeight(120)
        self.ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.SUCCESS};
                color: #000;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.SUCCESS_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {DarkTheme.SUCCESS_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: #004400;
                color: {DarkTheme.TEXT_DISABLED};
            }}
        """)
        if self.parent_window:
            self.ok_button.clicked.connect(lambda: self.parent_window.capture_sample("OK"))
        self.ok_button.setEnabled(False)
        layout.addWidget(self.ok_button, stretch=1)

        # NOT OK button
        self.not_ok_button = QPushButton("✕\nNOT OK\nPress ← or Backspace")
        self.not_ok_button.setFixedHeight(120)
        self.not_ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ERROR};
                color: #fff;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.ERROR_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {DarkTheme.ERROR_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: #440000;
                color: {DarkTheme.TEXT_DISABLED};
            }}
        """)
        if self.parent_window:
            self.not_ok_button.clicked.connect(lambda: self.parent_window.capture_sample("NOT_OK"))
        self.not_ok_button.setEnabled(False)
        layout.addWidget(self.not_ok_button, stretch=1)

        return layout

