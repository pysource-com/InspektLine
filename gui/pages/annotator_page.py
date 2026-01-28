"""Image annotator page with bounding box drawing."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsPixmapItem, QSizePolicy, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPixmap, QPen, QColor, QBrush, QPainter, QFont, QCursor
)
from pathlib import Path
from typing import List, Optional

from gui.styles.themes import DarkTheme
from database.project_db import ProjectDatabase, ImageRecord, AnnotationRecord, LabelRecord


class AnnotationRect(QGraphicsRectItem):
    """A draggable, resizable annotation rectangle."""

    def __init__(self, x: float, y: float, width: float, height: float,
                 class_id: int, class_name: str, color: str, annotation_id: int = -1):
        super().__init__(x, y, width, height)
        self.class_id = class_id
        self.class_name = class_name
        self.annotation_id = annotation_id
        self.color = QColor(color)

        # Set appearance
        pen = QPen(self.color)
        pen.setWidth(2)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(self.color.red(), self.color.green(), self.color.blue(), 40)))

        # Enable interaction
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

    def paint(self, painter, option, widget):
        """Custom paint to add label."""
        super().paint(painter, option, widget)

        # Draw label background
        rect = self.rect()
        label_height = 18
        label_width = min(int(len(self.class_name) * 8 + 10), int(rect.width()))
        label_rect = QRectF(rect.x(), rect.y() - label_height,
                           label_width, label_height)

        painter.fillRect(label_rect, self.color)

        # Draw label text
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.class_name)


class AnnotationCanvas(QGraphicsView):
    """Canvas for displaying images and drawing annotations."""

    annotation_added = Signal(int, float, float, float, float)  # class_id, x, y, w, h (normalized)
    annotation_selected = Signal(int)  # annotation_id
    annotation_deleted = Signal(int)  # annotation_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Setup view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Styling
        self.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {DarkTheme.BG_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
            }}
        """)

        # State
        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.current_image_path: Optional[str] = None
        self.image_width = 0
        self.image_height = 0
        self.annotations: List[AnnotationRect] = []

        # Drawing state
        self.is_drawing = False
        self.draw_start: Optional[QPointF] = None
        self.temp_rect: Optional[QGraphicsRectItem] = None
        self.current_class_id = 0
        self.current_class_name = "Defect"
        self.current_class_color = "#ff4444"

    def load_image(self, image_path: str):
        """Load an image into the canvas."""
        self.scene.clear()
        self.annotations.clear()

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return False

        self.current_image_path = image_path
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()

        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(0, 0, self.image_width, self.image_height)

        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

        return True

    def add_annotation(self, class_id: int, class_name: str, color: str,
                       x_center: float, y_center: float, width: float, height: float,
                       annotation_id: int = -1):
        """Add an annotation rectangle (normalized YOLO coords)."""
        # Convert normalized to pixel coordinates
        px_x = (x_center - width / 2) * self.image_width
        px_y = (y_center - height / 2) * self.image_height
        px_w = width * self.image_width
        px_h = height * self.image_height

        rect = AnnotationRect(px_x, px_y, px_w, px_h, class_id, class_name, color, annotation_id)
        self.scene.addItem(rect)
        self.annotations.append(rect)

    def clear_annotations(self):
        """Remove all annotations from the canvas."""
        for rect in self.annotations:
            self.scene.removeItem(rect)
        self.annotations.clear()

    def set_current_class(self, class_id: int, class_name: str, color: str):
        """Set the current class for new annotations."""
        self.current_class_id = class_id
        self.current_class_name = class_name
        self.current_class_color = color

    def mousePressEvent(self, event):
        """Start drawing a rectangle."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            # Check if clicking on image area
            if self.pixmap_item and self.pixmap_item.contains(scene_pos):
                # Check if clicking on existing annotation
                item = self.scene.itemAt(scene_pos, self.transform())
                if isinstance(item, AnnotationRect):
                    item.setSelected(True)
                    self.annotation_selected.emit(item.annotation_id)
                    super().mousePressEvent(event)
                    return

                # Start drawing new rectangle
                self.is_drawing = True
                self.draw_start = scene_pos

                # Create temporary rectangle
                pen = QPen(QColor(self.current_class_color))
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DashLine)
                self.temp_rect = self.scene.addRect(
                    QRectF(scene_pos, scene_pos), pen,
                    QBrush(QColor(self.current_class_color).lighter(150))
                )

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Update rectangle while drawing."""
        if self.is_drawing and self.temp_rect and self.draw_start:
            scene_pos = self.mapToScene(event.pos())

            # Clamp to image bounds
            scene_pos.setX(max(0, min(scene_pos.x(), self.image_width)))
            scene_pos.setY(max(0, min(scene_pos.y(), self.image_height)))

            # Update rectangle
            rect = QRectF(self.draw_start, scene_pos).normalized()
            self.temp_rect.setRect(rect)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finish drawing rectangle."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False

            if self.temp_rect and self.draw_start:
                scene_pos = self.mapToScene(event.pos())
                rect = QRectF(self.draw_start, scene_pos).normalized()

                # Remove temporary rectangle
                self.scene.removeItem(self.temp_rect)
                self.temp_rect = None

                # Only add if rectangle is big enough
                if rect.width() > 10 and rect.height() > 10:
                    # Convert to normalized coordinates
                    x_center = (rect.x() + rect.width() / 2) / self.image_width
                    y_center = (rect.y() + rect.height() / 2) / self.image_height
                    width = rect.width() / self.image_width
                    height = rect.height() / self.image_height

                    # Emit signal to save annotation
                    self.annotation_added.emit(
                        self.current_class_id,
                        x_center, y_center, width, height
                    )

            self.draw_start = None

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Zoom with mouse wheel."""
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Delete:
            # Delete selected annotations
            for item in self.scene.selectedItems():
                if isinstance(item, AnnotationRect):
                    self.annotation_deleted.emit(item.annotation_id)
                    self.scene.removeItem(item)
                    if item in self.annotations:
                        self.annotations.remove(item)

        super().keyPressEvent(event)

    def fit_to_view(self):
        """Fit the image to the view."""
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)


class LabelButton(QPushButton):
    """A label type selection button."""

    def __init__(self, label: LabelRecord, parent=None):
        super().__init__(parent)
        self.label = label
        self.is_selected = False

        self.setText(f"  {label.name}")
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        """Update button style based on selection state."""
        if self.is_selected:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.label.color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 16px;
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {DarkTheme.BG_INPUT};
                    color: {DarkTheme.TEXT_PRIMARY};
                    border: 1px solid {DarkTheme.BORDER_SECONDARY};
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 16px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {DarkTheme.BG_HOVER};
                }}
            """)

    def set_selected(self, selected: bool):
        """Set selection state."""
        self.is_selected = selected
        self._update_style()


