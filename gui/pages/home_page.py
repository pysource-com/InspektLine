"""Home page with guided onboarding workflow."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QSpacerItem, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from pathlib import Path

from gui.styles.themes import DarkTheme
from database.project_db import ProjectDatabase, ProjectStats


class WorkflowStep(QWidget):
    """A single step in the getting started workflow."""

    clicked = Signal()

    def __init__(self, step_number: int, title: str, subtitle: str,
                 is_active: bool = False, is_complete: bool = False, parent=None):
        super().__init__(parent)
        self.step_number = step_number
        self.is_active = is_active
        self.is_complete = is_complete

        self.init_ui(title, subtitle)

    def init_ui(self, title: str, subtitle: str):
        """Initialize the step UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        # Step number circle
        self.number_label = QLabel()
        self.number_label.setFixedSize(28, 28)
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_number_style()
        layout.addWidget(self.number_label)

        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if self.is_active else QFont.Weight.Normal))
        self._update_title_style()
        text_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px;")
        text_layout.addWidget(self.subtitle_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _update_number_style(self):
        """Update the number circle style based on state."""
        if self.is_complete:
            # Green checkmark circle
            self.number_label.setText("✓")
            self.number_label.setStyleSheet(f"""
                background-color: {DarkTheme.SUCCESS};
                color: white;
                border-radius: 14px;
                font-size: 14px;
                font-weight: bold;
            """)
        elif self.is_active:
            # Blue active circle
            self.number_label.setText(str(self.step_number))
            self.number_label.setStyleSheet(f"""
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border-radius: 14px;
                font-size: 12px;
                font-weight: bold;
            """)
        else:
            # Gray inactive circle
            self.number_label.setText(str(self.step_number))
            self.number_label.setStyleSheet(f"""
                background-color: {DarkTheme.BG_HOVER};
                color: {DarkTheme.TEXT_SECONDARY};
                border-radius: 14px;
                font-size: 12px;
            """)

    def _update_title_style(self):
        """Update the title style based on state."""
        if self.is_active:
            self.title_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 13px;")
        else:
            self.title_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px;")

    def set_state(self, is_active: bool = False, is_complete: bool = False):
        """Update the step state."""
        self.is_active = is_active
        self.is_complete = is_complete
        self._update_number_style()
        self._update_title_style()
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if is_active else QFont.Weight.Normal))

    def set_subtitle(self, text: str):
        """Update subtitle text."""
        self.subtitle_label.setText(text)

    def mousePressEvent(self, event):
        """Handle mouse press."""
        self.clicked.emit()
        super().mousePressEvent(event)


