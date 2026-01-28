"""Quick test of database functionality."""
import sys
sys.path.insert(0, ".")

from database.project_db import ProjectDatabase

def test_db():
    print("Testing database connection...")

    try:
        db = ProjectDatabase()
        print("[OK] Database connected")

        # Test sync
        print("Testing sync_images_from_folder...")
        count = db.sync_images_from_folder("storage/dataset")
        print(f"[OK] Synced {count} images")

        # Test get stats
        stats = db.get_project_stats()
        print(f"[OK] Stats: {stats.total_images} images, {stats.annotated_images} annotated")

        db.close()
        print("[OK] Database closed")
        print("\n[OK] All database tests passed!")
        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_db()
    sys.exit(0 if success else 1)
