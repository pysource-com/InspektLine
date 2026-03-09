"""Home page — focused on real-time defect inspection."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from gui.styles.themes import DarkTheme


class HomePage(QWidget):
    """Home page for the real-time inspection workflow."""

    # Signals for navigation
    navigate_to_settings = Signal()
    navigate_to_camera = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # UI element references
        self.model_status = None
        self.model_path_label = None
        self.start_inspection_btn = None
        self.load_model_btn = None

        self.init_ui()

    def init_ui(self):
        """Initialize the home page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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

        main_layout.addWidget(content_widget)

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

        # Title and model status
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Visual Inspection System")
        title.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 18px; "
            f"font-weight: bold; border: none; background: transparent;"
        )
        title_layout.addWidget(title)

        self.model_status = QLabel("No model loaded")
        self.model_status.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
        )
        title_layout.addWidget(self.model_status)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Camera button
        camera_btn = QPushButton("📹  Camera Feed")
        camera_btn.setFixedHeight(36)
        camera_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        camera_btn.setStyleSheet(f"""
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
        camera_btn.clicked.connect(self.navigate_to_camera.emit)
        layout.addWidget(camera_btn)

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

        camera_icon = QLabel("🔍")
        camera_icon.setStyleSheet("font-size: 40px; background: transparent;")
        camera_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(camera_icon)

        layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(24)

        # Title
        title = QLabel("Real-Time Defect Inspection")
        title.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 28px; font-weight: bold;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Load a detection model and start inspecting products in real-time.")
        subtitle.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 14px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(500)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(32)

        # Model card
        model_card = self._create_model_card()
        layout.addWidget(model_card, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(32)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Load Model button
        self.load_model_btn = QPushButton("📂  Load Model")
        self.load_model_btn.setFixedHeight(50)
        self.load_model_btn.setMinimumWidth(180)
        self.load_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_model_btn.setStyleSheet(f"""
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
        self.load_model_btn.clicked.connect(self._load_model)
        buttons_layout.addWidget(self.load_model_btn)

        # Start Inspection button
        self.start_inspection_btn = QPushButton("▶  Start Inspection")
        self.start_inspection_btn.setFixedHeight(50)
        self.start_inspection_btn.setMinimumWidth(200)
        self.start_inspection_btn.setEnabled(False)
        self.start_inspection_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.start_inspection_btn.clicked.connect(self._toggle_inspection)
        buttons_layout.addWidget(self.start_inspection_btn)

        layout.addLayout(buttons_layout)

        layout.addStretch()

        return content

    def _create_model_card(self) -> QFrame:
        """Create a card showing current model status."""
        card = QFrame()
        card.setFixedWidth(450)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 10px;
                padding: 20px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Brain icon
        icon_label = QLabel("🧠")
        icon_label.setStyleSheet("font-size: 36px; border: none;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)

        # Model path label
        self.model_path_label = QLabel("No model loaded")
        self.model_path_label.setStyleSheet(
            f"font-size: 14px; color: {DarkTheme.TEXT_SECONDARY}; border: none;"
        )
        self.model_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.model_path_label.setWordWrap(True)
        card_layout.addWidget(self.model_path_label)

        return card

    # ================================================================
    # Actions
    # ================================================================

    def _load_model(self):
        """Open file dialog to select a model directory or file."""
        model_path = QFileDialog.getExistingDirectory(
            self, "Select Model Directory", "",
        )
        if not model_path:
            return

        if self.parent_window and hasattr(self.parent_window, "inspection_service"):
            success = self.parent_window.inspection_service.load_model(model_path)
            if success:
                self.model_path_label.setText(model_path)
                self.model_status.setText(f"Model: {model_path.split('/')[-1]}")
                self.model_status.setStyleSheet(
                    f"color: {DarkTheme.SUCCESS}; font-size: 12px; border: none;"
                )
                self.start_inspection_btn.setEnabled(True)
            else:
                self.model_path_label.setText("Failed to load model")
                self.model_path_label.setStyleSheet(
                    f"font-size: 14px; color: {DarkTheme.DANGER}; border: none;"
                )

    def _toggle_inspection(self):
        """Start or stop real-time inspection."""
        if not self.parent_window or not hasattr(self.parent_window, "inspection_service"):
            return

        svc = self.parent_window.inspection_service
        if svc.is_running:
            svc.stop()
            self.start_inspection_btn.setText("▶  Start Inspection")
        else:
            svc.start()
            self.start_inspection_btn.setText("⏹  Stop Inspection")
