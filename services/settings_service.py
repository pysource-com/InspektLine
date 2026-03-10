"""Application settings with JSON persistence.

Single source of truth for all configurable parameters.
No Qt dependency — pure Python dataclass + JSON file.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


_DEFAULT_SETTINGS_PATH = Path("storage/settings.json")


@dataclass
class CameraSettings:
    """Camera-related settings."""
    camera_index: int = 0
    camera_type: str = "usb-standard"  # "usb-standard" | "intel-realsense" | "daheng-gige"
    resolution: str = "1920 x 1080 (Full HD)"
    frame_rate: str = "30 FPS"
    auto_focus_enabled: bool = False
    manual_focus_value: int = 128


@dataclass
class DetectionSettings:
    """Detection / inspection settings."""
    confidence_threshold: int = 85
    min_defect_size: int = 10
    detection_frequency: str = "Every 1.5 seconds"
    active_model_path: str = ""


@dataclass
class DatasetSettings:
    """Dataset collection settings."""
    dataset_dir: str = "storage/dataset"
    collection_mode: str = "images"  # "video" | "images"
    frame_skip: int = 5
    video_format: str = "mp4"


@dataclass
class AppSettings:
    """Root settings container."""
    camera: CameraSettings = field(default_factory=CameraSettings)
    detection: DetectionSettings = field(default_factory=DetectionSettings)
    dataset: DatasetSettings = field(default_factory=DatasetSettings)


class SettingsService:
    """Manages loading, saving, and accessing application settings.

    Usage::

        svc = SettingsService()           # loads from disk (or defaults)
        svc.settings.camera.camera_index  # read
        svc.settings.camera.camera_index = 1
        svc.save()                        # persist to JSON
    """

    def __init__(self, path: Optional[Path] = None):
        self._path = path or _DEFAULT_SETTINGS_PATH
        self.settings = AppSettings()
        self.load()

    # ---- persistence -------------------------------------------------------

    def load(self) -> None:
        """Load settings from JSON file. Missing keys keep their defaults."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if "camera" in data:
                for k, v in data["camera"].items():
                    if hasattr(self.settings.camera, k):
                        setattr(self.settings.camera, k, v)
            if "detection" in data:
                for k, v in data["detection"].items():
                    if hasattr(self.settings.detection, k):
                        setattr(self.settings.detection, k, v)
            if "dataset" in data:
                for k, v in data["dataset"].items():
                    if hasattr(self.settings.dataset, k):
                        setattr(self.settings.dataset, k, v)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[SettingsService] Could not load settings: {exc}")

    def save(self) -> None:
        """Persist current settings to JSON."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(asdict(self.settings), fh, indent=2)

    # ---- convenience shortcuts ---------------------------------------------

    @property
    def camera(self) -> CameraSettings:
        return self.settings.camera

    @property
    def detection(self) -> DetectionSettings:
        return self.settings.detection

    @property
    def dataset(self) -> DatasetSettings:
        return self.settings.dataset

