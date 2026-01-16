"""Dataset collection page."""

import cv2
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QComboBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
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
        self.gallery_content = None
        self.ok_badge = None
        self.ng_badge = None

        # Dataset storage
        self.storage_path = Path("storage/dataset")
        self.ok_path = self.storage_path / "ok"
        self.not_ok_path = self.storage_path / "not_ok"

        # Create storage directories
        self.ok_path.mkdir(parents=True, exist_ok=True)
        self.not_ok_path.mkdir(parents=True, exist_ok=True)

        # Sample counters
        self.total_samples = 0
        self.ok_samples = 0
        self.not_ok_samples = 0

        # Gallery items
        self.gallery_items = []

        self.init_ui()

        # Load existing samples from storage
        self.load_existing_samples()

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
        self.ok_badge = QLabel("OK: 0")
        self.ok_badge.setStyleSheet(f"""
            background-color: {DarkTheme.SUCCESS};
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.ok_badge)

        self.ng_badge = QLabel("NG: 0")
        self.ng_badge.setStyleSheet(f"""
            background-color: {DarkTheme.ERROR};
            color: #fff;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.ng_badge)

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
            QScrollBar:vertical {{
                background-color: {DarkTheme.BG_PRIMARY};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {DarkTheme.BG_HOVER};
                border-radius: 4px;
            }}
        """)

        # Create a widget to hold the grid layout
        self.gallery_content = QWidget()
        self.gallery_layout = QVBoxLayout(self.gallery_content)
        self.gallery_layout.setContentsMargins(10, 10, 10, 10)
        self.gallery_layout.setSpacing(10)
        self.gallery_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Initial empty message
        empty_label = QLabel("Gallery thumbnails\nwill appear here")
        empty_label.setStyleSheet(f"color: {DarkTheme.TEXT_DISABLED}; padding: 40px;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setObjectName("empty_gallery_label")
        self.gallery_layout.addWidget(empty_label)

        gallery_scroll.setWidget(self.gallery_content)

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
            self.not_ok_button.clicked.connect(lambda: self.capture_sample("NOT_OK"))
        self.not_ok_button.setEnabled(False)
        layout.addWidget(self.not_ok_button, stretch=1)

        return layout

    def capture_sample(self, label_type):
        """Capture and save a sample image with the given label."""
        if not self.parent_window or not hasattr(self.parent_window, 'get_current_frame'):
            print("Cannot capture: parent window not available")
            return

        # Get current frame from parent
        frame = self.parent_window.get_current_frame()
        if frame is None:
            print("Cannot capture: no frame available")
            return

        # Generate timestamp filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Remove last 3 digits of microseconds

        # Determine save path based on label
        if label_type == "OK":
            save_path = self.ok_path / f"ok_{timestamp}.jpg"
            self.ok_samples += 1
        else:  # NOT_OK
            category = self.defect_category_combo.currentText().replace(" ", "_").lower()
            save_path = self.not_ok_path / f"notok_{category}_{timestamp}.jpg"
            self.not_ok_samples += 1

        # Save image
        cv2.imwrite(str(save_path), frame)
        self.total_samples += 1

        print(f"Saved sample: {save_path}")

        # Update statistics
        self.update_statistics()

        # Add to gallery
        self.add_to_gallery(save_path, label_type)

    def update_statistics(self):
        """Update the statistics display."""
        # Find and update the value labels in the statistics widget
        # This requires us to have stored references to these labels
        # For now, update the badges
        if self.ok_badge:
            self.ok_badge.setText(f"OK: {self.ok_samples}")
        if self.ng_badge:
            self.ng_badge.setText(f"NG: {self.not_ok_samples}")

        # Update the stat labels in the left panel
        if hasattr(self, 'total_samples_label') and self.total_samples_label:
            # The stat labels are layouts, need to find the value QLabel
            self.update_stat_label(self.total_samples_label, str(self.total_samples))
        if hasattr(self, 'ok_samples_label') and self.ok_samples_label:
            self.update_stat_label(self.ok_samples_label, str(self.ok_samples))
        if hasattr(self, 'not_ok_samples_label') and self.not_ok_samples_label:
            self.update_stat_label(self.not_ok_samples_label, str(self.not_ok_samples))

    def update_stat_label(self, layout, value_text):
        """Update a stat label's value."""
        if layout and layout.count() >= 2:
            value_widget = layout.itemAt(layout.count() - 1).widget()
            if isinstance(value_widget, QLabel):
                value_widget.setText(value_text)

    def add_to_gallery(self, image_path, label_type):
        """Add a thumbnail to the gallery."""
        # Remove empty label if this is the first image
        if len(self.gallery_items) == 0:
            # Find and remove the empty label
            for i in range(self.gallery_layout.count()):
                widget = self.gallery_layout.itemAt(i).widget()
                if widget and widget.objectName() == "empty_gallery_label":
                    widget.deleteLater()
                    break

        # Create thumbnail widget
        thumbnail_widget = QWidget()
        thumbnail_widget.setFixedHeight(100)
        thumbnail_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
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
        filename = image_path.name
        filename_label = QLabel(filename[:20] + "..." if len(filename) > 20 else filename)
        filename_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 10px;")
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
        # Load OK samples
        if self.ok_path.exists():
            ok_files = sorted(self.ok_path.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)
            for img_path in ok_files[:50]:  # Load last 50
                self.ok_samples += 1
                self.total_samples += 1
                self.add_to_gallery(img_path, "OK")

        # Load NOT OK samples
        if self.not_ok_path.exists():
            notok_files = sorted(self.not_ok_path.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)
            for img_path in notok_files[:50]:  # Load last 50
                self.not_ok_samples += 1
                self.total_samples += 1
                self.add_to_gallery(img_path, "NOT_OK")

        # Update statistics
        self.update_statistics()


