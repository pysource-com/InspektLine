"""Dataset collection service.

Captures frames from the live camera feed as either a video file or
a series of images.  No Qt dependency — pure Python + OpenCV.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from services.settings_service import SettingsService


class DatasetService:
    """Manages dataset collection (video recording or image capture).

    Usage::

        svc = DatasetService(settings)
        svc.start_collection()
        for frame in frames:
            svc.process_frame(frame)
        svc.stop_collection()
    """

    def __init__(self, settings: SettingsService):
        self._settings = settings

        # Collection state
        self._is_collecting = False
        self._mode: str = "images"  # "video" | "images"
        self._session_dir: Optional[Path] = None

        # Video recording
        self._video_writer: Optional[cv2.VideoWriter] = None

        # Image capture
        self._frame_counter: int = 0
        self._frames_saved: int = 0
        self._frame_skip: int = 5

    # ---- properties --------------------------------------------------------

    @property
    def is_collecting(self) -> bool:
        return self._is_collecting

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def frames_saved(self) -> int:
        return self._frames_saved

    @property
    def session_dir(self) -> Optional[Path]:
        return self._session_dir

    # ---- lifecycle ---------------------------------------------------------

    def start_collection(self, output_dir: Optional[str] = None,
                         mode: Optional[str] = None,
                         frame_skip: Optional[int] = None) -> bool:
        """Start a new collection session.

        Creates a timestamped subfolder inside *output_dir* (or the
        configured dataset directory).  Returns True on success.
        """
        if self._is_collecting:
            return False

        ds = self._settings.dataset
        self._mode = mode or ds.collection_mode
        self._frame_skip = frame_skip if frame_skip is not None else ds.frame_skip
        base_dir = Path(output_dir or ds.dataset_dir)

        # Create timestamped session folder
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        prefix = "video" if self._mode == "video" else "images"
        self._session_dir = base_dir / f"{prefix}_{timestamp}"

        try:
            self._session_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"[DatasetService] Cannot create session directory: {exc}")
            return False

        self._frame_counter = 0
        self._frames_saved = 0
        self._is_collecting = True

        print(f"[DatasetService] Collection started — mode={self._mode}, "
              f"dir={self._session_dir}")
        return True

    def stop_collection(self) -> None:
        """Stop the current collection session and release resources."""
        if not self._is_collecting:
            return

        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None

        print(f"[DatasetService] Collection stopped — "
              f"{self._frames_saved} frames saved to {self._session_dir}")

        self._is_collecting = False

    # ---- frame processing --------------------------------------------------

    def process_frame(self, frame: np.ndarray) -> None:
        """Process a single frame according to the current collection mode.

        Must be called for every displayed frame; the service decides
        internally whether to save it (based on mode and frame_skip).
        """
        if not self._is_collecting or frame is None:
            return

        if self._mode == "video":
            self._write_video_frame(frame)
        else:
            self._write_image_frame(frame)

        self._frame_counter += 1

    # ---- internals ---------------------------------------------------------

    def _write_video_frame(self, frame: np.ndarray) -> None:
        """Append *frame* to the video file, lazily creating the writer."""
        if self._video_writer is None:
            h, w = frame.shape[:2]
            video_path = str(self._session_dir / "recording.mp4")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            fps = 30.0
            self._video_writer = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
            if not self._video_writer.isOpened():
                print(f"[DatasetService] Failed to open VideoWriter at {video_path}")
                self._video_writer = None
                return

        self._video_writer.write(frame)
        self._frames_saved += 1

    def _write_image_frame(self, frame: np.ndarray) -> None:
        """Save *frame* as a PNG if the skip interval has elapsed."""
        if self._frame_counter % self._frame_skip != 0:
            return

        self._frames_saved += 1
        filename = f"{self._frames_saved:05d}.png"
        filepath = str(self._session_dir / filename)

        try:
            cv2.imwrite(filepath, frame)
        except Exception as exc:
            print(f"[DatasetService] Failed to write {filepath}: {exc}")

