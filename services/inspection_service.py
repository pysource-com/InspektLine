"""Inspection orchestration service.

Combines CameraService + detector model for live inspection.
Inference runs on a dedicated background thread.
No Qt dependency.
"""

import os
import json
import threading
import time
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from services.camera_service import CameraService
from services.settings_service import SettingsService
from detector.tracker import ObjectTracker


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
        self._frame_event = threading.Event()  # wakes inference thread on new frame

        # Thread-safe results (inference thread → main)
        self._results_lock = threading.Lock()
        self._latest_detections: List[Dict[str, Any]] = []

        # Pre-annotated frame (inference thread → main, avoids annotation on UI thread)
        self._annotated_lock = threading.Lock()
        self._latest_annotated_frame: Optional[np.ndarray] = None

        # Background thread
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Object tracker (ByteTrack + polygon ROI zone)
        self._tracker = ObjectTracker()
        self._tracker_lock = threading.Lock()
        self._tracking_enabled = False

        # Secondary classifier for two-stage ROI inspection
        self._classifier: Any = None
        self._classifier_lock = threading.Lock()

        # Classification results log: tracker_id → {label, score, timestamp}
        self._classification_log: Dict[int, Dict[str, Any]] = {}
        self._classification_log_lock = threading.Lock()

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

    @property
    def latest_annotated_frame(self) -> Optional[np.ndarray]:
        """Return the latest pre-annotated frame (thread-safe read).

        The inference thread draws detection overlays after each inference
        pass so the display thread can use this directly without re-drawing.
        """
        with self._annotated_lock:
            return self._latest_annotated_frame

    # ---- tracking / ROI properties -----------------------------------------

    @property
    def tracking_enabled(self) -> bool:
        return self._tracking_enabled

    @tracking_enabled.setter
    def tracking_enabled(self, value: bool) -> None:
        self._tracking_enabled = value
        if not value:
            with self._tracker_lock:
                self._tracker.reset()

    @property
    def zone_count(self) -> int:
        """Objects currently inside the ROI polygon."""
        with self._tracker_lock:
            return self._tracker.zone_count

    @property
    def total_entered(self) -> int:
        """Total unique objects that have entered the ROI polygon."""
        with self._tracker_lock:
            return self._tracker.total_entered

    @property
    def has_roi_polygon(self) -> bool:
        with self._tracker_lock:
            return self._tracker.has_polygon

    @property
    def roi_polygon(self) -> Optional[np.ndarray]:
        with self._tracker_lock:
            return self._tracker.polygon

    def set_roi_polygon(self, points: List[Tuple[int, int]]) -> None:
        """Set the ROI polygon (thread-safe). Points in frame coords."""
        with self._tracker_lock:
            self._tracker.set_polygon(points)
            self._tracking_enabled = True

    def clear_roi_polygon(self) -> None:
        """Remove the ROI polygon and reset counters."""
        with self._tracker_lock:
            self._tracker.clear_polygon()
        with self._classification_log_lock:
            self._classification_log.clear()

    def reset_roi_counts(self) -> None:
        """Reset zone counters without removing the polygon."""
        with self._tracker_lock:
            self._tracker.reset()

    # ---- secondary classifier (two-stage ROI inspection) -------------------

    @property
    def has_classifier(self) -> bool:
        """True if a secondary classification model is loaded."""
        return self._classifier is not None

    @property
    def classifier_path(self) -> Optional[str]:
        """Return the path of the currently loaded classifier, if any."""
        if self._classifier is not None:
            return getattr(self._classifier, "model_name", None)
        return None

    @property
    def classification_log(self) -> Dict[int, Dict[str, Any]]:
        """Return a snapshot of classification results keyed by tracker ID."""
        with self._classification_log_lock:
            return dict(self._classification_log)

    def load_classifier(self, model_path: str) -> bool:
        """Load a secondary classifier for two-stage ROI inspection.

        This classifier runs on objects that enter the ROI polygon:
        the segmentation model detects + segments, and the classifier
        categorises each cropped object (e.g. good / defective).

        Parameters
        ----------
        model_path : str
            Path to either:
            - A ``.pth`` checkpoint (loaded via *timm*, e.g. ConvNeXt)
            - A local HuggingFace model directory

        Returns True on success.
        """
        try:
            if model_path.lower().endswith(".pth"):
                from detector.classifier import TimmImageClassifier
                class_names = self._discover_class_names(model_path)
                classifier = TimmImageClassifier(
                    checkpoint_path=model_path,
                    class_names=class_names,
                )
            else:
                from detector.classifier import TransformerImageClassifier
                classifier = TransformerImageClassifier(model_name=model_path)

            with self._classifier_lock:
                self._classifier = classifier
            print(f"[InspectionService] Classifier loaded: {model_path}")
            return True
        except Exception as exc:
            print(f"[InspectionService] Failed to load classifier: {exc}")
            with self._classifier_lock:
                self._classifier = None
            return False

    def clear_classifier(self) -> None:
        """Unload the secondary classifier."""
        with self._classifier_lock:
            self._classifier = None
        with self._classification_log_lock:
            self._classification_log.clear()

    def clear_classification_log(self) -> None:
        """Clear the classification results log."""
        with self._classification_log_lock:
            self._classification_log.clear()

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

        # Only override resolution when the user explicitly changed it
        # from the model's own default (0 = use model default).
        resolution = det_settings.model_resolution
        variant = det_settings.model_variant
        default_res = RFDETRDetector.DEFAULT_RESOLUTION.get(variant, 0)
        use_resolution = resolution if (resolution and resolution != default_res) else None

        return RFDETRDetector(
            checkpoint_path=checkpoint_path,
            class_names=class_names,
            num_classes=num_classes,
            model_variant=variant,
            resolution=use_resolution,
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
        self._frame_event.set()  # wake the inference thread immediately

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
        self._frame_event.clear()
        self._thread = threading.Thread(
            target=self._inference_loop, daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the background inference thread."""
        self._running = False
        self._frame_event.set()  # wake thread so it can exit promptly
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        # Clear stale results
        with self._results_lock:
            self._latest_detections = []
        with self._annotated_lock:
            self._latest_annotated_frame = None
        with self._classification_log_lock:
            self._classification_log.clear()

    def _inference_loop(self) -> None:
        """Continuously grab the latest frame, run inference, store results.

        Uses an Event to wake up immediately when a new frame is
        submitted instead of polling with ``time.sleep()``.
        """
        from detector.annotate import draw_detections, draw_roi_polygon

        consecutive_errors = 0
        max_logged_errors = 3

        while self._running:
            # Block efficiently until a new frame arrives (or timeout to
            # re-check the running flag).
            self._frame_event.wait(timeout=0.5)
            self._frame_event.clear()

            if not self._running or self._detector is None:
                continue

            # Grab latest frame
            with self._frame_lock:
                frame = self._latest_frame
                self._latest_frame = None  # mark consumed

            if frame is None:
                continue

            try:
                results = self._run_inference(frame)

                # Run object tracking if enabled (detection / segmentation)
                if self._tracking_enabled and self._task_type in ("detection", "segmentation"):
                    with self._tracker_lock:
                        results = self._tracker.update(results)

                    # --- Two-stage classification on ROI-entering objects ---
                    with self._classifier_lock:
                        classifier = self._classifier

                    if classifier is not None:
                        results = self._classify_roi_objects(
                            frame, results, classifier
                        )

                # Pre-annotate the frame so the UI thread can display it
                # directly without doing expensive drawing work.
                draw_masks = self._task_type == "segmentation"
                annotated = draw_detections(
                    frame, results, draw_masks=draw_masks
                ) if results else frame.copy()

                # Draw ROI polygon overlay
                with self._tracker_lock:
                    if self._tracker.has_polygon:
                        annotated = draw_roi_polygon(
                            annotated,
                            self._tracker.polygon,
                            zone_count=self._tracker.zone_count,
                            total_entered=self._tracker.total_entered,
                        )

                with self._results_lock:
                    self._latest_detections = results
                with self._annotated_lock:
                    self._latest_annotated_frame = annotated

                consecutive_errors = 0  # reset on success
            except Exception as exc:
                consecutive_errors += 1
                if consecutive_errors <= max_logged_errors:
                    print(f"[InspectionService] Inference error: {exc}")
                if consecutive_errors == max_logged_errors:
                    print(
                        "[InspectionService] Suppressing further identical errors. "
                        "Fix the issue and restart inspection."
                    )

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

    # ---- two-stage classification ------------------------------------------

    def _classify_roi_objects(
        self,
        frame: np.ndarray,
        results: List[Dict[str, Any]],
        classifier,
    ) -> List[Dict[str, Any]]:
        """Run the secondary classifier on objects that just entered the ROI.

        For objects that were already classified on a previous frame, the
        cached result is re-attached so it persists on-screen.

        Parameters
        ----------
        frame : np.ndarray
            The original BGR frame (used for cropping).
        results : list[dict]
            Tracked detection dicts (must have ``tracker_id``,
            ``just_entered``, ``box``).
        classifier
            A loaded ``TransformerImageClassifier`` instance.

        Returns
        -------
        list[dict]
            The same dicts, enriched with a ``"classification"`` key
            where applicable.
        """

        for det in results:
            tid = det.get("tracker_id", -1)
            if tid < 0:
                continue

            # --- newly entered → classify now ---
            if det.get("just_entered", False):
                cls_result = self._classify_crop(frame, det["box"], classifier)
                if cls_result is not None:
                    det["classification"] = cls_result
                    with self._classification_log_lock:
                        self._classification_log[tid] = cls_result

            # --- previously classified → carry forward cached result ---
            elif tid >= 0:
                with self._classification_log_lock:
                    cached = self._classification_log.get(tid)
                if cached is not None:
                    det["classification"] = cached

        return results

    def _classify_crop(
        self,
        frame: np.ndarray,
        box: List[float],
        classifier,
    ) -> Optional[Dict[str, Any]]:
        """Crop the bounding box region and run the classifier.

        Returns
        -------
        dict or None
            ``{"label": str, "score": float, "timestamp": float}``
            on success, *None* on failure.
        """
        from detector.crop import extract_object_crop
        import cv2
        from PIL import Image

        try:
            crop = extract_object_crop(frame, box)
            rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            preds = classifier.predict([pil_img], top_k=1)
            if preds and preds[0]:
                top = preds[0][0]
                return {
                    "label": top["label"],
                    "score": top["score"],
                    "timestamp": time.time(),
                }
        except Exception as exc:
            print(f"[InspectionService] Classification error: {exc}")
        return None

