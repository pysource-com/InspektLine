"""Home page — camera feed with inspection controls always visible."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from gui.components import VideoLabel
from gui.styles.themes import DarkTheme


class HomePage(QWidget):
    """Home page showing real-time camera feed with inspection controls."""

    # Signals for navigation
    navigate_to_settings = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # UI element references
        self.video_label = None
        self.model_status = None
        self.model_path_label = None
        self.start_inspection_btn = None
        self.load_model_btn = None
        self.resolution_value = None
        self.inspection_label = None

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

        # Main content: camera feed + side panel
        body = self._create_body()
        content_layout.addWidget(body, stretch=1)

        main_layout.addWidget(content_widget)

    def _create_header(self) -> QWidget:
        """Create the header bar."""
        header = QWidget()
        header.setFixedHeight(60)
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

        title = QLabel("InspektLine")
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

    def _create_body(self) -> QWidget:
        """Create the body: camera feed on the left, controls on the right."""
        body = QWidget()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # --- Camera feed area (takes most space) ---
        camera_container = self._create_camera_area()
        layout.addWidget(camera_container, stretch=3)

        # --- Right side panel with controls ---
        side_panel = self._create_side_panel()
        layout.addWidget(side_panel, stretch=1)

        return body

    def _create_camera_area(self) -> QWidget:
        """Create the camera feed display area."""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Video label for real-time feed
        self.video_label = VideoLabel()
        self.video_label.setMinimumSize(640, 360)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.video_label, stretch=1)

        # Info bar below video
        info_bar = QWidget()
        info_bar.setMaximumHeight(32)
        info_bar.setStyleSheet(
            "background-color: rgba(0, 0, 0, 180); border-radius: 4px;"
        )
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(12, 4, 12, 4)
        info_layout.setSpacing(16)

        res_label = QLabel("Resolution:")
        res_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; border: none;")
        info_layout.addWidget(res_label)

        self.resolution_value = QLabel("—")
        self.resolution_value.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 11px; font-weight: bold; border: none;"
        )
        info_layout.addWidget(self.resolution_value)

        layout.addWidget(info_bar)

        return container

    def _create_side_panel(self) -> QWidget:
        """Create the right-side control panel."""
        panel = QWidget()
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(360)
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # --- Model section ---
        model_section_title = QLabel("Detection Model")
        model_section_title.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; "
            f"font-weight: bold; border: none;"
        )
        layout.addWidget(model_section_title)

        # Model card
        model_card = self._create_model_card()
        layout.addWidget(model_card)

        # Load Model button
        self.load_model_btn = QPushButton("📂  Load Model")
        self.load_model_btn.setFixedHeight(44)
        self.load_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_model_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
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
        layout.addWidget(self.load_model_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {DarkTheme.BORDER_PRIMARY}; border: none; background: {DarkTheme.BORDER_PRIMARY}; max-height: 1px;")
        layout.addWidget(sep)

        # --- Inspection section ---
        inspection_title = QLabel("Inspection")
        inspection_title.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; "
            f"font-weight: bold; border: none;"
        )
        layout.addWidget(inspection_title)

        # Inspection status label
        self.inspection_label = QLabel("Load a model to begin inspection")
        self.inspection_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
        )
        self.inspection_label.setWordWrap(True)
        layout.addWidget(self.inspection_label)

        # Start Inspection button
        self.start_inspection_btn = QPushButton("▶  Start Inspection")
        self.start_inspection_btn.setFixedHeight(50)
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
                font-weight: bold;
            }}
            QPushButton:enabled:hover {{
                background-color: {DarkTheme.SUCCESS_HOVER};
            }}
        """)
        self.start_inspection_btn.clicked.connect(self._toggle_inspection)
        layout.addWidget(self.start_inspection_btn)

        layout.addStretch()


        return panel

    def _create_model_card(self) -> QFrame:
        """Create a card showing current model status."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_CARD};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(12, 10, 12, 10)

        # Brain icon
        icon_label = QLabel("🧠")
        icon_label.setStyleSheet("font-size: 24px; border: none;")
        card_layout.addWidget(icon_label)

        # Model path label
        self.model_path_label = QLabel("No model loaded")
        self.model_path_label.setStyleSheet(
            f"font-size: 12px; color: {DarkTheme.TEXT_SECONDARY}; border: none;"
        )
        self.model_path_label.setWordWrap(True)
        card_layout.addWidget(self.model_path_label, stretch=1)

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
                short_name = model_path.replace("\\", "/").split("/")[-1]
                self.model_path_label.setText(model_path)
                self.model_status.setText(f"Model: {short_name}")
                self.model_status.setStyleSheet(
                    f"color: {DarkTheme.SUCCESS}; font-size: 12px; border: none;"
                )
                self.inspection_label.setText("Model loaded — ready to inspect")
                self.inspection_label.setStyleSheet(
                    f"color: {DarkTheme.SUCCESS}; font-size: 12px; border: none;"
                )
                self.start_inspection_btn.setEnabled(True)
            else:
                self.model_path_label.setText("Failed to load model")
                self.model_path_label.setStyleSheet(
                    f"font-size: 12px; color: {DarkTheme.ERROR}; border: none;"
                )

    def _toggle_inspection(self):
        """Start or stop real-time inspection."""
        if not self.parent_window or not hasattr(self.parent_window, "inspection_service"):
            return

        svc = self.parent_window.inspection_service
        if svc.is_running:
            svc.stop()
            self.start_inspection_btn.setText("▶  Start Inspection")
            self.inspection_label.setText("Inspection stopped")
            self.inspection_label.setStyleSheet(
                f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
            )
        else:
            svc.start()
            self.start_inspection_btn.setText("⏹  Stop Inspection")
            self.inspection_label.setText("Inspection running…")
            self.inspection_label.setStyleSheet(
                f"color: {DarkTheme.SUCCESS}; font-size: 12px; border: none;"
            )
