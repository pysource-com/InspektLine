"""Inspection orchestration service.

Combines CameraService + detector model for live inspection.
Inference runs on a dedicated background thread.
No Qt dependency.
"""

import os
import re
import json
import threading
import time
from typing import List, Dict, Any, Optional

import numpy as np

from services.camera_service import CameraService
from services.settings_service import SettingsService


def _parse_frequency_seconds(freq_str: str) -> float:
    """Convert a human-readable frequency string to seconds.

    Examples: ``"Every 1.5 seconds"`` → 1.5, ``"Every 500 ms"`` → 0.5
    Falls back to 1.5 seconds on parse failure.
    """
    try:
        m = re.search(r"([\d.]+)\s*(s|sec|second|ms|millisecond)", freq_str, re.IGNORECASE)
        if m:
            value = float(m.group(1))
            unit = m.group(2).lower()
            if unit.startswith("ms") or unit.startswith("milli"):
                return value / 1000.0
            return value
    except Exception:
        pass
    return 1.5


class InspectionService:
    """Orchestrates real-time inspection using camera frames + detector.

    Inference runs on a **background thread** so the GUI frame loop is
    never blocked.  The main thread can read the latest results at any
    time via :pyattr:`latest_detections`.

    Usage::

        svc = InspectionService(settings, camera_service)
        svc.load_model("path/to/model")
        svc.start()
        ...
        svc.stop()
    """

    def __init__(self, settings: SettingsService, camera: CameraService):
        self._settings = settings
        self._camera = camera

        # Detector instance (classifier or RF-DETR)
        self._detector: Any = None
        self._task_type: Optional[str] = None  # "classification" | "detection" | "segmentation"

        # Thread-safe frame hand-off (main → inference thread)
        self._frame_lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None

        # Thread-safe results (inference thread → main)
        self._results_lock = threading.Lock()
        self._latest_detections: List[Dict[str, Any]] = []

        # Background thread
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ---- properties --------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def has_model(self) -> bool:
        return self._detector is not None

    @property
    def task_type(self) -> Optional[str]:
        return self._task_type

    # For backward compat — old code references model_type
    @property
    def model_type(self) -> Optional[str]:
        return self._task_type

    @property
    def latest_detections(self) -> List[Dict[str, Any]]:
        """Return the most recent detection results (thread-safe read)."""
        with self._results_lock:
            return list(self._latest_detections)

    # ---- model loading -----------------------------------------------------

    def load_model(self, model_path: str) -> bool:
        """Load a detection / classification model.

        The backend is chosen based on ``settings.detection.task_type``:
        - ``"classification"``  → HuggingFace transformer classifier
        - ``"detection"``       → RF-DETR object detector (.pth checkpoint)
        - ``"segmentation"``    → RF-DETRSeg instance segmentation (.pth checkpoint)

        Returns True on success.
        """
        task_type = self._settings.detection.task_type

        try:
            if task_type in ("detection", "segmentation"):
                self._detector = self._load_rfdetr(model_path)
            else:
                self._detector = self._load_classifier(model_path)

            self._task_type = task_type
            self._settings.detection.active_model_path = model_path
            return True
        except Exception as exc:
            print(f"[InspectionService] Failed to load model: {exc}")
            self._detector = None
            self._task_type = None
            return False

    def _load_classifier(self, model_path: str):
        from detector.classifier import TransformerImageClassifier
        return TransformerImageClassifier(model_name=model_path)

    def _load_rfdetr(self, checkpoint_path: str):
        from detector.rfdetr_detector import RFDETRDetector

        det_settings = self._settings.detection

        # Try to load class names from a classes.txt / classes.json
        # alongside the checkpoint file.
        class_names = self._discover_class_names(checkpoint_path)
        num_classes = det_settings.num_classes
        if class_names:
            num_classes = len(class_names)

        return RFDETRDetector(
            checkpoint_path=checkpoint_path,
            class_names=class_names,
            num_classes=num_classes,
            model_variant=det_settings.model_variant,
            resolution=det_settings.model_resolution,
        )

    @staticmethod
    def _discover_class_names(checkpoint_path: str) -> Optional[List[str]]:
        """Look for ``classes.txt`` or ``classes.json`` next to the checkpoint."""
        parent = os.path.dirname(checkpoint_path)
        txt = os.path.join(parent, "classes.txt")
        jsn = os.path.join(parent, "classes.json")

        if os.path.isfile(txt):
            with open(txt, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        if os.path.isfile(jsn):
            with open(jsn, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        return None

    # ---- frame submission --------------------------------------------------

    def submit_frame(self, frame: np.ndarray) -> None:
        """Hand a new frame to the inference thread (non-blocking).

        Only the *latest* frame is kept — older un-processed frames are
        silently dropped so inference never falls behind.
        """
        with self._frame_lock:
            self._latest_frame = frame

    # ---- single-shot inference (backward compat) ---------------------------

    def inspect_frame(self, frame) -> List[Dict[str, Any]]:
        """Run inference on a single frame (blocking, for one-off use).

        Returns list of prediction dicts.
        """
        if self._detector is None:
            return []
        try:
            return self._run_inference(frame)
        except Exception as exc:
            print(f"[InspectionService] Inference error: {exc}")
            return []

    # ---- background inference thread ---------------------------------------

    def start(self) -> None:
        """Start the background inference thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._inference_loop, daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the background inference thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        # Clear stale results
        with self._results_lock:
            self._latest_detections = []

    def _inference_loop(self) -> None:
        """Continuously grab the latest frame, run inference, store results."""
        interval = _parse_frequency_seconds(
            self._settings.detection.detection_frequency
        )
        while self._running:
            if self._detector is None:
                time.sleep(interval)
                continue

            # Grab latest frame
            with self._frame_lock:
                frame = self._latest_frame
                self._latest_frame = None  # mark consumed

            if frame is None:
                time.sleep(0.01)  # nothing to process
                continue

            try:
                results = self._run_inference(frame)
                with self._results_lock:
                    self._latest_detections = results
            except Exception as exc:
                print(f"[InspectionService] Inference error: {exc}")

            time.sleep(interval)

    # ---- internal ----------------------------------------------------------

    def _run_inference(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Dispatch to the loaded detector backend."""
        if self._task_type in ("detection", "segmentation"):
            return self._infer_rfdetr(frame)
        else:
            return self._infer_classifier(frame)

    def _infer_classifier(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Run the transformer classifier on a frame."""
        import cv2
        from PIL import Image

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        results = self._detector.predict([pil_img], top_k=1)
        return results[0] if results else []

    def _infer_rfdetr(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Run the RF-DETR detector on a frame."""
        threshold = self._settings.detection.confidence_threshold / 100.0
        return self._detector.predict(frame, confidence_threshold=threshold)
