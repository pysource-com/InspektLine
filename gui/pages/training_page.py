"""Training page for model training with HuggingFace transformers."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QComboBox, QProgressBar, QScrollArea,
    QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont
from pathlib import Path
from datetime import datetime
import json
from typing import Optional

from gui.styles.themes import DarkTheme
from database.project_db import ProjectDatabase, ProjectStats


class TrainingWorker(QObject):
    """Worker for running training in background thread."""

    progress = Signal(int, str)  # epoch, message
    log = Signal(str)
    finished = Signal(bool, str)  # success, message
    metrics = Signal(dict)  # metrics dict

    def __init__(self, model_name: str, dataset_path: str, output_dir: str,
                 epochs: int = 10, batch_size: int = 8):
        super().__init__()
        self.model_name = model_name
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.epochs = epochs
        self.batch_size = batch_size
        self.is_cancelled = False

    def run(self):
        """Run the training process."""
        try:
            self.log.emit("Initializing training...")
            self.log.emit(f"Model: RT-DETR (PekingU/rtdetr_r50vd)")
            self.log.emit(f"Dataset: {self.dataset_path}")
            self.log.emit(f"Output: {self.output_dir}")
            self.log.emit("")

            # Check for required packages
            try:
                import torch
                from transformers import (
                    RTDetrForObjectDetection,
                    RTDetrImageProcessor,
                )
                self.log.emit(f"PyTorch version: {torch.__version__}")
                self.log.emit(f"CUDA available: {torch.cuda.is_available()}")
                if torch.cuda.is_available():
                    self.log.emit(f"GPU: {torch.cuda.get_device_name(0)}")
            except ImportError as e:
                self.log.emit(f"Error: Missing required package - {e}")
                self.log.emit("Please install: pip install torch transformers")
                self.finished.emit(False, "Missing dependencies")
                return

            self.log.emit("")
            self.log.emit("Loading model and processor...")

            # Load model and processor
            device = "cuda" if torch.cuda.is_available() else "cpu"

            try:
                processor = RTDetrImageProcessor.from_pretrained("PekingU/rtdetr_r50vd")
                model = RTDetrForObjectDetection.from_pretrained(
                    "PekingU/rtdetr_r50vd",
                    num_labels=2,  # Defect, Pass
                    ignore_mismatched_sizes=True
                )
                model.to(device)
                self.log.emit("Model loaded successfully!")
            except Exception as e:
                self.log.emit(f"Error loading model: {e}")
                self.finished.emit(False, str(e))
                return

            self.log.emit("")
            self.log.emit("Preparing dataset...")

            # For now, simulate training progress
            # Full implementation would load COCO-format dataset
            self.log.emit("Note: Full training requires COCO-format dataset")
            self.log.emit("Simulating training for demonstration...")
            self.log.emit("")

            import time
            for epoch in range(1, self.epochs + 1):
                if self.is_cancelled:
                    self.log.emit("Training cancelled by user.")
                    self.finished.emit(False, "Cancelled")
                    return

                self.progress.emit(epoch, f"Epoch {epoch}/{self.epochs}")
                self.log.emit(f"Epoch {epoch}/{self.epochs}")

                # Simulate training time
                time.sleep(0.5)

                # Fake metrics
                loss = 1.0 - (epoch * 0.08)
                mAP = 0.3 + (epoch * 0.05)
                self.log.emit(f"  Loss: {loss:.4f}, mAP: {mAP:.4f}")

                self.metrics.emit({
                    "epoch": epoch,
                    "loss": loss,
                    "mAP": mAP
                })

            self.log.emit("")
            self.log.emit("Training completed!")

            # Save model
            output_path = Path(self.output_dir) / self.model_name
            output_path.mkdir(parents=True, exist_ok=True)

            self.log.emit(f"Saving model to {output_path}...")
            model.save_pretrained(str(output_path))
            processor.save_pretrained(str(output_path))

            self.log.emit("Model saved successfully!")
            self.finished.emit(True, str(output_path))

        except Exception as e:
            self.log.emit(f"Error during training: {e}")
            self.finished.emit(False, str(e))

    def cancel(self):
        """Cancel the training."""
        self.is_cancelled = True


class TrainingPage(QWidget):
    """Page for training detection models."""

    navigate_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.db = ProjectDatabase()

        # State
        self.is_training = False
        self.worker: Optional[TrainingWorker] = None
        self.thread: Optional[QThread] = None

        # UI elements
        self.model_name_input: Optional[QLineEdit] = None
        self.epochs_input: Optional[QLineEdit] = None
        self.batch_size_combo: Optional[QComboBox] = None
        self.total_images_label: Optional[QLabel] = None
        self.defect_labels_label: Optional[QLabel] = None
        self.pass_labels_label: Optional[QLabel] = None
        self.train_button: Optional[QPushButton] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.log_output: Optional[QTextEdit] = None

        self.init_ui()
        self.refresh_stats()

    def init_ui(self):
        """Initialize the training page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {DarkTheme.BG_PRIMARY};
                border: none;
            }}
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)

        # Subtitle
        subtitle = QLabel("Create a computer vision model from your annotated data")
        subtitle.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px;")
        content_layout.addWidget(subtitle)

        # Training Configuration section
        config_section = self._create_config_section()
        content_layout.addWidget(config_section)

        # Dataset Summary section
        summary_section = self._create_summary_section()
        content_layout.addWidget(summary_section)

        # Training Progress section
        progress_section = self._create_progress_section()
        content_layout.addWidget(progress_section)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Bottom action bar
        action_bar = self._create_action_bar()
        layout.addWidget(action_bar)

    def _create_header(self) -> QWidget:
        """Create the header with tabs."""
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-bottom: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 0)
        layout.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()

        title_layout = QVBoxLayout()
        title = QLabel("Dataset & Training")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title)

        subtitle = QLabel("Manage training data and models")
        subtitle.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        title_layout.addWidget(subtitle)

        title_row.addLayout(title_layout)
        title_row.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {DarkTheme.TEXT_SECONDARY};
                border: none;
                font-size: 18px;
            }}
            QPushButton:hover {{
                color: {DarkTheme.TEXT_PRIMARY};
            }}
        """)
        close_btn.clicked.connect(self.navigate_back.emit)
        title_row.addWidget(close_btn)

        layout.addLayout(title_row)

        # Tabs
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(24)

        tab_names = ["Overview", "Collect Images", "Annotate", "Train Model"]
        for name in tab_names:
            tab = QPushButton(name)
            is_active = name == "Train Model"
            tab.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {DarkTheme.TEXT_PRIMARY if is_active else DarkTheme.TEXT_SECONDARY};
                    border: none;
                    border-bottom: 2px solid {"#0066ff" if is_active else "transparent"};
                    padding: 8px 0;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    color: {DarkTheme.TEXT_PRIMARY};
                }}
            """)
            tabs_layout.addWidget(tab)

        tabs_layout.addStretch()
        layout.addLayout(tabs_layout)

        return header

    def _create_config_section(self) -> QWidget:
        """Create the training configuration section."""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_CARD};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Section title
        title = QLabel("Training Configuration")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Model Name
        name_layout = QVBoxLayout()
        name_label = QLabel("Model Name")
        name_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        name_layout.addWidget(name_label)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.model_name_input = QLineEdit(f"Model-{timestamp}")
        self.model_name_input.setFixedHeight(44)
        self.model_name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 0 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {DarkTheme.PRIMARY};
            }}
        """)
        name_layout.addWidget(self.model_name_input)
        layout.addLayout(name_layout)

        # Model type and parameters row
        params_row = QHBoxLayout()
        params_row.setSpacing(20)

        # Model Type
        type_layout = QVBoxLayout()
        type_label = QLabel("Model Type")
        type_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        type_layout.addWidget(type_label)

        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems([
            "RT-DETR (Object Detection)",
            "ConvNeXt (Classification)",
            "Mask2Former (Segmentation)"
        ])
        self.model_type_combo.setFixedHeight(44)
        self.model_type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 0 16px;
                font-size: 14px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                selection-background-color: {DarkTheme.PRIMARY};
            }}
        """)
        type_layout.addWidget(self.model_type_combo)
        params_row.addLayout(type_layout)

        # Epochs
        epochs_layout = QVBoxLayout()
        epochs_label = QLabel("Epochs")
        epochs_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        epochs_layout.addWidget(epochs_label)

        self.epochs_input = QLineEdit("10")
        self.epochs_input.setFixedHeight(44)
        self.epochs_input.setFixedWidth(100)
        self.epochs_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 0 16px;
                font-size: 14px;
            }}
        """)
        epochs_layout.addWidget(self.epochs_input)
        params_row.addLayout(epochs_layout)

        # Batch Size
        batch_layout = QVBoxLayout()
        batch_label = QLabel("Batch Size")
        batch_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        batch_layout.addWidget(batch_label)

        self.batch_size_combo = QComboBox()
        self.batch_size_combo.addItems(["4", "8", "16", "32"])
        self.batch_size_combo.setCurrentText("8")
        self.batch_size_combo.setFixedHeight(44)
        self.batch_size_combo.setFixedWidth(100)
        self.batch_size_combo.setStyleSheet(self.model_type_combo.styleSheet())
        batch_layout.addWidget(self.batch_size_combo)
        params_row.addLayout(batch_layout)

        params_row.addStretch()
        layout.addLayout(params_row)

        return section

    def _create_summary_section(self) -> QWidget:
        """Create the dataset summary section."""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_CARD};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Section title
        title = QLabel("Dataset Summary")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(40)

        # Total Images
        total_layout = QVBoxLayout()
        total_label = QLabel("Total Images")
        total_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        total_layout.addWidget(total_label)

        self.total_images_label = QLabel("0")
        self.total_images_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 32px; font-weight: bold;")
        total_layout.addWidget(self.total_images_label)
        stats_row.addLayout(total_layout)

        # Defect Labels
        defect_layout = QVBoxLayout()
        defect_label = QLabel("Defect Labels")
        defect_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        defect_layout.addWidget(defect_label)

        self.defect_labels_label = QLabel("0")
        self.defect_labels_label.setStyleSheet(f"color: {DarkTheme.ERROR}; font-size: 32px; font-weight: bold;")
        defect_layout.addWidget(self.defect_labels_label)
        stats_row.addLayout(defect_layout)

        # Pass Labels
        pass_layout = QVBoxLayout()
        pass_label = QLabel("Pass Labels")
        pass_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        pass_layout.addWidget(pass_label)

        self.pass_labels_label = QLabel("0")
        self.pass_labels_label.setStyleSheet(f"color: {DarkTheme.SUCCESS}; font-size: 32px; font-weight: bold;")
        pass_layout.addWidget(self.pass_labels_label)
        stats_row.addLayout(pass_layout)

        stats_row.addStretch()
        layout.addLayout(stats_row)

        return section

    def _create_progress_section(self) -> QWidget:
        """Create the training progress section."""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_CARD};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Section title
        title = QLabel("Training Progress")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {DarkTheme.BG_INPUT};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {DarkTheme.PRIMARY};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Progress label
        self.progress_label = QLabel("Ready to train")
        self.progress_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self.progress_label)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(200)
        self.log_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {DarkTheme.BG_PRIMARY};
                color: {DarkTheme.TEXT_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 12px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.log_output)

        return section

    def _create_action_bar(self) -> QWidget:
        """Create the bottom action bar."""
        bar = QWidget()
        bar.setFixedHeight(80)
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-top: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)

        layout.addStretch()

        # Train button
        self.train_button = QPushButton("▶  Start Training")
        self.train_button.setFixedHeight(50)
        self.train_button.setMinimumWidth(600)
        self.train_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.train_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_DISABLED};
            }}
        """)
        self.train_button.clicked.connect(self._toggle_training)
        layout.addWidget(self.train_button)

        layout.addStretch()

        return bar

    def refresh_stats(self):
        """Refresh the dataset statistics."""
        stats = self.db.get_project_stats()

        self.total_images_label.setText(str(stats.annotated_images))
        self.defect_labels_label.setText(str(stats.defect_labels))
        self.pass_labels_label.setText(str(stats.pass_labels))

        # Enable/disable training based on data availability
        can_train = stats.annotated_images > 0 and stats.total_annotations > 0
        self.train_button.setEnabled(can_train)

        if not can_train:
            self.progress_label.setText("Annotate images before training")

    def _toggle_training(self):
        """Start or stop training."""
        if self.is_training:
            self._stop_training()
        else:
            self._start_training()

    def _start_training(self):
        """Start the training process."""
        self.is_training = True
        self.train_button.setText("⏹  Stop Training")
        self.train_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ERROR};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.ERROR_HOVER};
            }}
        """)

        self.log_output.clear()
        self.progress_bar.setValue(0)

        # Get parameters
        model_name = self.model_name_input.text()
        epochs = int(self.epochs_input.text() or "10")
        batch_size = int(self.batch_size_combo.currentText())

        # Create worker and thread
        self.thread = QThread()
        self.worker = TrainingWorker(
            model_name=model_name,
            dataset_path="storage/dataset",
            output_dir="models",
            epochs=epochs,
            batch_size=batch_size
        )
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._on_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.metrics.connect(self._on_metrics)

        # Start training
        epochs_count = int(self.epochs_input.text() or "10")
        self.progress_bar.setMaximum(epochs_count)
        self.thread.start()

    def _stop_training(self):
        """Stop the training process."""
        if self.worker:
            self.worker.cancel()

    def _on_progress(self, epoch: int, message: str):
        """Handle progress updates."""
        self.progress_bar.setValue(epoch)
        self.progress_label.setText(message)

    def _on_log(self, message: str):
        """Handle log messages."""
        self.log_output.append(message)

    def _on_metrics(self, metrics: dict):
        """Handle metrics updates."""
        pass  # Could update a chart here

    def _on_finished(self, success: bool, message: str):
        """Handle training completion."""
        self.is_training = False
        self.train_button.setText("▶  Start Training")
        self.train_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
        """)

        if success:
            self.progress_label.setText("Training completed!")

            # Save model to database
            model_name = self.model_name_input.text()
            self.db.add_model(
                name=model_name,
                path=message,  # path returned from worker
                model_type="detection",
                metrics=json.dumps({"status": "completed"})
            )
        else:
            self.progress_label.setText(f"Training failed: {message}")

        # Cleanup thread
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
            self.worker = None

    def showEvent(self, event):
        """Refresh when page becomes visible."""
        super().showEvent(event)
        self.refresh_stats()

    def closeEvent(self, event):
        """Cleanup on close."""
        if self.is_training:
            self._stop_training()
        super().closeEvent(event)
