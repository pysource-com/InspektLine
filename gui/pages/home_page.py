"""Home page — camera feed with inspection controls always visible."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QSizePolicy, QComboBox, QSpinBox,
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
        self.task_type_combo = None
        self.model_variant_combo = None
        self.model_variant_label = None
        self.detection_count_label = None

        # Dataset collection UI references
        self.collection_mode_combo = None
        self.frame_skip_spin = None
        self.frame_skip_label = None
        self.output_dir_label = None
        self.collection_btn = None
        self.collection_status_label = None
        self._output_dir = "storage/dataset"

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

        info_layout.addStretch()

        fps_icon = QLabel("FPS:")
        fps_icon.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; border: none;"
        )
        info_layout.addWidget(fps_icon)

        self.fps_value = QLabel("—")
        self.fps_value.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 11px; font-weight: bold; border: none;"
        )
        info_layout.addWidget(self.fps_value)

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
        model_section_title = QLabel("Model")
        model_section_title.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; "
            f"font-weight: bold; border: none;"
        )
        layout.addWidget(model_section_title)

        # Shared combo style
        combo_style = f"""
            QComboBox {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border-color: {DarkTheme.BORDER_SECONDARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                selection-background-color: {DarkTheme.PRIMARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """

        # Task type selector
        type_label = QLabel("Task")
        type_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
        )
        layout.addWidget(type_label)

        self.task_type_combo = QComboBox()
        self.task_type_combo.addItems(["Classification", "Detection", "Segmentation"])
        self.task_type_combo.setFixedHeight(36)
        self.task_type_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.task_type_combo.setStyleSheet(combo_style)
        self.task_type_combo.currentIndexChanged.connect(self._on_task_type_changed)
        layout.addWidget(self.task_type_combo)

        # Model variant selector (visible for detection / segmentation)
        self.model_variant_label = QLabel("Model")
        self.model_variant_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
        )
        self.model_variant_label.setVisible(False)
        layout.addWidget(self.model_variant_label)

        self.model_variant_combo = QComboBox()
        self.model_variant_combo.setFixedHeight(36)
        self.model_variant_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_variant_combo.setStyleSheet(combo_style)
        self.model_variant_combo.setVisible(False)
        layout.addWidget(self.model_variant_combo)

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

        # Detection count (visible during RF-DETR inspection)
        self.detection_count_label = QLabel("")
        self.detection_count_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
        )
        self.detection_count_label.setVisible(False)
        layout.addWidget(self.detection_count_label)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {DarkTheme.BORDER_PRIMARY}; border: none; background: {DarkTheme.BORDER_PRIMARY}; max-height: 1px;")
        layout.addWidget(sep2)

        # --- Dataset Collection section ---
        dataset_title = QLabel("Dataset Collection")
        dataset_title.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; "
            f"font-weight: bold; border: none;"
        )
        layout.addWidget(dataset_title)

        # Mode selector
        mode_label = QLabel("Mode")
        mode_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
        )
        layout.addWidget(mode_label)

        self.collection_mode_combo = QComboBox()
        self.collection_mode_combo.addItems(["Save Images", "Record Video"])
        self.collection_mode_combo.setFixedHeight(36)
        self.collection_mode_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collection_mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border-color: {DarkTheme.BORDER_SECONDARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                selection-background-color: {DarkTheme.PRIMARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)
        self.collection_mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        layout.addWidget(self.collection_mode_combo)

        # Frame skip (only visible in image mode)
        self.frame_skip_label = QLabel("Save every N frames")
        self.frame_skip_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
        )
        layout.addWidget(self.frame_skip_label)

        self.frame_skip_spin = QSpinBox()
        self.frame_skip_spin.setMinimum(1)
        self.frame_skip_spin.setMaximum(1000)
        self.frame_skip_spin.setValue(5)
        self.frame_skip_spin.setFixedHeight(36)
        self.frame_skip_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QSpinBox:hover {{
                border-color: {DarkTheme.BORDER_SECONDARY};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {DarkTheme.BG_HOVER};
                border: none;
                width: 20px;
            }}
        """)
        layout.addWidget(self.frame_skip_spin)

        # Output directory picker
        output_dir_row = QHBoxLayout()
        output_dir_row.setSpacing(8)

        self.output_dir_label = QLabel("storage/dataset")
        self.output_dir_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; border: none;"
        )
        self.output_dir_label.setWordWrap(True)
        output_dir_row.addWidget(self.output_dir_label, stretch=1)

        browse_btn = QPushButton("📁")
        browse_btn.setFixedSize(36, 36)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setToolTip("Choose output folder")
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 6px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
            }}
        """)
        browse_btn.clicked.connect(self._browse_output_dir)
        output_dir_row.addWidget(browse_btn)

        layout.addLayout(output_dir_row)

        # Collection status
        self.collection_status_label = QLabel("Ready")
        self.collection_status_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
        )
        layout.addWidget(self.collection_status_label)

        # Start / Stop Collection button
        self.collection_btn = QPushButton("⏺  Start Collection")
        self.collection_btn.setFixedHeight(44)
        self.collection_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collection_btn.setStyleSheet(f"""
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
        self.collection_btn.clicked.connect(self._toggle_collection)
        layout.addWidget(self.collection_btn)

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
        """Open file dialog to select a model directory or checkpoint file."""
        task_index = self.task_type_combo.currentIndex()
        # 0 = Classification, 1 = Detection, 2 = Segmentation
        task_type = ["classification", "detection", "segmentation"][task_index]

        if task_type == "classification":
            # Classifier: pick a HuggingFace model directory
            model_path = QFileDialog.getExistingDirectory(
                self, "Select Model Directory", "",
            )
        else:
            # RF-DETR / RF-DETRSeg: pick a .pth checkpoint file
            model_path, _ = QFileDialog.getOpenFileName(
                self, "Select Checkpoint", "",
                "PyTorch Checkpoint (*.pth *.pt);;All Files (*)",
            )

        if not model_path:
            return

        if self.parent_window and hasattr(self.parent_window, "inspection_service"):
            # Store task + variant in settings before loading
            settings_svc = getattr(self.parent_window, "settings_service", None)
            if settings_svc:
                settings_svc.detection.task_type = task_type
                if task_type != "classification":
                    settings_svc.detection.model_variant = (
                        self.model_variant_combo.currentText()
                    )

            success = self.parent_window.inspection_service.load_model(model_path)
            if success:
                short_name = model_path.replace("\\", "/").split("/")[-1]
                if task_type == "classification":
                    tag = "Classifier"
                else:
                    tag = self.model_variant_combo.currentText()
                self.model_path_label.setText(model_path)
                self.model_status.setText(f"{tag}: {short_name}")
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

    def _on_task_type_changed(self, index: int):
        """Populate model variant combo based on the selected task type."""
        # 0 = Classification, 1 = Detection, 2 = Segmentation
        show_variant = index > 0
        self.model_variant_label.setVisible(show_variant)
        self.model_variant_combo.setVisible(show_variant)

        if not show_variant:
            return

        from detector.rfdetr_detector import RFDETRDetector

        self.model_variant_combo.blockSignals(True)
        self.model_variant_combo.clear()

        if index == 1:  # Detection
            self.model_variant_combo.addItems(RFDETRDetector.DETECTION_MODELS)
        elif index == 2:  # Segmentation
            self.model_variant_combo.addItems(RFDETRDetector.SEGMENTATION_MODELS)

        self.model_variant_combo.blockSignals(False)

    def update_detection_count(self, count: int):
        """Called from MainWindow to update the live detection counter."""
        if self.detection_count_label is not None:
            self.detection_count_label.setVisible(True)
            self.detection_count_label.setText(f"Detections: {count}")

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
            self.detection_count_label.setVisible(False)
        else:
            svc.start()
            self.start_inspection_btn.setText("⏹  Stop Inspection")
            self.inspection_label.setText("Inspection running…")
            self.inspection_label.setStyleSheet(
                f"color: {DarkTheme.SUCCESS}; font-size: 12px; border: none;"
            )
            if svc.task_type in ("detection", "segmentation"):
                self.detection_count_label.setVisible(True)
                self.detection_count_label.setText("Detections: 0")

    # ================================================================
    # Dataset Collection
    # ================================================================

    def _on_mode_changed(self, index: int):
        """Show/hide the frame-skip spinner depending on the selected mode."""
        is_image_mode = index == 0  # "Save Images" is first
        self.frame_skip_spin.setVisible(is_image_mode)
        self.frame_skip_label.setVisible(is_image_mode)

    def _browse_output_dir(self):
        """Open folder picker for the dataset output directory."""
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self._output_dir,
        )
        if chosen:
            self._output_dir = chosen
            self.output_dir_label.setText(chosen)

    def _toggle_collection(self):
        """Start or stop dataset collection."""
        if not self.parent_window or not hasattr(self.parent_window, "dataset_service"):
            return

        svc = self.parent_window.dataset_service

        if svc.is_collecting:
            svc.stop_collection()
            self.collection_btn.setText("⏺  Start Collection")
            self.collection_btn.setStyleSheet(f"""
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
            self.collection_status_label.setText(
                f"Done — {svc.frames_saved} frames saved"
            )
            self.collection_status_label.setStyleSheet(
                f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; border: none;"
            )
            # Re-enable controls
            self.collection_mode_combo.setEnabled(True)
            self.frame_skip_spin.setEnabled(True)
        else:
            mode = "images" if self.collection_mode_combo.currentIndex() == 0 else "video"
            frame_skip = self.frame_skip_spin.value()

            ok = svc.start_collection(
                output_dir=self._output_dir,
                mode=mode,
                frame_skip=frame_skip,
            )
            if not ok:
                self.collection_status_label.setText("Failed to start collection")
                self.collection_status_label.setStyleSheet(
                    f"color: {DarkTheme.ERROR}; font-size: 12px; border: none;"
                )
                return

            self.collection_btn.setText("⏹  Stop Collection")
            self.collection_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {DarkTheme.ERROR};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0 20px;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {DarkTheme.ERROR_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {DarkTheme.ERROR_PRESSED};
                }}
            """)
            label = "Recording video…" if mode == "video" else "Capturing images…"
            self.collection_status_label.setText(label)
            self.collection_status_label.setStyleSheet(
                f"color: {DarkTheme.SUCCESS}; font-size: 12px; border: none;"
            )
            # Disable controls while collecting
            self.collection_mode_combo.setEnabled(False)
            self.frame_skip_spin.setEnabled(False)

    def update_collection_status(self, frames_saved: int):
        """Called from MainWindow on each frame to update the counter."""
        if self.collection_status_label is None:
            return
        svc = self.parent_window.dataset_service if self.parent_window else None
        if svc and svc.is_collecting:
            if svc.mode == "video":
                self.collection_status_label.setText(
                    f"Recording… {frames_saved} frames"
                )
            else:
                self.collection_status_label.setText(
                    f"Capturing… {frames_saved} images saved"
                )

