"""Main window for InspektLine GUI using modular architecture."""

import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QDialog
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon

from camera.camera import Camera
from database.project_db import ProjectDatabase
from gui.pages import (CameraPage, DatasetPage, SettingsPage, HomePage,
                       AnnotatorPage, TrainingPage)
from gui.styles import DarkTheme


class PageDialog(QDialog):
    """Base dialog for opening pages in separate windows."""

    def __init__(self, title, page_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(DarkTheme.get_main_window_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(page_widget)

        self.page_widget = page_widget


class MainWindow(QMainWindow):
    """Main application window with home page as main content."""

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

        # Dialog references (to keep them alive)
        self.settings_dialog = None
        self.dataset_dialog = None
        self.camera_dialog = None
        self.annotator_dialog = None
        self.training_dialog = None

        # Page references (created when dialogs open)
        self.camera_page = None
        self.dataset_page = None
        self.annotator_page = None
        self.training_page = None
        self.settings_page = None

        self.init_ui()
        self.start_video()

    def init_ui(self):
        """Initialize the user interface."""
        print("=== NEW MAINWINDOW WITHOUT SIDEBAR ===")
        self.setWindowTitle("InspektLine - Visual Inspection System")
        self.setWindowIcon(QIcon())  # Clear window icon
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(DarkTheme.get_main_window_style())

        # Initialize home page as the main content
        self.home_page = HomePage(parent=self)
        self.home_page.navigate_to_capture.connect(self.open_dataset_window)
        self.home_page.navigate_to_annotate.connect(self.open_annotator_window)
        self.home_page.navigate_to_train.connect(self.open_training_window)
        self.home_page.navigate_to_settings.connect(self.open_settings_window)
        self.home_page.navigate_to_dataset.connect(self.open_dataset_window)

        self.setCentralWidget(self.home_page)


    # ========================
    # Window Opening Methods
    # ========================

    def open_settings_window(self):
        """Open settings in a separate window."""
        if self.settings_dialog is None or not self.settings_dialog.isVisible():
            self.settings_page = SettingsPage(parent=self)
            self.settings_dialog = PageDialog("InspektLine - Settings", self.settings_page, self)
            self.settings_dialog.show()
        else:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()

    def open_dataset_window(self):
        """Open dataset collection in a separate window."""
        if self.dataset_dialog is None or not self.dataset_dialog.isVisible():
            self.dataset_page = DatasetPage(parent=self)
            if not self.gallery_loaded and hasattr(self.dataset_page, 'load_existing_samples'):
                self.dataset_page.load_existing_samples()
                self.gallery_loaded = True
            self.dataset_dialog = PageDialog("InspektLine - Dataset Collection", self.dataset_page, self)
            self.is_capturing = True
            self.dataset_dialog.show()
        else:
            self.dataset_dialog.raise_()
            self.dataset_dialog.activateWindow()

    def open_camera_window(self):
        """Open camera feed in a separate window."""
        if self.camera_dialog is None or not self.camera_dialog.isVisible():
            self.camera_page = CameraPage(parent=self)
            self.camera_dialog = PageDialog("InspektLine - Camera Feed", self.camera_page, self)
            self.camera_dialog.show()
        else:
            self.camera_dialog.raise_()
            self.camera_dialog.activateWindow()

    def open_annotator_window(self):
        """Open annotator in a separate window."""
        if self.annotator_dialog is None or not self.annotator_dialog.isVisible():
            self.annotator_page = AnnotatorPage(parent=self)
            self.annotator_dialog = PageDialog("InspektLine - Annotator", self.annotator_page, self)
            self.annotator_dialog.show()
        else:
            self.annotator_dialog.raise_()
            self.annotator_dialog.activateWindow()

    def open_training_window(self):
        """Open training in a separate window."""
        if self.training_dialog is None or not self.training_dialog.isVisible():
            self.training_page = TrainingPage(parent=self)
            self.training_dialog = PageDialog("InspektLine - Training", self.training_page, self)
            self.training_dialog.show()
        else:
            self.training_dialog.raise_()
            self.training_dialog.activateWindow()

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

                # Update camera page video label if dialog is open
                if self.camera_dialog and self.camera_dialog.isVisible():
                    if hasattr(self.camera_page, 'video_label'):
                        self.camera_page.video_label.display_frame(frame)

                # Update dataset page video label if dialog is open
                if self.dataset_dialog and self.dataset_dialog.isVisible():
                    if hasattr(self.dataset_page, 'video_label'):
                        self.dataset_page.video_label.display_frame(frame)

                # Update resolution info on camera page
                if self.camera_dialog and self.camera_dialog.isVisible():
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
        if hasattr(self, 'dataset_page') and self.dataset_page:
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

        # Close any open dialogs
        for dialog in [self.settings_dialog, self.dataset_dialog, self.camera_dialog,
                       self.annotator_dialog, self.training_dialog]:
            if dialog and dialog.isVisible():
                dialog.close()

        event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Dataset collection shortcuts when dataset dialog is open
        if self.dataset_dialog and self.dataset_dialog.isVisible():
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
