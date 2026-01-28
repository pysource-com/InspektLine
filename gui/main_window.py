"""Main window for InspektLine GUI using modular architecture."""

import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QFrame, QStackedWidget)
from PySide6.QtCore import QTimer, Qt

from camera.camera import Camera
from database.project_db import ProjectDatabase
from gui.components import SidebarButton
from gui.pages import (CameraPage, DatasetPage, SettingsPage, HomePage,
                       AnnotatorPage, TrainingPage)
from gui.styles import DarkTheme


class MainWindow(QMainWindow):
    """Main application window with left sidebar and modular pages."""

    # Page indices
    PAGE_HOME = 0
    PAGE_CAMERA = 1
    PAGE_DATASET = 2
    PAGE_ANNOTATE = 3
    PAGE_TRAIN = 4
    PAGE_SETTINGS = 5

    def __init__(self, camera_index=0, camera_type="usb-standard"):
        """
        Initialize the main window.

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
        self.current_page = "home"
        self.current_frame = None

        # Database
        self.db = ProjectDatabase()

        # Camera info tracking
        self.frame_count = 0
        self.fps_update_counter = 0
        self.fps_update_interval = 10

        # Settings values
        self.confidence_threshold = 85
        self.min_defect_size = 10
        self.auto_focus_enabled = False
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

        # Store sidebar buttons for group management
        self.sidebar_buttons = []

        self.init_ui()
        self.start_video()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("InspektLine - Visual Inspection System")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(DarkTheme.get_main_window_style())

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

        # Initialize pages
        self.setup_pages()

        # Set HomePage as default
        self.stacked_widget.setCurrentIndex(self.PAGE_HOME)

        main_layout.addWidget(self.stacked_widget, stretch=1)

    def setup_pages(self):
        """Set up all application pages."""
        # PAGE 0: Home page
        self.home_page = HomePage(parent=self)
        self.home_page.navigate_to_capture.connect(lambda: self.switch_to_page(self.PAGE_DATASET))
        self.home_page.navigate_to_annotate.connect(lambda: self.switch_to_page(self.PAGE_ANNOTATE))
        self.home_page.navigate_to_train.connect(lambda: self.switch_to_page(self.PAGE_TRAIN))
        self.home_page.navigate_to_settings.connect(lambda: self.switch_to_page(self.PAGE_SETTINGS))
        self.home_page.navigate_to_dataset.connect(lambda: self.switch_to_page(self.PAGE_DATASET))
        self.stacked_widget.addWidget(self.home_page)

        # PAGE 1: Camera feed page
        self.camera_page = CameraPage(parent=self)
        self.stacked_widget.addWidget(self.camera_page)

        # PAGE 2: Dataset collection page
        self.dataset_page = DatasetPage(parent=self)
        self.stacked_widget.addWidget(self.dataset_page)

        # PAGE 3: Annotator page
        self.annotator_page = AnnotatorPage(parent=self)
        self.annotator_page.navigate_back.connect(lambda: self.switch_to_page(self.PAGE_HOME))
        self.stacked_widget.addWidget(self.annotator_page)

        # PAGE 4: Training page
        self.training_page = TrainingPage(parent=self)
        self.training_page.navigate_back.connect(lambda: self.switch_to_page(self.PAGE_HOME))
        self.stacked_widget.addWidget(self.training_page)

        # PAGE 5: Settings page
        self.settings_page = SettingsPage(parent=self)
        self.stacked_widget.addWidget(self.settings_page)

    def create_sidebar(self):
        """Create the left sidebar with navigation buttons."""
        sidebar = QFrame()
        sidebar.setFixedWidth(100)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-right: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

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

        # Handle page-specific logic
        if page_index == self.PAGE_DATASET:
            self.is_capturing = True
            # Load existing images on first visit to dataset page
            if not self.gallery_loaded and hasattr(self.dataset_page, 'load_existing_samples'):
                self.dataset_page.load_existing_samples()
                self.gallery_loaded = True
        else:
            self.is_capturing = False

        # Refresh home page when navigating to it
        if page_index == self.PAGE_HOME and hasattr(self.home_page, 'refresh_state'):
            self.home_page.refresh_state()

    # ========================
    # Camera Methods
    # ========================

    def start_video(self):
        """Start capturing and displaying video."""
        if self.cap is None:
            try:
                print(f"Loading camera: index={self.camera_index}, type={self.camera_type}")
                self.cap = self.camera.load_cap(self.camera_index, self.camera_type)
                print("Camera loaded successfully")
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
            self.timer.start(30)

    def stop_video(self):
        """Stop capturing and displaying video."""
        if self.timer is not None and self.timer.isActive():
            self.timer.stop()

    def update_frame(self):
        """Read and display the next video frame."""
        if self.cap is not None:
            ret, frame = self.camera.read_frame(self.cap)

            if ret:
                # Store the current frame
                self.current_frame = frame.copy()
                self.frame_count += 1

                # Update camera page video label
                if hasattr(self.camera_page, 'video_label'):
                    self.camera_page.video_label.display_frame(frame)

                # Update dataset page video label
                if hasattr(self.dataset_page, 'video_label'):
                    self.dataset_page.video_label.display_frame(frame)

                # Update resolution info on camera page
                if hasattr(self.camera_page, 'resolution_value') and self.frame_count == 1:
                    height, width = frame.shape[:2]
                    self.camera_page.resolution_value.setText(f"{width}×{height}")

    def refresh_camera(self):
        """Refresh camera connection."""
        print(f"Refreshing camera: type={self.camera_type}, index={self.camera_index}")
        self.stop_video()

        if self.cap is not None:
            try:
                self.camera.release_cap(self.cap)
            except Exception as e:
                print(f"Error releasing camera: {e}")
            finally:
                self.cap = None

        # Use QTimer for non-blocking delay
        QTimer.singleShot(500, self.start_video)

    def get_current_frame(self):
        """Get the current camera frame."""
        return self.current_frame

    # ========================
    # Camera Settings Methods
    # ========================

    def on_camera_type_changed(self, text):
        """Handle camera type change."""
        if text == "Intel RealSense":
            new_camera_type = "intel-realsense"
        else:
            new_camera_type = "usb-standard"

        if new_camera_type != self.camera_type:
            self.camera_type = new_camera_type
            self.refresh_camera()

    def on_camera_device_changed(self, index):
        """Handle camera device change."""
        # Implementation depends on settings page integration
        pass

    def on_autofocus_changed(self, state):
        """Handle autofocus checkbox state change."""
        enabled = state == Qt.CheckState.Checked.value
        if self.cap is not None:
            success = self.camera.set_autofocus(self.cap, enabled)
            if not success:
                print(f"Warning: Could not {'enable' if enabled else 'disable'} autofocus")

    def on_manual_focus_changed(self, value):
        """Handle manual focus slider value change."""
        if self.cap is not None:
            success = self.camera.set_manual_focus(self.cap, value)
            if not success:
                print(f"Warning: Could not set manual focus to {value}")

    # ========================
    # Inspection Methods
    # ========================

    def toggle_inspection(self):
        """Toggle inspection mode."""
        self.is_inspecting = not self.is_inspecting

    def toggle_pause(self):
        """Toggle video pause."""
        if self.timer.isActive():
            self.stop_video()
        else:
            self.start_video()

    # ========================
    # Dataset Methods
    # ========================

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
        else:
            save_path = not_ok_path / f"notok_{timestamp}.jpg"
            self.not_ok_samples += 1

        # Save the image
        cv2.imwrite(str(save_path), self.current_frame)
        self.total_samples += 1

        # Add to database
        self.db.add_image(str(save_path))

        print(f"Saved sample: {save_path}")

        # Update dataset page if available - sync counters first
        if hasattr(self.dataset_page, 'update_statistics'):
            self.dataset_page.total_samples = self.total_samples
            self.dataset_page.ok_samples = self.ok_samples
            self.dataset_page.not_ok_samples = self.not_ok_samples
            self.dataset_page.update_statistics()

        if hasattr(self.dataset_page, 'add_to_gallery'):
            self.dataset_page.add_to_gallery(save_path, label_type)

    # ========================
    # Event Handlers
    # ========================

    def closeEvent(self, event):
        """Clean up when the window is closed."""
        self.stop_video()
        if self.cap is not None:
            self.camera.release_cap(self.cap)
        event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Dataset collection shortcuts
        if self.stacked_widget.currentIndex() == self.PAGE_DATASET:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Right):
                self.capture_sample("OK")
            elif event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Left):
                self.capture_sample("NOT_OK")

        super().keyPressEvent(event)


def main():
    """Main function to run the application."""
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow(camera_index=0, camera_type="usb-standard")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
