"""Dataset & Training page with tabbed interface."""

import cv2
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QStackedWidget, QLineEdit,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPixmap, QPen, QColor, QBrush, QPainter, QFont

from gui.components import VideoLabel
from gui.styles import StyleSheets, DarkTheme
from database.project_db import ProjectDatabase, ImageRecord, LabelRecord


# ============== Annotation Components ==============

class AnnotationRect(QGraphicsRectItem):
    """A draggable, resizable annotation rectangle."""

    def __init__(self, x: float, y: float, width: float, height: float,
                 class_id: int, class_name: str, color: str, annotation_id: int = -1):
        super().__init__(x, y, width, height)
        self.class_id = class_id
        self.class_name = class_name
        self.annotation_id = annotation_id
        self.color = QColor(color)

        pen = QPen(self.color)
        pen.setWidth(2)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(self.color.red(), self.color.green(), self.color.blue(), 40)))

        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        rect = self.rect()
        label_height = 18
        label_width = min(int(len(self.class_name) * 8 + 10), int(rect.width()))
        label_rect = QRectF(rect.x(), rect.y() - label_height, label_width, label_height)
        painter.fillRect(label_rect, self.color)
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.class_name)


class AnnotationCanvas(QGraphicsView):
    """Canvas for displaying images and drawing annotations."""

    annotation_added = Signal(int, float, float, float, float)
    annotation_selected = Signal(int)
    annotation_deleted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {DarkTheme.BG_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
            }}
        """)

        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.current_image_path: Optional[str] = None
        self.image_width = 0
        self.image_height = 0
        self.annotations: List[AnnotationRect] = []

        self.is_drawing = False
        self.draw_start: Optional[QPointF] = None
        self.temp_rect: Optional[QGraphicsRectItem] = None
        self.current_class_id = 0
        self.current_class_name = "Defect"
        self.current_class_color = "#ff4444"

    def load_image(self, image_path: str):
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
        px_x = (x_center - width / 2) * self.image_width
        px_y = (y_center - height / 2) * self.image_height
        px_w = width * self.image_width
        px_h = height * self.image_height

        rect = AnnotationRect(px_x, px_y, px_w, px_h, class_id, class_name, color, annotation_id)
        self.scene.addItem(rect)
        self.annotations.append(rect)

    def clear_annotations(self):
        for rect in self.annotations:
            self.scene.removeItem(rect)
        self.annotations.clear()

    def set_current_class(self, class_id: int, class_name: str, color: str):
        self.current_class_id = class_id
        self.current_class_name = class_name
        self.current_class_color = color

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            if self.pixmap_item and self.pixmap_item.contains(scene_pos):
                item = self.scene.itemAt(scene_pos, self.transform())
                if isinstance(item, AnnotationRect):
                    item.setSelected(True)
                    self.annotation_selected.emit(item.annotation_id)
                    super().mousePressEvent(event)
                    return

                self.is_drawing = True
                self.draw_start = scene_pos

                pen = QPen(QColor(self.current_class_color))
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DashLine)
                self.temp_rect = self.scene.addRect(
                    QRectF(scene_pos, scene_pos), pen,
                    QBrush(QColor(self.current_class_color).lighter(150))
                )

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.temp_rect and self.draw_start:
            scene_pos = self.mapToScene(event.pos())
            scene_pos.setX(max(0, min(scene_pos.x(), self.image_width)))
            scene_pos.setY(max(0, min(scene_pos.y(), self.image_height)))
            rect = QRectF(self.draw_start, scene_pos).normalized()
            self.temp_rect.setRect(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False

            if self.temp_rect and self.draw_start:
                scene_pos = self.mapToScene(event.pos())
                rect = QRectF(self.draw_start, scene_pos).normalized()
                self.scene.removeItem(self.temp_rect)
                self.temp_rect = None

                if rect.width() > 10 and rect.height() > 10:
                    x_center = (rect.x() + rect.width() / 2) / self.image_width
                    y_center = (rect.y() + rect.height() / 2) / self.image_height
                    width = rect.width() / self.image_width
                    height = rect.height() / self.image_height
                    self.annotation_added.emit(self.current_class_id, x_center, y_center, width, height)

            self.draw_start = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.scene.selectedItems():
                if isinstance(item, AnnotationRect):
                    self.annotation_deleted.emit(item.annotation_id)
                    self.scene.removeItem(item)
                    if item in self.annotations:
                        self.annotations.remove(item)
        super().keyPressEvent(event)

    def fit_to_view(self):
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)


class LabelButton(QPushButton):
    """A label type selection button."""

    def __init__(self, label: LabelRecord, parent=None):
        super().__init__(parent)
        self.label = label
        self.is_selected = False
        # Add icon based on label name
        icon = "⚠" if label.name.lower() == "defect" else "✓"
        self.setText(f"  {icon}  {label.name}")
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

    def _update_style(self):
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
        self.is_selected = selected
        self._update_style()


# ============== Main Dataset Page ==============

class DatasetPage(QWidget):
    """Dataset & Training page with tabbed interface."""

    navigate_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.db = ProjectDatabase()

        # Storage paths
        self.storage_path = Path("storage/dataset")
        self.ok_path = self.storage_path / "ok"
        self.not_ok_path = self.storage_path / "not_ok"
        self.ok_path.mkdir(parents=True, exist_ok=True)
        self.not_ok_path.mkdir(parents=True, exist_ok=True)

        # UI references
        self.stacked_widget = None
        self.tab_buttons = []
        self.current_tab = 0

        # Overview stats labels
        self.total_images_label = None
        self.annotated_label = None
        self.defects_label = None

        # Collect Images references
        self.dataset_video_label = None
        self.ok_button = None
        self.not_ok_button = None
        self.defect_category_combo = None
        self.gallery_layout = None
        self.gallery_items = []
        self.ok_samples = 0
        self.not_ok_samples = 0
        self.total_samples = 0

        # Annotate references
        self.canvas = None
        self.images: List[ImageRecord] = []
        self.current_index = 0
        self.labels: List[LabelRecord] = []
        self.current_label: Optional[LabelRecord] = None
        self.label_buttons: List[LabelButton] = []
        self.labels_container = None
        self.annotations_count = None
        self.annotations_list_layout = None
        self.image_counter = None
        self.image_info_label = None

        # Train Model references
        self.model_name_input = None
        self.train_total_images = None
        self.train_defect_labels = None
        self.train_pass_labels = None

        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with tabs
        header = self._create_header()
        layout.addWidget(header)

        # Stacked widget for tab content
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(f"background-color: {DarkTheme.BG_PRIMARY};")

        # Create tab pages
        self.stacked_widget.addWidget(self._create_overview_page())
        self.stacked_widget.addWidget(self._create_collect_page())
        self.stacked_widget.addWidget(self._create_annotate_page())
        self.stacked_widget.addWidget(self._create_train_page())

        layout.addWidget(self.stacked_widget)

        # Load initial data
        self._refresh_stats()
        self._load_existing_samples()

    def _create_header(self) -> QWidget:
        """Create header with title and tabs."""
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
            tab.setCursor(Qt.CursorShape.PointingHandCursor)
            tab.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            self.tab_buttons.append(tab)
            tabs_layout.addWidget(tab)

        tabs_layout.addStretch()
        layout.addLayout(tabs_layout)

        self._update_tab_styles()
        return header

    def _update_tab_styles(self):
        """Update tab button styles based on current selection."""
        for i, tab in enumerate(self.tab_buttons):
            is_active = i == self.current_tab
            tab.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {DarkTheme.TEXT_PRIMARY if is_active else DarkTheme.TEXT_SECONDARY};
                    border: none;
                    border-bottom: 2px solid {"#0066ff" if is_active else "transparent"};
                    padding: 8px 0;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    color: {DarkTheme.TEXT_PRIMARY};
                }}
            """)

    def _switch_tab(self, index: int):
        """Switch to a different tab."""
        self.current_tab = index
        self.stacked_widget.setCurrentIndex(index)
        self._update_tab_styles()

        # Refresh data when switching tabs
        if index == 0:
            self._refresh_stats()
        elif index == 2:
            self._load_annotation_data()
        elif index == 3:
            self._refresh_train_stats()

    # ============== Overview Page ==============

    def _create_overview_page(self) -> QWidget:
        """Create the Overview tab page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Stats cards row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        # Total Images card
        total_card, self.total_images_label = self._create_stat_card(
            "Total Images", "0", "#a855f7", "🖼"
        )
        stats_layout.addWidget(total_card)

        # Annotated card
        annotated_card, self.annotated_label = self._create_stat_card(
            "Annotated", "0", "#22c55e", "🏷"
        )
        stats_layout.addWidget(annotated_card)

        # Defects Labeled card
        defects_card, self.defects_label = self._create_stat_card(
            "Defects Labeled", "0", "#3b82f6", "🔍"
        )
        stats_layout.addWidget(defects_card)

        layout.addLayout(stats_layout)

        # Quick Actions section
        actions_label = QLabel("QUICK ACTIONS")
        actions_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; font-weight: bold;")
        layout.addWidget(actions_label)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(16)

        # Add Images action
        add_action = self._create_action_card(
            "Add Images", "Upload or capture product images", "#a855f7", "🖼",
            lambda: self._switch_tab(1)
        )
        actions_layout.addWidget(add_action)

        # Annotate Images action
        annotate_action = self._create_action_card(
            "Annotate Images", "Label defects and features", "#22c55e", "🏷",
            lambda: self._switch_tab(2)
        )
        actions_layout.addWidget(annotate_action)

        # Train Model action
        train_action = self._create_action_card(
            "Train Model", "Create a detection model", "#3b82f6", "🧠",
            lambda: self._switch_tab(3)
        )
        actions_layout.addWidget(train_action)

        layout.addLayout(actions_layout)
        layout.addStretch()

        return page

    def _create_stat_card(self, title: str, value: str, color: str, icon: str):
        """Create a statistics card widget."""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 12px;
            }}
        """)
        card.setMinimumHeight(120)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # Header with icon and title
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 18px;")
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 13px;")
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 32px; font-weight: bold;")
        layout.addWidget(value_label)

        layout.addStretch()

        return card, value_label

    def _create_action_card(self, title: str, subtitle: str, color: str, icon: str, callback):
        """Create a quick action card."""
        card = QPushButton()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.clicked.connect(callback)
        card.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.BG_CARD};
                border: 1px solid {color};
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.BG_HOVER};
            }}
        """)
        card.setMinimumHeight(140)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Icon row with plus
        icon_row = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 24px;")
        icon_row.addWidget(icon_label)
        icon_row.addStretch()

        plus_label = QLabel("+")
        plus_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 18px;")
        icon_row.addWidget(plus_label)

        layout.addLayout(icon_row)
        layout.addStretch()

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(subtitle_label)

        return card

    def _refresh_stats(self):
        """Refresh the overview statistics."""
        self.db.sync_images_from_folder("storage/dataset")
        stats = self.db.get_project_stats()

        if self.total_images_label:
            self.total_images_label.setText(str(stats.total_images))
        if self.annotated_label:
            self.annotated_label.setText(str(stats.annotated_images))
        if self.defects_label:
            self.defects_label.setText(str(stats.defect_labels))

    # ============== Collect Images Page ==============

    def _create_collect_page(self) -> QWidget:
        """Create the Collect Images tab page."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Left panel - stats and category
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)

        # Stats widget
        stats_widget = self._create_collect_stats_widget()
        left_layout.addWidget(stats_widget)

        # Defect category
        category_widget = self._create_defect_category_widget()
        left_layout.addWidget(category_widget)

        left_layout.addStretch()
        layout.addWidget(left_panel)

        # Center panel - video feed
        center_panel = self._create_video_panel()
        layout.addWidget(center_panel, stretch=1)

        # Right panel - gallery
        right_panel = self._create_gallery_panel()
        layout.addWidget(right_panel)

        return page

    def _create_collect_stats_widget(self) -> QWidget:
        """Create collection statistics widget."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Collection Stats")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Stats will be updated dynamically
        self.collect_total_label = QLabel("Total: 0")
        self.collect_total_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(self.collect_total_label)

        self.collect_ok_label = QLabel("OK: 0")
        self.collect_ok_label.setStyleSheet(f"color: {DarkTheme.SUCCESS}; font-size: 14px;")
        layout.addWidget(self.collect_ok_label)

        self.collect_notok_label = QLabel("NOT OK: 0")
        self.collect_notok_label.setStyleSheet(f"color: {DarkTheme.ERROR}; font-size: 14px;")
        layout.addWidget(self.collect_notok_label)

        return widget

    def _create_defect_category_widget(self) -> QWidget:
        """Create defect category selection widget."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Defect Category")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self.defect_category_combo = QComboBox()
        self.defect_category_combo.addItems([
            "Surface Defect", "Crack", "Scratch", "Dent",
            "Discoloration", "Missing Part", "Contamination"
        ])
        self.defect_category_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.defect_category_combo.setFixedHeight(40)
        layout.addWidget(self.defect_category_combo)

        return widget

    def _create_video_panel(self) -> QWidget:
        """Create the video feed panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("📹 Live Feed")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.setStyleSheet(StyleSheets.get_icon_button_style())
        if self.parent_window:
            refresh_btn.clicked.connect(self.parent_window.refresh_camera)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Video container
        video_container = QWidget()
        video_container.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
            }}
        """)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(8, 8, 8, 8)

        self.dataset_video_label = VideoLabel()
        video_layout.addWidget(self.dataset_video_label)

        layout.addWidget(video_container, stretch=1)

        # Capture buttons
        buttons = self._create_capture_buttons()
        layout.addLayout(buttons)

        return panel

    def _create_capture_buttons(self) -> QHBoxLayout:
        """Create OK and NOT OK capture buttons."""
        layout = QHBoxLayout()
        layout.setSpacing(16)

        self.ok_button = QPushButton("✓  OK")
        self.ok_button.setFixedHeight(60)
        self.ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.SUCCESS};
                color: #000;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.SUCCESS_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #004400;
                color: {DarkTheme.TEXT_DISABLED};
            }}
        """)
        self.ok_button.clicked.connect(lambda: self._capture_sample("OK"))
        self.ok_button.setEnabled(False)
        layout.addWidget(self.ok_button, stretch=1)

        self.not_ok_button = QPushButton("✕  NOT OK")
        self.not_ok_button.setFixedHeight(60)
        self.not_ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.not_ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ERROR};
                color: #fff;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.ERROR_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #440000;
                color: {DarkTheme.TEXT_DISABLED};
            }}
        """)
        self.not_ok_button.clicked.connect(lambda: self._capture_sample("NOT_OK"))
        self.not_ok_button.setEnabled(False)
        layout.addWidget(self.not_ok_button, stretch=1)

        return layout

    def _create_gallery_panel(self) -> QWidget:
        """Create the gallery panel."""
        panel = QWidget()
        panel.setFixedWidth(280)
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Recent Captures")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Gallery scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {DarkTheme.BG_PRIMARY};
                border: none;
                border-radius: 8px;
            }}
        """)

        gallery_widget = QWidget()
        self.gallery_layout = QVBoxLayout(gallery_widget)
        self.gallery_layout.setContentsMargins(8, 8, 8, 8)
        self.gallery_layout.setSpacing(8)
        self.gallery_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        empty_label = QLabel("No captures yet")
        empty_label.setStyleSheet(f"color: {DarkTheme.TEXT_DISABLED}; padding: 20px;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setObjectName("empty_gallery_label")
        self.gallery_layout.addWidget(empty_label)

        scroll.setWidget(gallery_widget)
        layout.addWidget(scroll, stretch=1)

        return panel

    def _capture_sample(self, label_type: str):
        """Capture and save a sample image."""
        if not self.parent_window or not hasattr(self.parent_window, 'get_current_frame'):
            return

        frame = self.parent_window.get_current_frame()
        if frame is None:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        if label_type == "OK":
            save_path = self.ok_path / f"ok_{timestamp}.jpg"
            self.ok_samples += 1
        else:
            category = self.defect_category_combo.currentText().replace(" ", "_").lower()
            save_path = self.not_ok_path / f"notok_{category}_{timestamp}.jpg"
            self.not_ok_samples += 1

        cv2.imwrite(str(save_path), frame)
        self.total_samples += 1

        self._update_collect_stats()
        self._add_to_gallery(save_path, label_type)

    def _update_collect_stats(self):
        """Update collection statistics."""
        if hasattr(self, 'collect_total_label'):
            self.collect_total_label.setText(f"Total: {self.total_samples}")
        if hasattr(self, 'collect_ok_label'):
            self.collect_ok_label.setText(f"OK: {self.ok_samples}")
        if hasattr(self, 'collect_notok_label'):
            self.collect_notok_label.setText(f"NOT OK: {self.not_ok_samples}")

    def _add_to_gallery(self, image_path: Path, label_type: str):
        """Add thumbnail to gallery."""
        # Remove empty label
        if len(self.gallery_items) == 0:
            for i in range(self.gallery_layout.count()):
                widget = self.gallery_layout.itemAt(i).widget()
                if widget and widget.objectName() == "empty_gallery_label":
                    widget.deleteLater()
                    break

        thumb = QWidget()
        thumb.setFixedHeight(70)
        thumb.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-radius: 6px;
                border: 2px solid {DarkTheme.SUCCESS if label_type == 'OK' else DarkTheme.ERROR};
            }}
        """)

        layout = QHBoxLayout(thumb)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Thumbnail image
        pixmap = QPixmap(str(image_path))
        if not pixmap.isNull():
            scaled = pixmap.scaled(58, 58, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            img_label = QLabel()
            img_label.setPixmap(scaled)
            layout.addWidget(img_label)

        # Info
        info = QVBoxLayout()
        info.setSpacing(2)

        type_label = QLabel(label_type)
        type_label.setStyleSheet(f"color: {DarkTheme.SUCCESS if label_type == 'OK' else DarkTheme.ERROR}; font-size: 11px; font-weight: bold;")
        info.addWidget(type_label)

        name_label = QLabel(image_path.name[:15] + "..." if len(image_path.name) > 15 else image_path.name)
        name_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 10px;")
        info.addWidget(name_label)

        info.addStretch()
        layout.addLayout(info)

        self.gallery_layout.insertWidget(0, thumb)
        self.gallery_items.append(thumb)

        if len(self.gallery_items) > 30:
            old = self.gallery_items.pop(0)
            old.deleteLater()

    def _load_existing_samples(self):
        """Load existing samples from storage."""
        if self.ok_path.exists():
            for img in sorted(self.ok_path.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                self.ok_samples += 1
                self.total_samples += 1
                self._add_to_gallery(img, "OK")

        if self.not_ok_path.exists():
            for img in sorted(self.not_ok_path.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                self.not_ok_samples += 1
                self.total_samples += 1
                self._add_to_gallery(img, "NOT_OK")

        self._update_collect_stats()

    # ============== Annotate Page ==============

    def _create_annotate_page(self) -> QWidget:
        """Create the Annotate tab page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with title and buttons
        header = QHBoxLayout()

        title_section = QVBoxLayout()
        title = QLabel("Annotate Images")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 18px; font-weight: bold;")
        title_section.addWidget(title)

        self.image_info_label = QLabel("Image 0 of 0 - Draw boxes around defects")
        self.image_info_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        title_section.addWidget(self.image_info_label)

        header.addLayout(title_section)
        header.addStretch()

        # Skip button
        skip_btn = QPushButton("⏭ Skip")
        skip_btn.setFixedHeight(40)
        skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        skip_btn.setStyleSheet(f"""
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
        skip_btn.clicked.connect(self._next_image)
        header.addWidget(skip_btn)

        # Save & Next button
        save_btn = QPushButton("💾 Save & Next")
        save_btn.setFixedHeight(40)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
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
        save_btn.clicked.connect(self._save_and_next)
        header.addWidget(save_btn)

        layout.addLayout(header)

        # Main content
        content = QHBoxLayout()
        content.setSpacing(16)

        # Canvas
        self.canvas = AnnotationCanvas()
        self.canvas.annotation_added.connect(self._on_annotation_added)
        self.canvas.annotation_deleted.connect(self._on_annotation_deleted)
        content.addWidget(self.canvas, stretch=1)

        # Right sidebar
        sidebar = self._create_annotate_sidebar()
        content.addWidget(sidebar)

        layout.addLayout(content)

        return page

    def _create_annotate_sidebar(self) -> QWidget:
        """Create the annotation sidebar."""
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_SECONDARY};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Label Type section
        label_header = QLabel("Label Type")
        label_header.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        layout.addWidget(label_header)

        self.labels_container = QVBoxLayout()
        self.labels_container.setSpacing(8)
        layout.addLayout(self.labels_container)

        layout.addSpacing(16)

        # Annotations section
        ann_header = QHBoxLayout()
        ann_title = QLabel("Annotations")
        ann_title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        ann_header.addWidget(ann_title)

        self.annotations_count = QLabel("(0)")
        self.annotations_count.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 14px;")
        ann_header.addWidget(self.annotations_count)
        ann_header.addStretch()

        layout.addLayout(ann_header)

        # Annotations list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)

        ann_list = QWidget()
        self.annotations_list_layout = QVBoxLayout(ann_list)
        self.annotations_list_layout.setContentsMargins(0, 0, 0, 0)
        self.annotations_list_layout.setSpacing(4)
        self.annotations_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(ann_list)
        layout.addWidget(scroll, stretch=1)

        return sidebar

    def _load_annotation_data(self):
        """Load images and labels for annotation."""
        self.db.sync_images_from_folder("storage/dataset")
        self.labels = self.db.get_labels()
        self._update_label_buttons()

        if self.labels:
            self._select_label(self.labels[0])

        self.images = self.db.get_all_images()
        self.current_index = 0

        if self.images:
            self._load_current_image()

        self._update_image_counter()

    def _update_label_buttons(self):
        """Update label buttons."""
        for btn in self.label_buttons:
            btn.deleteLater()
        self.label_buttons.clear()

        for label in self.labels:
            btn = LabelButton(label)
            btn.clicked.connect(lambda checked, l=label: self._select_label(l))
            self.labels_container.addWidget(btn)
            self.label_buttons.append(btn)

    def _select_label(self, label: LabelRecord):
        """Select a label for annotation."""
        self.current_label = label

        for btn in self.label_buttons:
            btn.set_selected(btn.label.id == label.id)

        if self.canvas:
            self.canvas.set_current_class(label.id, label.name, label.color)

    def _load_current_image(self):
        """Load the current image."""
        if not self.images or self.current_index >= len(self.images):
            return

        image = self.images[self.current_index]

        if self.canvas.load_image(image.path):
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
        """Update the annotations list."""
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

            item = QWidget()
            item.setFixedHeight(36)
            item_layout = QHBoxLayout(item)
            item_layout.setContentsMargins(8, 4, 8, 4)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            item_layout.addWidget(dot)

            name = QLabel(ann.class_name)
            name.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 12px;")
            item_layout.addWidget(name)

            item_layout.addStretch()

            del_btn = QPushButton("✕")
            del_btn.setFixedSize(24, 24)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(f"""
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
            del_btn.clicked.connect(lambda checked, aid=ann.id: self._on_annotation_deleted(aid))
            item_layout.addWidget(del_btn)

            self.annotations_list_layout.addWidget(item)

    def _update_image_counter(self):
        """Update the image counter."""
        total = len(self.images)
        current = self.current_index + 1 if total > 0 else 0
        self.image_info_label.setText(f"Image {current} of {total} - Draw boxes around defects")

    def _prev_image(self):
        """Go to previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.canvas.clear_annotations()
            self._load_current_image()
            self._update_image_counter()

    def _next_image(self):
        """Go to next image."""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.canvas.clear_annotations()
            self._load_current_image()
            self._update_image_counter()

    def _save_and_next(self):
        """Save current and go to next."""
        self._next_image()

    def _on_annotation_added(self, class_id: int, x_center: float, y_center: float,
                              width: float, height: float):
        """Handle new annotation."""
        if not self.images or self.current_index >= len(self.images):
            return

        image = self.images[self.current_index]
        annotation_id = self.db.add_annotation(image.id, class_id, x_center, y_center, width, height)

        label = next((l for l in self.labels if l.id == class_id), None)
        if label:
            self.canvas.add_annotation(
                class_id, label.name, label.color,
                x_center, y_center, width, height,
                annotation_id
            )

        self._update_annotations_list()

    def _on_annotation_deleted(self, annotation_id: int):
        """Handle annotation deletion."""
        self.db.delete_annotation(annotation_id)
        self.canvas.clear_annotations()
        self._load_current_image()

    # ============== Train Model Page ==============

    def _create_train_page(self) -> QWidget:
        """Create the Train Model tab page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Header
        title = QLabel("Train Model")
        title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Create a computer vision model from your annotated data")
        subtitle.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(subtitle)

        # Training Configuration card
        config_card = QWidget()
        config_card.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(20, 20, 20, 20)
        config_layout.setSpacing(16)

        config_title = QLabel("Training Configuration")
        config_title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        config_layout.addWidget(config_title)

        # Model name
        name_label = QLabel("Model Name")
        name_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        config_layout.addWidget(name_label)

        self.model_name_input = QLineEdit()
        self.model_name_input.setText(f"Model-{int(time.time())}")
        self.model_name_input.setFixedHeight(45)
        self.model_name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {DarkTheme.BG_INPUT};
                color: {DarkTheme.TEXT_PRIMARY};
                border: 1px solid {DarkTheme.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 0 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {DarkTheme.PRIMARY};
            }}
        """)
        config_layout.addWidget(self.model_name_input)

        layout.addWidget(config_card)

        # Dataset Summary card
        summary_card = QWidget()
        summary_card.setStyleSheet(f"""
            QWidget {{
                background-color: {DarkTheme.BG_CARD};
                border-radius: 12px;
            }}
        """)
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(20, 20, 20, 20)
        summary_layout.setSpacing(16)

        summary_title = QLabel("Dataset Summary")
        summary_title.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        summary_layout.addWidget(summary_title)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(32)

        # Total Images
        total_col = QVBoxLayout()
        total_label = QLabel("Total Images")
        total_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        total_col.addWidget(total_label)

        self.train_total_images = QLabel("0")
        self.train_total_images.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 28px; font-weight: bold;")
        total_col.addWidget(self.train_total_images)
        stats_row.addLayout(total_col)

        # Defect Labels
        defect_col = QVBoxLayout()
        defect_label = QLabel("Defect Labels")
        defect_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        defect_col.addWidget(defect_label)

        self.train_defect_labels = QLabel("0")
        self.train_defect_labels.setStyleSheet(f"color: {DarkTheme.ERROR}; font-size: 28px; font-weight: bold;")
        defect_col.addWidget(self.train_defect_labels)
        stats_row.addLayout(defect_col)

        # Pass Labels
        pass_col = QVBoxLayout()
        pass_label = QLabel("Pass Labels")
        pass_label.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        pass_col.addWidget(pass_label)

        self.train_pass_labels = QLabel("0")
        self.train_pass_labels.setStyleSheet(f"color: {DarkTheme.SUCCESS}; font-size: 28px; font-weight: bold;")
        pass_col.addWidget(self.train_pass_labels)
        stats_row.addLayout(pass_col)

        stats_row.addStretch()
        summary_layout.addLayout(stats_row)

        layout.addWidget(summary_card)

        layout.addStretch()

        # Start Training button
        train_btn = QPushButton("▶  Start Training")
        train_btn.setFixedHeight(56)
        train_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        train_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY_HOVER};
            }}
        """)
        train_btn.clicked.connect(self._start_training)
        layout.addWidget(train_btn)

        return page

    def _refresh_train_stats(self):
        """Refresh training page statistics."""
        stats = self.db.get_project_stats()

        if self.train_total_images:
            self.train_total_images.setText(str(stats.total_images))
        if self.train_defect_labels:
            self.train_defect_labels.setText(str(stats.defect_labels))
        if self.train_pass_labels:
            self.train_pass_labels.setText(str(stats.pass_labels))

    def _start_training(self):
        """Start model training."""
        model_name = self.model_name_input.text()
        print(f"Starting training for model: {model_name}")
        # TODO: Implement actual training logic

    # ============== Public Methods ==============

    def showEvent(self, event):
        """Refresh data when page is shown."""
        super().showEvent(event)
        self._refresh_stats()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if self.current_tab == 2:  # Annotate tab
            if event.key() == Qt.Key.Key_Left:
                self._prev_image()
            elif event.key() == Qt.Key.Key_Right:
                self._next_image()
            elif event.key() == Qt.Key.Key_1 and self.labels:
                self._select_label(self.labels[0])
            elif event.key() == Qt.Key.Key_2 and len(self.labels) > 1:
                self._select_label(self.labels[1])
        super().keyPressEvent(event)
