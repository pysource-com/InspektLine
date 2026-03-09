"""Test script for dataset capture functionality."""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from services.settings_service import SettingsService
from services.dataset_service import DatasetService
from database.project_db import ProjectDatabase

def test_storage_creation():
    """Test that storage directories are created."""
    storage_path = Path("storage/dataset")
    ok_path = storage_path / "ok"
    not_ok_path = storage_path / "not_ok"

    print("Testing storage directory creation...")
    print(f"Storage path exists: {storage_path.exists()}")
    print(f"OK path exists: {ok_path.exists()}")
    print(f"NOT OK path exists: {not_ok_path.exists()}")

    if ok_path.exists():
        ok_files = list(ok_path.glob("*.jpg"))
        print(f"OK samples: {len(ok_files)}")

    if not_ok_path.exists():
        notok_files = list(not_ok_path.glob("*.jpg"))
        print(f"NOT OK samples: {len(notok_files)}")

def test_dataset_service():
    """Test DatasetService independently (no GUI needed)."""
    settings = SettingsService()
    db = ProjectDatabase(settings.storage_cfg.database_path)
    svc = DatasetService(settings, db)

    samples = svc.load_existing()
    stats = svc.stats
    print(f"\nDatasetService stats: total={stats.total}, ok={stats.ok}, not_ok={stats.not_ok}")
    print(f"Recent samples: {len(samples)}")
    db.close()

def main():
    """Run dataset tests."""
    print("Starting InspektLine Dataset Test...")
    test_storage_creation()
    test_dataset_service()

    print("\nLaunching GUI...")
    from services.camera_service import CameraService
    from services.inspection_service import InspectionService
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

    print("GUI launched. Open Dataset page and press OK/NOT OK buttons to test.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
