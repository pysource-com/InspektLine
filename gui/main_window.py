"""Main window for InspektLine GUI — thin orchestrator over services."""

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QDialog
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QIcon

from services.settings_service import SettingsService
from services.camera_service import CameraService
from services.inspection_service import InspectionService
from gui.pages import CameraPage, SettingsPage, HomePage
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
    """Main application window.

    Receives pre-built services via constructor injection.
    All business logic lives in the service layer — this class only
    wires Qt signals/slots and manages page navigation.
    """

    # Emitted on every new frame (from timer) so pages can update
    frame_ready = Signal(object)  # numpy ndarray

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

        # --- UI state ---
        self._timer: QTimer | None = None
        self._frame_count = 0

        # Dialog references (keep alive while open)
        self._dialogs: dict[str, PageDialog | None] = {
            "settings": None,
            "camera": None,
        }
        # Page widget references
        self._pages: dict[str, object | None] = {
            "camera": None,
            "settings": None,
        }

        self._init_ui()
        self._start_frame_timer()

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
        self.home_page.navigate_to_camera.connect(self.open_camera_window)
        self.setCentralWidget(self.home_page)

    # ================================================================
    # Frame timer
    # ================================================================

    def _start_frame_timer(self):
        """Open camera and start a QTimer that reads frames."""
        self.camera_service.open()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(30)  # ~33 fps

    def _stop_frame_timer(self):
        if self._timer and self._timer.isActive():
            self._timer.stop()

    def _on_timer_tick(self):
        ok, frame = self.camera_service.read_frame()
        if not ok:
            return

        self._frame_count += 1

        # Push frame to home page video label (always visible)
        if hasattr(self.home_page, "video_label") and self.home_page.video_label:
            self.home_page.video_label.display_frame(frame)
            if self._frame_count == 1 and hasattr(self.home_page, "resolution_value"):
                h, w = frame.shape[:2]
                self.home_page.resolution_value.setText(f"{w}×{h}")

        # Push frame to open camera page dialog (if open)
        cam_dialog = self._dialogs.get("camera")
        cam_page = self._pages.get("camera")
        if cam_dialog and cam_dialog.isVisible() and cam_page:
            if hasattr(cam_page, "video_label"):
                cam_page.video_label.display_frame(frame)
            if self._frame_count == 1 and hasattr(cam_page, "resolution_value"):
                h, w = frame.shape[:2]
                cam_page.resolution_value.setText(f"{w}×{h}")

        # Emit for any other listeners
        self.frame_ready.emit(frame)

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
        dialog.setMinimumSize(500, 400)
        dialog.resize(550, 450)
        dialog.show()

    def open_camera_window(self):
        dialog, page = self._open_dialog(
            "camera", "InspektLine - Camera Feed", CameraPage,
        )
        dialog.show()

    # ================================================================
    # Convenience accessors
    # ================================================================

    def get_current_frame(self):
        """Return the latest camera frame (numpy array or None)."""
        return self.camera_service.current_frame

    def refresh_camera(self):
        """Restart camera (e.g. after changing device in settings)."""
        self._stop_frame_timer()
        self.camera_service.reopen()
        self._start_frame_timer()

    def toggle_inspection(self):
        if self.inspection_service.is_running:
            self.inspection_service.stop()
        else:
            self.inspection_service.start()

    def toggle_pause(self):
        if self._timer and self._timer.isActive():
            self._stop_frame_timer()
        else:
            self._start_frame_timer()

    # ================================================================
    # Events
    # ================================================================

    def closeEvent(self, event):
        self._stop_frame_timer()
        self.camera_service.close()

        for dialog in self._dialogs.values():
            if dialog and dialog.isVisible():
                dialog.close()

        self.settings_service.save()
        event.accept()
