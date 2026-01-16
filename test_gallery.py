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
        print("❌ Storage directory doesn't exist yet")
        return

    print(f"✓ Storage path: {storage_path.absolute()}")

    if ok_path.exists():
        ok_files = list(ok_path.glob("*.jpg"))
        print(f"✓ OK path: {len(ok_files)} images")
        for f in ok_files[:3]:  # Show first 3
            print(f"  - {f.name}")
    else:
        print("❌ OK path doesn't exist")

    if not_ok_path.exists():
        notok_files = list(not_ok_path.glob("*.jpg"))
        print(f"✓ NOT OK path: {len(notok_files)} images")
        for f in notok_files[:3]:  # Show first 3
            print(f"  - {f.name}")
    else:
        print("❌ NOT OK path doesn't exist")

    print("="*50)

def main():
    """Run the GUI and check gallery."""
    print("\n🧪 TESTING GALLERY FUNCTIONALITY\n")

    # Check storage first
    check_storage()

    print("\n📋 TEST INSTRUCTIONS:")
    print("1. Application will launch")
    print("2. Click the Dataset icon (📁 2nd icon in sidebar)")
    print("3. Check if gallery shows existing images")
    print("4. Press OK or NOT OK button to capture")
    print("5. Verify new thumbnail appears at top of gallery")
    print("6. Verify badges update (OK: X, NG: X)")
    print("\n✨ Gallery should update INSTANTLY when you capture!\n")

    input("Press Enter to launch GUI...")

    # Import and run GUI
    try:
        from gui import VideoDisplayWidget
        app = QApplication(sys.argv)
        window = VideoDisplayWidget(camera_index=0, camera_type="usb-standard")
        window.show()

        print("\n✅ GUI launched successfully!")
        print("📸 Switch to Dataset page to test gallery...")

        sys.exit(app.exec())
    except Exception as e:
        print(f"\n❌ Error launching GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

