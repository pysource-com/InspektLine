"""
Quick test script to verify gallery functionality.
Run this to test the gallery without needing a camera.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

def check_storage():
    """Check storage directories and existing images."""
    storage_path = Path("storage/dataset")
    ok_path = storage_path / "ok"
    not_ok_path = storage_path / "not_ok"

    print("\n" + "="*50)
    print("STORAGE CHECK")
    print("="*50)

    if not storage_path.exists():
        print("Storage directory doesn't exist yet")
        return

    print(f"Storage path: {storage_path.absolute()}")

    if ok_path.exists():
        ok_files = list(ok_path.glob("*.jpg"))
        print(f"OK path: {len(ok_files)} images")
        for f in ok_files[:3]:
            print(f"  - {f.name}")
    else:
        print("OK path doesn't exist")

    if not_ok_path.exists():
        notok_files = list(not_ok_path.glob("*.jpg"))
        print(f"NOT OK path: {len(notok_files)} images")
        for f in notok_files[:3]:
            print(f"  - {f.name}")
    else:
        print("NOT OK path doesn't exist")

    print("="*50)

def main():
    """Run the GUI and check gallery."""
    print("\nTESTING GALLERY FUNCTIONALITY\n")
    check_storage()

    print("\nTEST INSTRUCTIONS:")
    print("1. Application will launch")
    print("2. Click 'Manage Dataset' button")
    print("3. Switch to 'Collect Images' tab")
    print("4. Check if gallery shows existing images")
    print("5. Press OK or NOT OK button to capture")
    print("6. Verify new thumbnail appears at top of gallery")

    input("Press Enter to launch GUI...")

    from services.settings_service import SettingsService
    from services.camera_service import CameraService
    from services.dataset_service import DatasetService
    from services.inspection_service import InspectionService
    from database.project_db import ProjectDatabase
    from gui.main_window import MainWindow

    settings = SettingsService()
    db = ProjectDatabase(settings.storage_cfg.database_path)
    camera_svc = CameraService(settings)
    dataset_svc = DatasetService(settings, db)
    inspection_svc = InspectionService(settings, camera_svc)

    app = QApplication(sys.argv)
    window = MainWindow(
        settings_service=settings,
        camera_service=camera_svc,
        dataset_service=dataset_svc,
        inspection_service=inspection_svc,
        db=db,
    )
    window.show()

    print("\nGUI launched successfully!")
    print("Open Dataset page to test gallery...")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
