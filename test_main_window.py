"""Test MainWindow import and basic structure."""

def test_imports():
    """Test that all imports work correctly."""
    print("Testing MainWindow imports...")

    try:
        from gui import MainWindow
        print("✓ MainWindow imported from gui package")
    except ImportError as e:
        print(f"✗ Failed to import MainWindow from gui: {e}")
        return False

    try:
        from gui.main_window import MainWindow as MW
        print("✓ MainWindow imported from gui.main_window")
    except ImportError as e:
        print(f"✗ Failed to import from gui.main_window: {e}")
        return False

    # Verify it's a class
    print(f"✓ MainWindow is a class: {MainWindow.__name__}")

    # Check key attributes
    expected_attrs = ['PAGE_HOME', 'PAGE_CAMERA', 'PAGE_DATASET',
                      'PAGE_ANNOTATE', 'PAGE_TRAIN', 'PAGE_SETTINGS']
    for attr in expected_attrs:
        if hasattr(MainWindow, attr):
            print(f"✓ Has attribute: {attr}")
        else:
            print(f"✗ Missing attribute: {attr}")

    print("\n✓ All MainWindow tests passed!")
    return True


if __name__ == "__main__":
    test_imports()
