"""Main window for InspektLine GUI — thin orchestrator over services."""

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QDialog
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QIcon

from services.settings_service import SettingsService
from services.camera_service import CameraService
from services.inspection_service import InspectionService
from gui.pages import SettingsPage, HomePage
from gui.styles import DarkTheme


class FrameBridge(QObject):
    """Bridge to marshal frames from background thread to Qt main thread."""
    frame_ready = Signal(object)  # numpy ndarray


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
    """Main application window.

    Receives pre-built services via constructor injection.
    All business logic lives in the service layer — this class only
    wires Qt signals/slots and manages page navigation.
    """

    def __init__(
        self,
        settings_service: SettingsService,
        camera_service: CameraService,
        inspection_service: InspectionService,
    ):
        super().__init__()

        # --- injected services ---
        self.settings_service = settings_service
        self.camera_service = camera_service
        self.inspection_service = inspection_service

        # --- frame bridge (background thread -> main thread) ---
        self._bridge = FrameBridge()
        self._bridge.frame_ready.connect(self._on_new_frame, Qt.ConnectionType.QueuedConnection)

        self._frame_count = 0
        self._resolution_set = False

        # Dialog references (keep alive while open)
        self._dialogs: dict[str, PageDialog | None] = {
            "settings": None,
        }
        # Page widget references
        self._pages: dict[str, object | None] = {
            "settings": None,
        }

        self._init_ui()
        self._start_camera()

    # ================================================================
    # UI Initialisation
    # ================================================================

    def _init_ui(self):
        self.setWindowTitle("InspektLine - Visual Inspection System")
        self.setWindowIcon(QIcon())
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(DarkTheme.get_main_window_style())

        # Home page is the central widget
        self.home_page = HomePage(parent=self)
        self.home_page.navigate_to_settings.connect(self.open_settings_window)
        self.setCentralWidget(self.home_page)

    # ================================================================
    # Camera capture (background thread)
    # ================================================================

    def _start_camera(self):
        """Open camera and start background capture thread."""
        self.camera_service.start(
            on_frame=self._on_frame_from_thread,
            fps=60,
        )

    def _stop_camera(self):
        """Stop background capture thread."""
        self.camera_service.stop()

    def _on_frame_from_thread(self, frame):
        """Called from the camera background thread — emit signal to main thread."""
        self._bridge.frame_ready.emit(frame)

    def _on_new_frame(self, frame):
        """Handle a new frame on the Qt main thread."""
        self._frame_count += 1

        # Push frame to home page video label
        if hasattr(self.home_page, "video_label") and self.home_page.video_label:
            self.home_page.video_label.display_frame(frame)
            if not self._resolution_set and hasattr(self.home_page, "resolution_value"):
                h, w = frame.shape[:2]
                self.home_page.resolution_value.setText(f"{w}×{h}")
                self._resolution_set = True

    # ================================================================
    # Window-opening helpers
    # ================================================================

    def _open_dialog(self, key: str, title: str, page_factory, **kwargs):
        """Generic helper to open/reuse a page dialog."""
        dialog = self._dialogs.get(key)
        if dialog is None or not dialog.isVisible():
            page = page_factory(
                settings_service=self.settings_service,
                camera_service=self.camera_service,
                inspection_service=self.inspection_service,
                parent=self,
                **kwargs,
            )
            self._pages[key] = page
            dialog = PageDialog(title, page, self)
            self._dialogs[key] = dialog
            return dialog, page
        else:
            dialog.raise_()
            dialog.activateWindow()
            return dialog, self._pages[key]

    def open_settings_window(self):
        dialog, page = self._open_dialog(
            "settings", "InspektLine - Settings", SettingsPage,
        )
        dialog.setMinimumSize(600, 500)
        dialog.resize(650, 800)
        dialog.show()

    # ================================================================
    # Convenience accessors
    # ================================================================

    def get_current_frame(self):
        """Return the latest camera frame (numpy array or None)."""
        return self.camera_service.current_frame

    def refresh_camera(self):
        """Restart camera (e.g. after changing device in settings)."""
        self._stop_camera()
        self.camera_service.reopen()
        self._resolution_set = False
        self._start_camera()

    def toggle_inspection(self):
        if self.inspection_service.is_running:
            self.inspection_service.stop()
        else:
            self.inspection_service.start()

    def toggle_pause(self):
        if self.camera_service._running:
            self._stop_camera()
        else:
            self._start_camera()

    # ================================================================
    # Events
    # ================================================================

    def closeEvent(self, event):
        self._stop_camera()
        self.camera_service.close()

        for dialog in self._dialogs.values():
            if dialog and dialog.isVisible():
                dialog.close()

        self.settings_service.save()
        event.accept()
