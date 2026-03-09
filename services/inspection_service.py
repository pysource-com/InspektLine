"""Inspection orchestration service.

Combines CameraService + detector model for live inspection.
No Qt dependency.
"""

from typing import List, Dict, Any

from services.camera_service import CameraService
from services.settings_service import SettingsService


class InspectionService:
    """Orchestrates real-time inspection using camera frames + classifier.

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
        self._classifier = None
        self._is_running = False
        self._last_results: List[Dict[str, Any]] = []

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def has_model(self) -> bool:
        return self._classifier is not None

    @property
    def last_results(self) -> List[Dict[str, Any]]:
        return self._last_results

    def load_model(self, model_path: str) -> bool:
        """Load a trained classification model.

        Returns True on success.
        """
        try:
            from detector.classifier import TransformerImageClassifier
            self._classifier = TransformerImageClassifier(model_name=model_path)
            self._settings.detection.active_model_path = model_path
            return True
        except Exception as exc:
            print(f"[InspectionService] Failed to load model: {exc}")
            self._classifier = None
            return False

    def inspect_frame(self, frame) -> List[Dict[str, Any]]:
        """Run inference on a single frame.

        Returns list of prediction dicts ``[{"label": str, "score": float, "id": int}]``.
        """
        if self._classifier is None:
            return []
        try:
            import cv2
            from PIL import Image
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            results = self._classifier.predict([pil_img], top_k=1)
            self._last_results = results[0] if results else []
            return self._last_results
        except Exception as exc:
            print(f"[InspectionService] Inference error: {exc}")
            return []

    def start(self) -> None:
        """Mark inspection as running."""
        self._is_running = True

    def stop(self) -> None:
        """Mark inspection as stopped."""
        self._is_running = False