class HomePage(QWidget):
    """Home page with guided onboarding workflow."""

    # Signals for navigation
    navigate_to_capture = Signal()
    navigate_to_annotate = Signal()
    navigate_to_train = Signal()
    navigate_to_settings = Signal()
    navigate_to_dataset = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.db = ProjectDatabase()

        # UI elements
        self.step1 = None
        self.step2 = None
        self.step3 = None
        self.main_title = None
        self.main_subtitle = None
        self.cta_button = None
        self.secondary_button = None
        self.collect_more_button = None
        self.dataset_count_label = None
        self.annotated_count_label = None
        self.start_inspection_btn = None
        self.dataset_badge = None

        self.init_ui()
        self.refresh_state()

    def init_ui(self):
        """Initialize the home page UI."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left content area
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {DarkTheme.BG_PRIMARY};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header bar
        header = self._create_header()
        content_layout.addWidget(header)

        # Main content area
        main_content = self._create_main_content()
        content_layout.addWidget(main_content, stretch=1)

        main_layout.addWidget(content_widget, stretch=1)

        # Right sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

    def _create_header(self) -> QWidget:
        """Create the header bar."""
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-bottom: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        # Title and subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel("Visual Inspection System")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 18px; font-weight: bold; border: none;")
        title_layout.addWidget(title)

        self.model_status = QLabel("No model active")
        self.model_status.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;")
        title_layout.addWidget(self.model_status)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Manage Dataset button
        self.manage_dataset_btn = QPushButton("☰  Manage Dataset")
        self.manage_dataset_btn.setFixedHeight(36)
        self.manage_dataset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manage_dataset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
            }}
        """)
        self.manage_dataset_btn.clicked.connect(self.navigate_to_dataset.emit)
        layout.addWidget(self.manage_dataset_btn)

        # Dataset count badge (initially hidden)
        self.dataset_badge = QLabel("0")
        self.dataset_badge.setFixedSize(22, 22)
        self.dataset_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dataset_badge.setStyleSheet(f"""
            background-color: {DarkTheme.PRIMARY};
            color: white;
            border-radius: 11px;
            font-size: 11px;
            font-weight: bold;
        """)
        self.dataset_badge.setVisible(False)
        layout.addWidget(self.dataset_badge)

        layout.addSpacing(8)

        # Settings button
        settings_btn = QPushButton("⚙  Settings")
        settings_btn.setFixedHeight(36)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
            }}
        """)
        settings_btn.clicked.connect(self.navigate_to_settings.emit)
        layout.addWidget(settings_btn)

        return header

    def _create_main_content(self) -> QWidget:
        """Create the main content area."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Camera icon
        icon_container = QWidget()
        icon_container.setFixedSize(100, 100)
        icon_container.setStyleSheet(f"""
            background-color: {DarkTheme.BG_INPUT};
            border-radius: 50px;
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        camera_icon = QLabel("📷")
        camera_icon.setStyleSheet("font-size: 40px; background: transparent;")
        camera_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(camera_icon)

        layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(24)

        # Main title
        self.main_title = QLabel("Welcome to Visual Inspection")
        self.main_title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 28px; font-weight: bold;")
        self.main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.main_title)

        # Main subtitle
        self.main_subtitle = QLabel('Let\'s start by collecting images for your dataset. Click "Start Collecting Images" below.')
        self.main_subtitle.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 14px;")
        self.main_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_subtitle.setWordWrap(True)
        self.main_subtitle.setMaximumWidth(500)
        layout.addWidget(self.main_subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(40)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Primary CTA button
        self.cta_button = QPushButton("📷  Start Collecting Images")
        self.cta_button.setFixedHeight(50)
        self.cta_button.setMinimumWidth(220)
        self.cta_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cta_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {DarkTheme.PRIMARY_PRESSED};
            }}
        """)
        self.cta_button.clicked.connect(self.navigate_to_capture.emit)
        buttons_layout.addWidget(self.cta_button)

        # Secondary button (Upload Images)
        self.secondary_button = QPushButton("⬆  Upload Images")
        self.secondary_button.setFixedHeight(50)
        self.secondary_button.setMinimumWidth(180)
        self.secondary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.secondary_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 0 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
            }}
        """)
        self.secondary_button.clicked.connect(self._upload_images)
        buttons_layout.addWidget(self.secondary_button)

        layout.addLayout(buttons_layout)

        # Start Inspection button (initially hidden/disabled)
        layout.addSpacing(24)

        self.start_inspection_btn = QPushButton("▶  Start Inspection")
        self.start_inspection_btn.setFixedHeight(50)
        self.start_inspection_btn.setMinimumWidth(200)
        self.start_inspection_btn.setEnabled(False)
        self.start_inspection_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_DISABLED};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
                padding: 0 24px;
                font-size: 14px;
            }}
            QPushButton:enabled {{
                background-color: {DarkTheme.SUCCESS};
                color: white;
                border: none;
            }}
            QPushButton:enabled:hover {{
                background-color: {DarkTheme.SUCCESS_HOVER};
            }}
        """)
        layout.addWidget(self.start_inspection_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Hint text
        self.hint_label = QLabel("Train a model to enable real-time inspection")
        self.hint_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Collect more images link
        layout.addSpacing(8)
        self.collect_more_button = QPushButton("+ Collect more images")
        self.collect_more_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {DarkTheme.TEXT_SECONDARY};
                border: none;
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {DarkTheme.TEXT_PRIMARY};
            }}
        """)
        self.collect_more_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collect_more_button.clicked.connect(self.navigate_to_capture.emit)
        self.collect_more_button.setVisible(False)
        layout.addWidget(self.collect_more_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        return content

    def _create_sidebar(self) -> QWidget:
        """Create the right sidebar with workflow steps."""
        sidebar = QWidget()
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-left: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        # Getting Started header
        header = QLabel("GETTING STARTED")
        header.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(header)
        layout.addSpacing(16)

        # Step 1: Collect Images
        self.step1 = WorkflowStep(1, "Collect Images", "Capture or upload product images", is_active=True)
        self.step1.clicked.connect(self.navigate_to_capture.emit)
        layout.addWidget(self.step1)

        # Step 2: Annotate Dataset
        self.step2 = WorkflowStep(2, "Annotate Dataset", "Collect images first")
        self.step2.clicked.connect(self._on_step2_clicked)
        layout.addWidget(self.step2)

        # Step 3: Train Model
        self.step3 = WorkflowStep(3, "Train Model", "Annotate images first")
        self.step3.clicked.connect(self._on_step3_clicked)
        layout.addWidget(self.step3)

        layout.addSpacing(16)

        # Annotate Now button (shown when images collected)
        self.annotate_btn = QPushButton("Annotate Images Now")
        self.annotate_btn.setFixedHeight(40)
        self.annotate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.annotate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
        """)
        self.annotate_btn.clicked.connect(self.navigate_to_annotate.emit)
        self.annotate_btn.setVisible(False)
        layout.addWidget(self.annotate_btn)

        layout.addSpacing(16)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {DarkTheme.BORDER_PRIMARY};")
        layout.addWidget(separator)

        layout.addSpacing(16)

        # Stats section
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)

        # Dataset Images count
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Dataset Images"))
        self.dataset_count_label = QLabel("0")
        self.dataset_count_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-weight: bold;")
        row1.addStretch()
        row1.addWidget(self.dataset_count_label)
        stats_layout.addLayout(row1)

        # Annotated count
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Annotated"))
        self.annotated_count_label = QLabel("0")
        self.annotated_count_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-weight: bold;")
        row2.addStretch()
        row2.addWidget(self.annotated_count_label)
        stats_layout.addLayout(row2)

        layout.addLayout(stats_layout)

        layout.addStretch()

        # Help button at bottom
        help_btn = QPushButton("?")
        help_btn.setFixedSize(32, 32)
        help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
                color: {DarkTheme.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(help_btn, alignment=Qt.AlignmentFlag.AlignRight)

        return sidebar

    def _on_step2_clicked(self):
        """Handle step 2 click."""
        stats = self.db.get_project_stats()
        if stats.total_images > 0:
            self.navigate_to_annotate.emit()

    def _on_step3_clicked(self):
        """Handle step 3 click."""
        stats = self.db.get_project_stats()
        if stats.annotated_images > 0:
            self.navigate_to_train.emit()

    def _upload_images(self):
        """Handle image upload."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )

        if files:
            import shutil
            storage_path = Path("storage/dataset/images")
            storage_path.mkdir(parents=True, exist_ok=True)

            for file_path in files:
                src = Path(file_path)
                dst = storage_path / src.name

                # Handle duplicates
                counter = 1
                while dst.exists():
                    dst = storage_path / f"{src.stem}_{counter}{src.suffix}"
                    counter += 1

                shutil.copy2(src, dst)
                self.db.add_image(str(dst))

            self.refresh_state()

    def refresh_state(self):
        """Refresh the UI based on current project state."""
        # Sync images from storage folder
        self.db.sync_images_from_folder("storage/dataset")

        stats = self.db.get_project_stats()
        models = self.db.get_models()

        # Update stats display
        self.dataset_count_label.setText(str(stats.total_images))
        self.annotated_count_label.setText(str(stats.annotated_images))

        # Update dataset badge
        if stats.total_images > 0:
            self.dataset_badge.setText(str(stats.total_images))
            self.dataset_badge.setVisible(True)
        else:
            self.dataset_badge.setVisible(False)

        # Determine workflow state
        has_images = stats.total_images > 0
        has_annotations = stats.annotated_images > 0
        has_model = len(models) > 0

        # Update model status
        if has_model:
            latest = models[0]
            self.model_status.setText(f"Model: {latest.name}")
            self.model_status.setStyleSheet(f"color: {DarkTheme.SUCCESS}; font-size: 12px; border: none;")
        else:
            self.model_status.setText("No model active")
            self.model_status.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;")

        # Update workflow steps
        if not has_images:
            # State 1: No images - show welcome
            self.step1.set_state(is_active=True, is_complete=False)
            self.step1.set_subtitle("Capture or upload product images")
            self.step2.set_state(is_active=False, is_complete=False)
            self.step2.set_subtitle("Collect images first")
            self.step3.set_state(is_active=False, is_complete=False)
            self.step3.set_subtitle("Annotate images first")

            self.main_title.setText("Welcome to Visual Inspection")
            self.main_subtitle.setText('Let\'s start by collecting images for your dataset. Click "Start Collecting Images" below.')
            self.cta_button.setText("📷  Start Collecting Images")
            self.cta_button.clicked.disconnect()
            self.cta_button.clicked.connect(self.navigate_to_capture.emit)
            self.secondary_button.setVisible(True)
            self.annotate_btn.setVisible(False)
            self.collect_more_button.setVisible(False)
            self.start_inspection_btn.setEnabled(False)
            self.hint_label.setText("Train a model to enable real-time inspection")

        elif not has_annotations:
            # State 2: Has images, no annotations - prompt to annotate
            self.step1.set_state(is_active=False, is_complete=True)
            self.step1.set_subtitle(f"{stats.total_images} images collected")
            self.step2.set_state(is_active=True, is_complete=False)
            self.step2.set_subtitle("Label defects in your images")
            self.step3.set_state(is_active=False, is_complete=False)
            self.step3.set_subtitle("Annotate images first")

            self.main_title.setText("Dataset Ready")
            self.main_subtitle.setText(f"You have {stats.total_images} images. Next, annotate them to train your model.")
            self.cta_button.setText("🏷  Annotate Images")
            self.cta_button.clicked.disconnect()
            self.cta_button.clicked.connect(self.navigate_to_annotate.emit)
            self.secondary_button.setVisible(False)
            self.annotate_btn.setVisible(True)
            self.collect_more_button.setVisible(True)
            self.start_inspection_btn.setEnabled(False)
            self.hint_label.setText("Train a model to enable real-time inspection")

        elif not has_model:
            # State 3: Has annotations, no model - prompt to train
            self.step1.set_state(is_active=False, is_complete=True)
            self.step1.set_subtitle(f"{stats.total_images} images collected")
            self.step2.set_state(is_active=False, is_complete=True)
            self.step2.set_subtitle(f"{stats.annotated_images} images annotated")
            self.step3.set_state(is_active=True, is_complete=False)
            self.step3.set_subtitle("Create your inspection model")

            self.main_title.setText("Ready to Train")
            self.main_subtitle.setText(f"You have {stats.annotated_images} annotated images. Train your model to start inspecting.")
            self.cta_button.setText("🧠  Train Model")
            self.cta_button.clicked.disconnect()
            self.cta_button.clicked.connect(self.navigate_to_train.emit)
            self.secondary_button.setVisible(False)
            self.annotate_btn.setVisible(False)
            self.collect_more_button.setVisible(True)
            self.start_inspection_btn.setEnabled(False)
            self.hint_label.setText("Train a model to enable real-time inspection")

        else:
            # State 4: Has model - ready for inspection
            self.step1.set_state(is_active=False, is_complete=True)
            self.step1.set_subtitle(f"{stats.total_images} images collected")
            self.step2.set_state(is_active=False, is_complete=True)
            self.step2.set_subtitle(f"{stats.annotated_images} images annotated")
            self.step3.set_state(is_active=False, is_complete=True)
            self.step3.set_subtitle("Model trained")

            self.main_title.setText("Ready for Inspection")
            self.main_subtitle.setText("Your model is trained. Start inspecting products in real-time.")
            self.cta_button.setText("▶  Start Inspection")
            self.cta_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {DarkTheme.SUCCESS};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0 24px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {DarkTheme.SUCCESS_HOVER};
                }}
            """)
            self.secondary_button.setVisible(False)
            self.annotate_btn.setVisible(False)
            self.collect_more_button.setVisible(True)
            self.start_inspection_btn.setEnabled(True)
            self.hint_label.setText("")

    def showEvent(self, event):
        """Refresh state when page becomes visible."""
        super().showEvent(event)
        self.refresh_state()
