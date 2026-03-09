"""Test MainWindow import and basic structure."""


def test_imports():
    """Test that all imports work correctly."""
    print("Testing MainWindow imports...")

    try:
        from gui import MainWindow
        print("  MainWindow imported from gui package")
    except ImportError as e:
        print(f"  Failed to import MainWindow from gui: {e}")
        return False

    try:
        from gui.main_window import MainWindow as MW
        print("  MainWindow imported from gui.main_window")
    except ImportError as e:
        print(f"  Failed to import from gui.main_window: {e}")
        return False

    print(f"  MainWindow is a class: {MainWindow.__name__}")

    print("\nAll MainWindow import tests passed!")
    return True


def test_services():
    """Test that services can be instantiated without GUI."""
    print("\nTesting service instantiation...")

    from services.settings_service import SettingsService
    from services.camera_service import CameraService
    from services.dataset_service import DatasetService
    from services.inspection_service import InspectionService
    from database.project_db import ProjectDatabase

    settings = SettingsService()
    print(f"  SettingsService OK (camera_index={settings.camera.camera_index})")

    db = ProjectDatabase(settings.storage_cfg.database_path)
    print("  ProjectDatabase OK")

    dataset_svc = DatasetService(settings, db)
    print(f"  DatasetService OK (ok_path={dataset_svc.ok_path})")

    camera_svc = CameraService(settings)
    print(f"  CameraService OK (is_open={camera_svc.is_open})")

    inspection_svc = InspectionService(settings, camera_svc)
    print(f"  InspectionService OK (has_model={inspection_svc.has_model})")

    db.close()
    print("\nAll service tests passed!")
    return True


if __name__ == "__main__":
    test_imports()
    test_services()
