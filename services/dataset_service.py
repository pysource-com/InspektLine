"""Dataset capture & management service.

Handles image capture, storage, sample counting, and gallery loading.
No Qt dependency — pure Python + OpenCV.
"""

import cv2
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

from database.project_db import ProjectDatabase
from services.settings_service import SettingsService


@dataclass
class SampleRecord:
    """Lightweight record for a captured sample."""
    path: Path
    label: str  # "OK" | "NOT_OK"
    timestamp: float  # mtime


@dataclass
class DatasetStats:
    """Current dataset statistics."""
    total: int = 0
    ok: int = 0
    not_ok: int = 0


class DatasetService:
    """Manages dataset capture and sample statistics.

    Usage::

        svc = DatasetService(settings, db)
        svc.capture("OK", frame)
        svc.capture("NOT_OK", frame, defect_category="Crack")
        stats = svc.stats
        recent = svc.recent_samples
    """

    MAX_RECENT = 50

    def __init__(self, settings: SettingsService, db: ProjectDatabase):
        self._settings = settings
        self._db = db

        self._ok_path = Path(settings.storage_cfg.dataset_ok_path)
        self._notok_path = Path(settings.storage_cfg.dataset_notok_path)
        self._ok_path.mkdir(parents=True, exist_ok=True)
        self._notok_path.mkdir(parents=True, exist_ok=True)

        self._stats = DatasetStats()
        self._recent: List[SampleRecord] = []
        self._loaded = False

    @property
    def stats(self) -> DatasetStats:
        return self._stats

    @property
    def recent_samples(self) -> List[SampleRecord]:
        return list(self._recent)

    @property
    def ok_path(self) -> Path:
        return self._ok_path

    @property
    def notok_path(self) -> Path:
        return self._notok_path

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def capture(self, label: str, frame, defect_category: str = "") -> Path:
        """Save frame to disk and update counters. Returns path to saved image."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        if label == "OK":
            save_path = self._ok_path / f"ok_{timestamp}.jpg"
            self._stats.ok += 1
        else:
            tag = defect_category.replace(" ", "_").lower() if defect_category else "notok"
            save_path = self._notok_path / f"notok_{tag}_{timestamp}.jpg"
            self._stats.not_ok += 1

        cv2.imwrite(str(save_path), frame)
        self._stats.total += 1
        self._db.add_image(str(save_path))

        record = SampleRecord(path=save_path, label=label, timestamp=save_path.stat().st_mtime)
        self._recent.insert(0, record)
        if len(self._recent) > self.MAX_RECENT:
            self._recent.pop()

        return save_path

    def load_existing(self) -> List[SampleRecord]:
        """Scan storage folders and populate stats + recent list."""
        self._stats = DatasetStats()
        all_files: List[Tuple[float, Path, str]] = []

        if self._ok_path.exists():
            for p in self._ok_path.glob("*.jpg"):
                all_files.append((p.stat().st_mtime, p, "OK"))
                self._stats.ok += 1
                self._stats.total += 1

        if self._notok_path.exists():
            for p in self._notok_path.glob("*.jpg"):
                all_files.append((p.stat().st_mtime, p, "NOT_OK"))
                self._stats.not_ok += 1
                self._stats.total += 1

        all_files.sort(key=lambda x: x[0], reverse=True)
        self._recent = [
            SampleRecord(path=p, label=lbl, timestamp=ts)
            for ts, p, lbl in all_files[:self.MAX_RECENT]
        ]
        self._loaded = True
        return self._recent