class AnnotationItem(QWidget):
    """Widget displaying a single annotation in the list."""

    delete_clicked = Signal(int)

    def __init__(self, annotation: AnnotationRecord, color: str, parent=None):
        super().__init__(parent)
        self.annotation = annotation

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Color indicator
        color_dot = QLabel("●")
        color_dot.setStyleSheet(f"color: {color}; font-size: 16px;")
        layout.addWidget(color_dot)

        # Label name
        name_label = QLabel(annotation.class_name)
        name_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 13px;")
        layout.addWidget(name_label)

        layout.addStretch()

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {DarkTheme.TEXT_SECONDARY};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {DarkTheme.ERROR};
            }}
        """)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(annotation.id))
        layout.addWidget(delete_btn)


class AnnotatorPage(QWidget):
    """Page for annotating images with bounding boxes."""

    navigate_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.db = ProjectDatabase()

        # State
        self.images: List[ImageRecord] = []
        self.current_index = 0
        self.labels: List[LabelRecord] = []
        self.current_label: Optional[LabelRecord] = None
        self.label_buttons: List[LabelButton] = []

        # UI elements
        self.canvas: Optional[AnnotationCanvas] = None
        self.annotations_list: Optional[QWidget] = None
        self.image_counter: Optional[QLabel] = None
        self.annotations_count: Optional[QLabel] = None

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize the annotator UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Main content
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Canvas area
        canvas_container = self._create_canvas_area()
        content_layout.addWidget(canvas_container, stretch=1)

        # Right sidebar
        sidebar = self._create_sidebar()
        content_layout.addWidget(sidebar)

        layout.addWidget(content, stretch=1)

    def _create_header(self) -> QWidget:
        """Create the header with tabs."""
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-bottom: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 0)
        layout.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()

        title_layout = QVBoxLayout()
        title = QLabel("Dataset & Training")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title)

        subtitle = QLabel("Manage training data and models")
        subtitle.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        title_layout.addWidget(subtitle)

        title_row.addLayout(title_layout)
        title_row.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {DarkTheme.TEXT_SECONDARY};
                border: none;
                font-size: 18px;
            }}
            QPushButton:hover {{
                color: {DarkTheme.TEXT_PRIMARY};
            }}
        """)
        close_btn.clicked.connect(self.navigate_back.emit)
        title_row.addWidget(close_btn)

        layout.addLayout(title_row)

        # Tabs
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(24)

        tab_names = ["Overview", "Collect Images", "Annotate", "Train Model"]
        for i, name in enumerate(tab_names):
            tab = QPushButton(name)
            tab.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {DarkTheme.TEXT_PRIMARY if name == "Annotate" else DarkTheme.TEXT_SECONDARY};
                    border: none;
                    border-bottom: 2px solid {"#0066ff" if name == "Annotate" else "transparent"};
                    padding: 8px 0;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    color: {DarkTheme.TEXT_PRIMARY};
                }}
            """)
            tabs_layout.addWidget(tab)

        tabs_layout.addStretch()
        layout.addLayout(tabs_layout)

        return header

    def _create_canvas_area(self) -> QWidget:
        """Create the canvas area for image display."""
        container = QWidget()
        container.setStyleSheet(f"background-color: {DarkTheme.BG_PRIMARY};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)

        # Canvas
        self.canvas = AnnotationCanvas()
        self.canvas.annotation_added.connect(self._on_annotation_added)
        self.canvas.annotation_deleted.connect(self._on_annotation_deleted)
        layout.addWidget(self.canvas, stretch=1)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(16)

        prev_btn = QPushButton("← Previous")
        prev_btn.setFixedHeight(40)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
            }}
        """)
        prev_btn.clicked.connect(self._prev_image)
        nav_layout.addWidget(prev_btn)

        nav_layout.addStretch()

        # Image counter
        self.image_counter = QLabel("0 / 0")
        self.image_counter.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px;")
        nav_layout.addWidget(self.image_counter)

        nav_layout.addStretch()

        next_btn = QPushButton("Next →")
        next_btn.setFixedHeight(40)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
        """)
        next_btn.clicked.connect(self._next_image)
        nav_layout.addWidget(next_btn)

        layout.addLayout(nav_layout)

        return container

    def _create_sidebar(self) -> QWidget:
        """Create the right sidebar with label selection."""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-left: 1px solid {DarkTheme.BORDER_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Label Type section
        label_header = QLabel("Label Type")
        label_header.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        layout.addWidget(label_header)

        # Label buttons container
        self.labels_container = QVBoxLayout()
        self.labels_container.setSpacing(8)
        layout.addLayout(self.labels_container)

        layout.addSpacing(16)

        # Annotations section
        annotations_header = QHBoxLayout()
        ann_title = QLabel("Annotations")
        ann_title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        annotations_header.addWidget(ann_title)

        self.annotations_count = QLabel("(0)")
        self.annotations_count.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 14px;")
        annotations_header.addWidget(self.annotations_count)
        annotations_header.addStretch()

        layout.addLayout(annotations_header)

        # Annotations scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {DarkTheme.BG_PRIMARY};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {DarkTheme.BG_HOVER};
                border-radius: 4px;
            }}
        """)

        self.annotations_list = QWidget()
        self.annotations_list_layout = QVBoxLayout(self.annotations_list)
        self.annotations_list_layout.setContentsMargins(0, 0, 0, 0)
        self.annotations_list_layout.setSpacing(4)
        self.annotations_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.annotations_list)
        layout.addWidget(scroll, stretch=1)

        return sidebar

    def load_data(self):
        """Load images and labels from database."""
        # Sync images first
        self.db.sync_images_from_folder("storage/dataset")

        # Load labels
        self.labels = self.db.get_labels()
        self._update_label_buttons()

        # Set default label
        if self.labels:
            self._select_label(self.labels[0])

        # Load images
        self.images = self.db.get_all_images()
        self.current_index = 0

        if self.images:
            self._load_current_image()

        self._update_counter()

    def _update_label_buttons(self):
        """Update the label buttons based on available labels."""
        # Clear existing
        for btn in self.label_buttons:
            btn.deleteLater()
        self.label_buttons.clear()

        # Create new buttons
        for label in self.labels:
            btn = LabelButton(label)
            btn.clicked.connect(lambda checked, l=label: self._select_label(l))
            self.labels_container.addWidget(btn)
            self.label_buttons.append(btn)

    def _select_label(self, label: LabelRecord):
        """Select a label for new annotations."""
        self.current_label = label

        # Update button states
        for btn in self.label_buttons:
            btn.set_selected(btn.label.id == label.id)

        # Update canvas
        if self.canvas:
            self.canvas.set_current_class(label.id, label.name, label.color)

    def _load_current_image(self):
        """Load the current image and its annotations."""
        if not self.images or self.current_index >= len(self.images):
            return

        image = self.images[self.current_index]

        # Load image
        if self.canvas.load_image(image.path):
            # Load annotations
            annotations = self.db.get_annotations_for_image(image.id)
            for ann in annotations:
                label = next((l for l in self.labels if l.id == ann.class_id), None)
                color = label.color if label else "#ffffff"
                self.canvas.add_annotation(
                    ann.class_id, ann.class_name, color,
                    ann.x_center, ann.y_center, ann.width, ann.height,
                    ann.id
                )

            self._update_annotations_list()

    def _update_annotations_list(self):
        """Update the annotations list in the sidebar."""
        # Clear existing
        while self.annotations_list_layout.count():
            item = self.annotations_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.images or self.current_index >= len(self.images):
            return

        image = self.images[self.current_index]
        annotations = self.db.get_annotations_for_image(image.id)

        self.annotations_count.setText(f"({len(annotations)})")

        for ann in annotations:
            label = next((l for l in self.labels if l.id == ann.class_id), None)
            color = label.color if label else "#ffffff"

            item = AnnotationItem(ann, color)
            item.delete_clicked.connect(self._on_annotation_deleted)
            self.annotations_list_layout.addWidget(item)

    def _update_counter(self):
        """Update the image counter."""
        total = len(self.images)
        current = self.current_index + 1 if total > 0 else 0
        self.image_counter.setText(f"{current} / {total}")

    def _prev_image(self):
        """Go to previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.canvas.clear_annotations()
            self._load_current_image()
            self._update_counter()

    def _next_image(self):
        """Go to next image."""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.canvas.clear_annotations()
            self._load_current_image()
            self._update_counter()

    def _on_annotation_added(self, class_id: int, x_center: float, y_center: float,
                              width: float, height: float):
        """Handle new annotation from canvas."""
        if not self.images or self.current_index >= len(self.images):
            return

        image = self.images[self.current_index]

        # Save to database
        annotation_id = self.db.add_annotation(
            image.id, class_id, x_center, y_center, width, height
        )

        # Get label info
        label = next((l for l in self.labels if l.id == class_id), None)
        if label:
            # Add to canvas
            self.canvas.add_annotation(
                class_id, label.name, label.color,
                x_center, y_center, width, height,
                annotation_id
            )

        self._update_annotations_list()

    def _on_annotation_deleted(self, annotation_id: int):
        """Handle annotation deletion."""
        self.db.delete_annotation(annotation_id)

        # Refresh display
        self.canvas.clear_annotations()
        self._load_current_image()

    def showEvent(self, event):
        """Refresh when page becomes visible."""
        super().showEvent(event)
        self.load_data()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Left:
            self._prev_image()
        elif event.key() == Qt.Key.Key_Right:
            self._next_image()
        elif event.key() == Qt.Key.Key_1 and self.labels:
            self._select_label(self.labels[0])
        elif event.key() == Qt.Key.Key_2 and len(self.labels) > 1:
            self._select_label(self.labels[1])
        else:
            super().keyPressEvent(event)
