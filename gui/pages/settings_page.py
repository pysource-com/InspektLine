"""Settings page — camera selection and camera parameters."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QFrame, QComboBox, QSlider,
                                QCheckBox, QScrollArea)
from PySide6.QtCore import Signal, Qt
from gui.styles import DarkTheme, StyleSheets


class SettingsPage(QWidget):
    """Settings page: camera type/device selection + live camera parameters.

    Receives services via constructor injection from MainWindow._open_dialog().
    """

    # Signal when settings dialog should close
    close_requested = Signal()

    # Mapping between UI display names and internal camera type identifiers
    CAMERA_TYPE_MAP = {
        "USB Webcam": "usb-standard",
        "Intel RealSense": "intel-realsense",
        "Daheng GigE": "daheng-gige",
    }
    CAMERA_TYPE_REVERSE = {v: k for k, v in CAMERA_TYPE_MAP.items()}

    def __init__(self, settings_service=None, camera_service=None,
                 inspection_service=None, parent=None, **kwargs):
        super().__init__(parent)
        self._settings = settings_service
        self._camera = camera_service
        self._parent_window = parent
        # Keeps references to dynamically-created parameter widgets
        self._param_widgets: dict[str, dict] = {}
        self.init_ui()

    # ================================================================
    # UI Init
    # ================================================================

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(30, 25, 30, 25)
        self._content_layout.setSpacing(25)

        # Header
        self._content_layout.addWidget(self._create_header())

        # Camera Parameters card (built empty, populated dynamically)
        # Must be created before camera section, which triggers _refresh_parameters()
        self._params_card_container = self._create_params_section()

        # Camera Selection card
        self._content_layout.addWidget(self._create_camera_section())

        self._content_layout.addWidget(self._params_card_container)

        self._content_layout.addStretch()

        # Done button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.done_button = QPushButton("Done")
        self.done_button.setFixedSize(100, 40)
        self.done_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.PRIMARY};
                color: white; border: none; border-radius: 6px;
                font-size: 14px; font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {DarkTheme.PRIMARY_HOVER}; }}
        """)
        self.done_button.clicked.connect(self._on_done_clicked)
        btn_row.addWidget(self.done_button)
        self._content_layout.addLayout(btn_row)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    # ---- header ------------------------------------------------------------

    def _create_header(self):
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)

        tc = QWidget()
        tl = QVBoxLayout(tc)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(5)
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff;")
        tl.addWidget(title)
        subtitle = QLabel("Select camera and adjust parameters")
        subtitle.setStyleSheet(f"font-size: 13px; color: {DarkTheme.TEXT_SECONDARY};")
        tl.addWidget(subtitle)
        hl.addWidget(tc)
        hl.addStretch()

        close_btn = QPushButton("\u00d7")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DarkTheme.TEXT_SECONDARY};
                border: none; font-size: 24px;
            }}
            QPushButton:hover {{ color: {DarkTheme.TEXT_PRIMARY}; }}
        """)
        close_btn.clicked.connect(self._on_close_clicked)
        hl.addWidget(close_btn)
        return header

    # ---- helpers -----------------------------------------------------------

    def _section_title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #fff; margin-bottom: 8px;")
        return lbl

    def _card(self):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_SECONDARY};
                border: 1px solid {DarkTheme.BORDER_PRIMARY};
                border-radius: 10px; padding: 15px;
            }}
        """)
        return card

    # ================================================================
    # Camera Selection
    # ================================================================

    def _create_camera_section(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._section_title("Camera Selection"))

        card = self._card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(15, 15, 15, 15)
        cl.setSpacing(12)

        # Camera Type
        cl.addWidget(self._field_label("Camera Type"))
        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems(list(self.CAMERA_TYPE_MAP.keys()))
        self.camera_type_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_type_combo.setFixedHeight(45)
        cl.addWidget(self.camera_type_combo)

        if self._settings:
            display = self.CAMERA_TYPE_REVERSE.get(
                self._settings.camera.camera_type, "USB Webcam")
            idx = self.camera_type_combo.findText(display)
            if idx >= 0:
                self.camera_type_combo.setCurrentIndex(idx)

        # Camera Device
        cl.addWidget(self._field_label("Camera Device", margin_top=6))
        self.camera_device_combo = QComboBox()
        self.camera_device_combo.setStyleSheet(StyleSheets.get_combobox_style())
        self.camera_device_combo.setFixedHeight(45)
        cl.addWidget(self.camera_device_combo)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 11px; "
            f"font-style: italic; margin-top: 4px;")
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        cl.addWidget(self.status_label)

        self.refresh_btn = QPushButton("Refresh devices")
        self.refresh_btn.setFixedHeight(36)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DarkTheme.PRIMARY};
                border: 1px solid {DarkTheme.PRIMARY};
                border-radius: 6px; font-size: 12px; padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {DarkTheme.PRIMARY}; color: white;
            }}
        """)
        self.refresh_btn.clicked.connect(self._populate_camera_devices)
        cl.addWidget(self.refresh_btn)

        layout.addWidget(card)

        self.camera_type_combo.currentIndexChanged.connect(
            lambda _: self._populate_camera_devices())
        self._populate_camera_devices()

        return container

    def _field_label(self, text, margin_top=0):
        lbl = QLabel(text)
        style = f"font-size: 12px; color: {DarkTheme.TEXT_SECONDARY};"
        if margin_top:
            style += f" margin-top: {margin_top}px;"
        lbl.setStyleSheet(style)
        return lbl

    def _populate_camera_devices(self):
        internal_type = self.CAMERA_TYPE_MAP.get(
            self.camera_type_combo.currentText(), "usb-standard")

        devices = []
        if self._camera is not None:
            try:
                devices = self._camera.get_cameras_list(internal_type)
            except Exception as exc:
                print(f"[SettingsPage] Enumeration error: {exc}")

        self.camera_device_combo.blockSignals(True)
        self.camera_device_combo.clear()
        if devices:
            for dev in devices:
                self.camera_device_combo.addItem(
                    dev.get("name", f"Device {dev['index']}"),
                    userData=dev["index"])
            self.status_label.hide()
            if self._settings:
                saved = self._settings.camera.camera_index
                for i in range(self.camera_device_combo.count()):
                    if self.camera_device_combo.itemData(i) == saved:
                        self.camera_device_combo.setCurrentIndex(i)
                        break
        else:
            self.camera_device_combo.addItem("No devices found")
            self.status_label.setText(
                "No cameras detected for this type. Check connections and drivers.")
            self.status_label.show()
        self.camera_device_combo.blockSignals(False)

        # Refresh the parameters panel for the new camera type
        self._refresh_parameters()

    # ================================================================
    # Camera Parameters
    # ================================================================

    def _create_params_section(self):
        """Create the (initially hidden) camera parameters card."""
        self._params_container = QWidget()
        layout = QVBoxLayout(self._params_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._section_title("Camera Parameters"))

        self._params_card = self._card()
        self._params_card_layout = QVBoxLayout(self._params_card)
        self._params_card_layout.setContentsMargins(15, 15, 15, 15)
        self._params_card_layout.setSpacing(14)

        # Placeholder text (shown when no params available)
        self._params_placeholder = QLabel(
            "Camera parameters will appear here once a supported camera is connected.")
        self._params_placeholder.setStyleSheet(
            f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
        self._params_placeholder.setWordWrap(True)
        self._params_card_layout.addWidget(self._params_placeholder)

        layout.addWidget(self._params_card)
        return self._params_container

    def _refresh_parameters(self):
        """Query the camera service for available parameters and rebuild controls."""
        # Clear existing parameter widgets
        self._param_widgets.clear()
        while self._params_card_layout.count():
            item = self._params_card_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        params: list[dict] = []
        if self._camera is not None:
            try:
                params = self._camera.get_camera_parameters()
            except Exception:
                pass

        if not params:
            self._params_placeholder = QLabel(
                "Camera parameters will appear here once a supported camera is connected.")
            self._params_placeholder.setStyleSheet(
                f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
            self._params_placeholder.setWordWrap(True)
            self._params_card_layout.addWidget(self._params_placeholder)
            return

        for p in params:
            key = p["key"]
            kind = p["kind"]

            # Skip parameters whose value is not readable
            if p.get("value") is None:
                continue

            if kind in ("float", "int"):
                # Also need valid min/max for slider
                if p.get("min") is None or p.get("max") is None:
                    continue
                # Skip parameters whose min/max/value overflow a 32-bit int
                # (sentinel values from camera SDKs like Daheng)
                _INT32_MIN, _INT32_MAX = -(2 ** 31), 2 ** 31 - 1
                try:
                    lo, hi, v = p["min"], p["max"], p["value"]
                    if kind == "float":
                        vals = [int(lo * 100), int(hi * 100), int(v * 100)]
                    else:
                        vals = [int(lo), int(hi), int(v)]
                    if any(x < _INT32_MIN or x > _INT32_MAX for x in vals):
                        continue
                except (OverflowError, ValueError):
                    continue
                widget_row = self._build_slider_row(p)
            elif kind in ("bool", "enum_auto"):
                widget_row = self._build_toggle_row(p)
            else:
                continue

            self._params_card_layout.addWidget(widget_row)

    # ---- parameter widget builders -----------------------------------------

    def _build_slider_row(self, p: dict) -> QWidget:
        """Build a labelled slider for a numeric parameter."""
        key = p["key"]
        label_text = p["label"]
        unit = p["unit"]
        val = p["value"]
        lo = p["min"]
        hi = p["max"]
        inc = p.get("inc", 1)
        kind = p["kind"]

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(row)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(4)

        # Top: label + value readout
        top = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        top.addWidget(lbl)
        top.addStretch()

        display_val = f"{val:.2f}" if kind == "float" else str(int(val))
        if unit:
            display_val += f" {unit}"
        val_lbl = QLabel(display_val)
        val_lbl.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
        val_lbl.setMinimumWidth(80)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(val_lbl)
        vl.addLayout(top)

        # Slider — always integer internally; for floats we scale ×100
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setStyleSheet(self._slider_style())

        if kind == "float":
            scale = 100
            slider.setMinimum(int(lo * scale))
            slider.setMaximum(int(hi * scale))
            slider.setValue(int(val * scale))
            slider.setSingleStep(max(1, int(inc * scale)))
        else:
            scale = 1
            slider.setMinimum(int(lo))
            slider.setMaximum(int(hi))
            slider.setValue(int(val))
            slider.setSingleStep(max(1, int(inc)))

        # On change → update value label + send to camera
        def _on_changed(raw, _key=key, _kind=kind, _unit=unit, _scale=scale, _lbl=val_lbl):
            real = raw / _scale if _kind == "float" else raw
            disp = f"{real:.2f}" if _kind == "float" else str(int(real))
            if _unit:
                disp += f" {_unit}"
            _lbl.setText(disp)
            if self._camera is not None:
                self._camera.set_camera_parameter(_key, real)

        slider.valueChanged.connect(_on_changed)

        vl.addWidget(slider)

        # Range labels
        range_row = QHBoxLayout()
        lo_lbl = QLabel(f"{lo:.2f}" if kind == "float" else str(int(lo)))
        lo_lbl.setStyleSheet(f"color: {DarkTheme.TEXT_DISABLED}; font-size: 10px;")
        range_row.addWidget(lo_lbl)
        range_row.addStretch()
        hi_lbl = QLabel(f"{hi:.2f}" if kind == "float" else str(int(hi)))
        hi_lbl.setStyleSheet(f"color: {DarkTheme.TEXT_DISABLED}; font-size: 10px;")
        hi_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        range_row.addWidget(hi_lbl)
        vl.addLayout(range_row)

        self._param_widgets[key] = {"slider": slider, "val_lbl": val_lbl, "scale": scale}
        return row

    def _build_toggle_row(self, p: dict) -> QWidget:
        """Build a labelled checkbox for a boolean/enum_auto parameter."""
        key = p["key"]
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)

        cb = QCheckBox(p["label"])
        cb.setChecked(bool(p["value"]))
        cb.setStyleSheet(StyleSheets.get_checkbox_style())

        def _toggled(state, _key=key):
            checked = state == Qt.CheckState.Checked.value
            if self._camera is not None:
                self._camera.set_camera_parameter(_key, checked)

        cb.stateChanged.connect(_toggled)
        hl.addWidget(cb)

        self._param_widgets[key] = {"checkbox": cb}
        return row

    # ---- slider style (inline, matching app theme) -------------------------

    @staticmethod
    def _slider_style():
        return f"""
            QSlider::groove:horizontal {{
                background: {DarkTheme.BG_INPUT}; height: 6px; border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {DarkTheme.PRIMARY}; border: 2px solid white;
                width: 14px; height: 14px; margin: -5px 0; border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {DarkTheme.PRIMARY}; border-radius: 3px;
            }}
        """

    # ================================================================
    # Save / Close
    # ================================================================

    def _on_close_clicked(self):
        self.close_requested.emit()
        if self.parent() and hasattr(self.parent(), 'close'):
            self.parent().close()

    def _on_done_clicked(self):
        self._save_settings()
        self._on_close_clicked()

    def _save_settings(self):
        if not self._settings:
            return

        changed = False

        new_type = self.CAMERA_TYPE_MAP.get(
            self.camera_type_combo.currentText(), "usb-standard")
        if new_type != self._settings.camera.camera_type:
            self._settings.camera.camera_type = new_type
            changed = True

        device_data = self.camera_device_combo.currentData()
        new_index = device_data if device_data is not None else 0
        if new_index != self._settings.camera.camera_index:
            self._settings.camera.camera_index = new_index
            changed = True

        self._settings.save()

        if changed and self._parent_window and hasattr(self._parent_window, "refresh_camera"):
            self._parent_window.refresh_camera()
