"""Test script for dataset capture functionality."""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.py import VideoDisplayWidget

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

def main():
    """Run the application in test mode."""
    print("Starting InspektLine Dataset Test...")
    test_storage_creation()

    print("\nLaunching GUI...")
    app = QApplication(sys.argv)
    window = VideoDisplayWidget(camera_index=0, camera_type="usb-standard")
    window.show()

    print("GUI launched. Switch to Dataset page and press OK/NOT OK buttons to test.")
    print("Images will be saved to storage/dataset/ok and storage/dataset/not_ok")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

