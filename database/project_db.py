"""SQLite database for project state management."""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class ImageRecord:
    """Represents an image in the dataset."""
    id: int
    project_id: int
    path: str
    filename: str
    annotated: bool
    created_at: str


@dataclass
class AnnotationRecord:
    """Represents a bounding box annotation."""
    id: int
    image_id: int
    class_id: int
    class_name: str
    x_center: float
    y_center: float
    width: float
    height: float


@dataclass
class LabelRecord:
    """Represents a label/class definition."""
    id: int
    project_id: int
    name: str
    color: str


@dataclass
class ModelRecord:
    """Represents a trained model."""
    id: int
    project_id: int
    name: str
    path: str
    model_type: str  # 'detection', 'classification', 'segmentation'
    metrics: str  # JSON string
    created_at: str


@dataclass
class ProjectStats:
    """Project statistics."""
    total_images: int
    annotated_images: int
    total_annotations: int
    defect_labels: int
    pass_labels: int
    models_count: int


class ProjectDatabase:
    """SQLite database manager for InspektLine projects."""

    def __init__(self, db_path: str = "storage/inspektline.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()
        self._ensure_default_project()
        self._ensure_default_labels()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0  # Wait up to 30 seconds for locks
        )
        self.conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Labels/Classes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                path TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                annotated INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Annotations table (YOLO format: normalized coordinates)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                x_center REAL NOT NULL,
                y_center REAL NOT NULL,
                width REAL NOT NULL,
                height REAL NOT NULL,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES labels(id) ON DELETE CASCADE
            )
        """)

        # Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                model_type TEXT NOT NULL,
                metrics TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    def _ensure_default_project(self):
        """Create default project if none exists."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO projects (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
                ("Default Project", "Default inspection project", now, now)
            )
            self.conn.commit()

    def _ensure_default_labels(self):
        """Create default labels if none exist for default project."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM labels WHERE project_id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO labels (project_id, name, color) VALUES (?, ?, ?)",
                (1, "Defect", "#ff4444")
            )
            cursor.execute(
                "INSERT INTO labels (project_id, name, color) VALUES (?, ?, ?)",
                (1, "Pass", "#44cc44")
            )
            self.conn.commit()

    # ========== Image Operations ==========

    def add_image(self, path: str, project_id: int = 1) -> int:
        """Add an image to the database."""
        cursor = self.conn.cursor()
        filename = Path(path).name
        now = datetime.now().isoformat()

        try:
            cursor.execute(
                "INSERT INTO images (project_id, path, filename, annotated, created_at) VALUES (?, ?, ?, ?, ?)",
                (project_id, path, filename, 0, now)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Image already exists, return existing ID
            cursor.execute("SELECT id FROM images WHERE path = ?", (path,))
            row = cursor.fetchone()
            return row["id"] if row else -1

    def get_image(self, image_id: int) -> Optional[ImageRecord]:
        """Get image by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        if row:
            return ImageRecord(
                id=row["id"],
                project_id=row["project_id"],
                path=row["path"],
                filename=row["filename"],
                annotated=bool(row["annotated"]),
                created_at=row["created_at"]
            )
        return None

    def get_all_images(self, project_id: int = 1) -> List[ImageRecord]:
        """Get all images for a project."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM images WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
        return [
            ImageRecord(
                id=row["id"],
                project_id=row["project_id"],
                path=row["path"],
                filename=row["filename"],
                annotated=bool(row["annotated"]),
                created_at=row["created_at"]
            )
            for row in cursor.fetchall()
        ]

    def get_unannotated_images(self, project_id: int = 1) -> List[ImageRecord]:
        """Get images that haven't been annotated."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM images WHERE project_id = ? AND annotated = 0 ORDER BY created_at ASC",
            (project_id,)
        )
        return [
            ImageRecord(
                id=row["id"],
                project_id=row["project_id"],
                path=row["path"],
                filename=row["filename"],
                annotated=bool(row["annotated"]),
                created_at=row["created_at"]
            )
            for row in cursor.fetchall()
        ]

    def mark_image_annotated(self, image_id: int, annotated: bool = True):
        """Mark an image as annotated or not."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE images SET annotated = ? WHERE id = ?",
            (1 if annotated else 0, image_id)
        )
        self.conn.commit()

    def delete_image(self, image_id: int):
        """Delete an image and its annotations."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        self.conn.commit()

    def sync_images_from_folder(self, folder_path: str, project_id: int = 1) -> int:
        """Sync images from storage folder to database."""
        folder = Path(folder_path)
        if not folder.exists():
            return 0

        extensions = (".jpg", ".jpeg", ".png", ".bmp")
        added = 0
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()

        # Collect all images to add
        images_to_add = []
        for ext in extensions:
            for img_path in folder.rglob(f"*{ext}"):
                images_to_add.append((project_id, str(img_path), img_path.name, 0, now))

        # Batch insert with INSERT OR IGNORE to handle duplicates
        try:
            cursor.executemany(
                "INSERT OR IGNORE INTO images (project_id, path, filename, annotated, created_at) VALUES (?, ?, ?, ?, ?)",
                images_to_add
            )
            added = cursor.rowcount
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during sync: {e}")
            self.conn.rollback()
            added = 0

        return added

    # ========== Annotation Operations ==========

    def add_annotation(self, image_id: int, class_id: int,
                       x_center: float, y_center: float,
                       width: float, height: float) -> int:
        """Add a bounding box annotation."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO annotations (image_id, class_id, x_center, y_center, width, height) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (image_id, class_id, x_center, y_center, width, height)
        )
        self.conn.commit()

        # Mark image as annotated
        self.mark_image_annotated(image_id, True)

        return cursor.lastrowid

    def get_annotations_for_image(self, image_id: int) -> List[AnnotationRecord]:
        """Get all annotations for an image."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT a.*, l.name as class_name 
               FROM annotations a 
               JOIN labels l ON a.class_id = l.id 
               WHERE a.image_id = ?""",
            (image_id,)
        )
        return [
            AnnotationRecord(
                id=row["id"],
                image_id=row["image_id"],
                class_id=row["class_id"],
                class_name=row["class_name"],
                x_center=row["x_center"],
                y_center=row["y_center"],
                width=row["width"],
                height=row["height"]
            )
            for row in cursor.fetchall()
        ]

    def delete_annotation(self, annotation_id: int):
        """Delete an annotation."""
        cursor = self.conn.cursor()

        # Get image_id before deletion
        cursor.execute("SELECT image_id FROM annotations WHERE id = ?", (annotation_id,))
        row = cursor.fetchone()
        image_id = row["image_id"] if row else None

        cursor.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
        self.conn.commit()

        # Check if image still has annotations
        if image_id:
            cursor.execute("SELECT COUNT(*) FROM annotations WHERE image_id = ?", (image_id,))
            if cursor.fetchone()[0] == 0:
                self.mark_image_annotated(image_id, False)

    def clear_annotations_for_image(self, image_id: int):
        """Remove all annotations for an image."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM annotations WHERE image_id = ?", (image_id,))
        self.mark_image_annotated(image_id, False)
        self.conn.commit()

    # ========== Label Operations ==========

    def get_labels(self, project_id: int = 1) -> List[LabelRecord]:
        """Get all labels for a project."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM labels WHERE project_id = ?", (project_id,))
        return [
            LabelRecord(
                id=row["id"],
                project_id=row["project_id"],
                name=row["name"],
                color=row["color"]
            )
            for row in cursor.fetchall()
        ]

    def add_label(self, name: str, color: str, project_id: int = 1) -> int:
        """Add a new label."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO labels (project_id, name, color) VALUES (?, ?, ?)",
            (project_id, name, color)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_label_by_name(self, name: str, project_id: int = 1) -> Optional[LabelRecord]:
        """Get label by name."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM labels WHERE project_id = ? AND name = ?",
            (project_id, name)
        )
        row = cursor.fetchone()
        if row:
            return LabelRecord(
                id=row["id"],
                project_id=row["project_id"],
                name=row["name"],
                color=row["color"]
            )
        return None

    # ========== Model Operations ==========

    def add_model(self, name: str, path: str, model_type: str,
                  metrics: str = "{}", project_id: int = 1) -> int:
        """Add a trained model record."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO models (project_id, name, path, model_type, metrics, created_at) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, name, path, model_type, metrics, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_models(self, project_id: int = 1) -> List[ModelRecord]:
        """Get all models for a project."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM models WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,)
        )
        return [
            ModelRecord(
                id=row["id"],
                project_id=row["project_id"],
                name=row["name"],
                path=row["path"],
                model_type=row["model_type"],
                metrics=row["metrics"],
                created_at=row["created_at"]
            )
            for row in cursor.fetchall()
        ]

    def get_latest_model(self, project_id: int = 1) -> Optional[ModelRecord]:
        """Get the most recent model."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM models WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
            (project_id,)
        )
        row = cursor.fetchone()
        if row:
            return ModelRecord(
                id=row["id"],
                project_id=row["project_id"],
                name=row["name"],
                path=row["path"],
                model_type=row["model_type"],
                metrics=row["metrics"],
                created_at=row["created_at"]
            )
        return None

    # ========== Statistics ==========

    def get_project_stats(self, project_id: int = 1) -> ProjectStats:
        """Get project statistics."""
        cursor = self.conn.cursor()

        # Total images
        cursor.execute("SELECT COUNT(*) FROM images WHERE project_id = ?", (project_id,))
        total_images = cursor.fetchone()[0]

        # Annotated images
        cursor.execute(
            "SELECT COUNT(*) FROM images WHERE project_id = ? AND annotated = 1",
            (project_id,)
        )
        annotated_images = cursor.fetchone()[0]

        # Total annotations
        cursor.execute(
            """SELECT COUNT(*) FROM annotations a 
               JOIN images i ON a.image_id = i.id 
               WHERE i.project_id = ?""",
            (project_id,)
        )
        total_annotations = cursor.fetchone()[0]

        # Defect labels count
        defect_label = self.get_label_by_name("Defect", project_id)
        defect_labels = 0
        if defect_label:
            cursor.execute(
                """SELECT COUNT(*) FROM annotations a 
                   JOIN images i ON a.image_id = i.id 
                   WHERE i.project_id = ? AND a.class_id = ?""",
                (project_id, defect_label.id)
            )
            defect_labels = cursor.fetchone()[0]

        # Pass labels count
        pass_label = self.get_label_by_name("Pass", project_id)
        pass_labels = 0
        if pass_label:
            cursor.execute(
                """SELECT COUNT(*) FROM annotations a 
                   JOIN images i ON a.image_id = i.id 
                   WHERE i.project_id = ? AND a.class_id = ?""",
                (project_id, pass_label.id)
            )
            pass_labels = cursor.fetchone()[0]

        # Models count
        cursor.execute("SELECT COUNT(*) FROM models WHERE project_id = ?", (project_id,))
        models_count = cursor.fetchone()[0]

        return ProjectStats(
            total_images=total_images,
            annotated_images=annotated_images,
            total_annotations=total_annotations,
            defect_labels=defect_labels,
            pass_labels=pass_labels,
            models_count=models_count
        )

    # ========== YOLO Export ==========

    def export_yolo_annotations(self, output_dir: str, project_id: int = 1):
        """Export annotations in YOLO format."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Export classes.txt
        labels = self.get_labels(project_id)
        with open(output_path / "classes.txt", "w") as f:
            for label in labels:
                f.write(f"{label.name}\n")

        # Create label index map
        label_index = {label.id: idx for idx, label in enumerate(labels)}

        # Export annotations for each image
        images = self.get_all_images(project_id)
        for image in images:
            annotations = self.get_annotations_for_image(image.id)
            if annotations:
                txt_filename = Path(image.filename).stem + ".txt"
                with open(output_path / txt_filename, "w") as f:
                    for ann in annotations:
                        class_idx = label_index.get(ann.class_id, 0)
                        f.write(f"{class_idx} {ann.x_center:.6f} {ann.y_center:.6f} "
                                f"{ann.width:.6f} {ann.height:.6f}\n")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
