"""YOLO format annotation handler."""

from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """Bounding box in YOLO format (normalized coordinates)."""
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

    def to_yolo_string(self) -> str:
        """Convert to YOLO format string."""
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"

    def to_pixel_coords(self, img_width: int, img_height: int) -> Tuple[int, int, int, int]:
        """Convert to pixel coordinates (x1, y1, x2, y2)."""
        x1 = int((self.x_center - self.width / 2) * img_width)
        y1 = int((self.y_center - self.height / 2) * img_height)
        x2 = int((self.x_center + self.width / 2) * img_width)
        y2 = int((self.y_center + self.height / 2) * img_height)
        return (x1, y1, x2, y2)

    @classmethod
    def from_pixel_coords(cls, x1: int, y1: int, x2: int, y2: int,
                          img_width: int, img_height: int, class_id: int) -> "BoundingBox":
        """Create from pixel coordinates."""
        x_center = ((x1 + x2) / 2) / img_width
        y_center = ((y1 + y2) / 2) / img_height
        width = abs(x2 - x1) / img_width
        height = abs(y2 - y1) / img_height
        return cls(class_id, x_center, y_center, width, height)

    @classmethod
    def from_yolo_string(cls, line: str) -> Optional["BoundingBox"]:
        """Parse from YOLO format string."""
        parts = line.strip().split()
        if len(parts) >= 5:
            try:
                return cls(
                    class_id=int(parts[0]),
                    x_center=float(parts[1]),
                    y_center=float(parts[2]),
                    width=float(parts[3]),
                    height=float(parts[4])
                )
            except ValueError:
                return None
        return None


class YOLOAnnotation:
    """Handler for YOLO format annotations."""

    def __init__(self, labels_path: Optional[str] = None):
        """
        Initialize YOLO annotation handler.

        Args:
            labels_path: Path to classes.txt file
        """
        self.labels: List[str] = []
        self.label_colors: dict = {
            "Defect": "#ff4444",
            "Pass": "#44cc44"
        }

        if labels_path:
            self.load_labels(labels_path)
        else:
            # Default labels
            self.labels = ["Defect", "Pass"]

    def load_labels(self, path: str):
        """Load class labels from classes.txt."""
        labels_file = Path(path)
        if labels_file.exists():
            with open(labels_file, "r") as f:
                self.labels = [line.strip() for line in f if line.strip()]

    def save_labels(self, path: str):
        """Save class labels to classes.txt."""
        with open(path, "w") as f:
            for label in self.labels:
                f.write(f"{label}\n")

    def get_label_name(self, class_id: int) -> str:
        """Get label name by class ID."""
        if 0 <= class_id < len(self.labels):
            return self.labels[class_id]
        return f"class_{class_id}"

    def get_label_id(self, name: str) -> int:
        """Get class ID by label name."""
        try:
            return self.labels.index(name)
        except ValueError:
            return -1

    def get_label_color(self, class_id: int) -> str:
        """Get color for a class."""
        name = self.get_label_name(class_id)
        return self.label_colors.get(name, "#ffffff")

    def load_annotations(self, txt_path: str) -> List[BoundingBox]:
        """Load annotations from a YOLO .txt file."""
        annotations = []
        txt_file = Path(txt_path)

        if txt_file.exists():
            with open(txt_file, "r") as f:
                for line in f:
                    bbox = BoundingBox.from_yolo_string(line)
                    if bbox:
                        annotations.append(bbox)

        return annotations

    def save_annotations(self, txt_path: str, annotations: List[BoundingBox]):
        """Save annotations to a YOLO .txt file."""
        with open(txt_path, "w") as f:
            for bbox in annotations:
                f.write(bbox.to_yolo_string() + "\n")

    def get_annotation_path_for_image(self, image_path: str, labels_dir: Optional[str] = None) -> str:
        """Get the annotation file path for an image."""
        img_path = Path(image_path)

        if labels_dir:
            # Use specified labels directory
            return str(Path(labels_dir) / (img_path.stem + ".txt"))
        else:
            # Same directory as image
            return str(img_path.with_suffix(".txt"))

    def image_has_annotations(self, image_path: str, labels_dir: Optional[str] = None) -> bool:
        """Check if an image has annotations."""
        txt_path = self.get_annotation_path_for_image(image_path, labels_dir)
        txt_file = Path(txt_path)
        return txt_file.exists() and txt_file.stat().st_size > 0


class YOLODatasetExporter:
    """Export dataset in YOLO format for training."""

    def __init__(self, output_dir: str):
        """
        Initialize exporter.

        Args:
            output_dir: Base output directory for dataset
        """
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.labels_dir = self.output_dir / "labels"

    def setup_directories(self, splits: List[str] = None):
        """Create directory structure."""
        if splits is None:
            splits = ["train", "val", "test"]

        for split in splits:
            (self.images_dir / split).mkdir(parents=True, exist_ok=True)
            (self.labels_dir / split).mkdir(parents=True, exist_ok=True)

    def export_image_with_annotations(self, image_path: str, annotations: List[BoundingBox],
                                       split: str = "train"):
        """Copy image and create annotation file."""
        import shutil

        src_path = Path(image_path)
        dst_image = self.images_dir / split / src_path.name
        dst_label = self.labels_dir / split / (src_path.stem + ".txt")

        # Copy image
        shutil.copy2(src_path, dst_image)

        # Write annotation file
        handler = YOLOAnnotation()
        handler.save_annotations(str(dst_label), annotations)

    def create_data_yaml(self, labels: List[str], output_path: Optional[str] = None):
        """Create data.yaml for training."""
        if output_path is None:
            output_path = str(self.output_dir / "data.yaml")

        yaml_content = f"""# InspektLine Dataset
path: {self.output_dir.absolute()}
train: images/train
val: images/val
test: images/test

# Classes
names:
"""
        for i, label in enumerate(labels):
            yaml_content += f"  {i}: {label}\n"

        with open(output_path, "w") as f:
            f.write(yaml_content)
