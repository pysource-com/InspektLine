"""InspektLine — Visual Inspection System.

Single entry point.  Instantiates services, then launches the GUI.
"""

import sys

from PySide6.QtWidgets import QApplication

from config import APP_TITLE
from services.settings_service import SettingsService
from services.camera_service import CameraService
from services.inspection_service import InspectionService
from gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    # --- bootstrap services (no Qt dependency) ---
    settings = SettingsService()
    camera_svc = CameraService(settings)
    inspection_svc = InspectionService(settings, camera_svc)

    # --- create GUI (thin layer over services) ---
    window = MainWindow(
        settings_service=settings,
        camera_service=camera_svc,
        inspection_service=inspection_svc,
    )
    window.setWindowTitle(APP_TITLE)
    window.show()

    exit_code = app.exec()

    # --- cleanup ---
    camera_svc.stop()
    camera_svc.close()
    settings.save()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
