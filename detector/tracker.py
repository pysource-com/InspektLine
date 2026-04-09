"""Object tracking (ByteTrack) and polygon-ROI zone counting.

Wraps ``supervision.ByteTrack`` for persistent object IDs and
``supervision.PolygonZone`` for counting objects inside a user-drawn
polygon region of interest.

No Qt dependency — pure Python + numpy + supervision.
"""

from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import supervision as sv


class ObjectTracker:
    """Lightweight ByteTrack wrapper that operates on plain detection dicts.

    Parameters
    ----------
    track_activation_threshold : float
        Minimum confidence for a detection to initialise a new track.
    lost_track_buffer : int
        Number of frames a lost track is kept before deletion.
    minimum_matching_threshold : float
        IoU threshold for matching detections to existing tracks.
    frame_rate : int
        Expected frame rate (used internally by ByteTrack).
    """

    def __init__(
        self,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        minimum_matching_threshold: float = 0.8,
        frame_rate: int = 30,
    ):
        self._tracker = sv.ByteTrack(
            track_activation_threshold=track_activation_threshold,
            lost_track_buffer=lost_track_buffer,
            minimum_matching_threshold=minimum_matching_threshold,
            frame_rate=frame_rate,
        )

        # Polygon ROI zone (set by the user)
        self._polygon: Optional[np.ndarray] = None
        self._zone: Optional[sv.PolygonZone] = None
        self._zone_count: int = 0  # objects currently inside the zone

        # Cumulative counter: total unique tracker IDs that have been
        # observed inside the zone at least once.
        self._seen_ids: set = set()
        self._total_entered: int = 0

    # ---- polygon ROI -------------------------------------------------------

    def set_polygon(self, points: List[Tuple[int, int]]) -> None:
        """Define the ROI polygon.

        Parameters
        ----------
        points : list of (x, y) tuples
            Vertices in *frame* (pixel) coordinates.  At least 3 points.
        """
        if len(points) < 3:
            self.clear_polygon()
            return
        self._polygon = np.array(points, dtype=np.int32)
        self._zone = sv.PolygonZone(
            polygon=self._polygon,
        )
        self._seen_ids.clear()
        self._total_entered = 0
        self._zone_count = 0

    def clear_polygon(self) -> None:
        """Remove the ROI polygon."""
        self._polygon = None
        self._zone = None
        self._zone_count = 0
        self._seen_ids.clear()
        self._total_entered = 0

    @property
    def has_polygon(self) -> bool:
        return self._polygon is not None

    @property
    def polygon(self) -> Optional[np.ndarray]:
        """Return the current polygon vertices (N×2 int array) or None."""
        return self._polygon

    @property
    def zone_count(self) -> int:
        """Number of tracked objects currently inside the polygon."""
        return self._zone_count

    @property
    def total_entered(self) -> int:
        """Total unique objects that have entered the polygon."""
        return self._total_entered

    # ---- tracking ----------------------------------------------------------

    def reset(self) -> None:
        """Reset tracker state and all counters."""
        self._tracker.reset()
        self._seen_ids.clear()
        self._total_entered = 0
        self._zone_count = 0

    def update(
        self, detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Track detections and update zone counts.

        Parameters
        ----------
        detections : list[dict]
            Each dict must have ``box`` ([x1,y1,x2,y2]), ``score`` (float),
            ``class_id`` (int).  Optionally ``mask``, ``label``.

        Returns
        -------
        list[dict]
            Same dicts enriched with ``tracker_id`` (int) and
            ``in_zone`` (bool).  Order may differ from input.
        """
        if not detections:
            self._zone_count = 0
            return []

        # Build a supervision.Detections object
        boxes = np.array([d["box"] for d in detections], dtype=np.float32)
        scores = np.array([d["score"] for d in detections], dtype=np.float32)
        class_ids = np.array([d["class_id"] for d in detections], dtype=int)

        masks = None
        if detections[0].get("mask") is not None:
            masks = np.stack([d["mask"] for d in detections])

        sv_det = sv.Detections(
            xyxy=boxes,
            confidence=scores,
            class_id=class_ids,
            mask=masks,
        )

        # Run ByteTrack
        sv_det = self._tracker.update_with_detections(sv_det)

        # Zone trigger
        in_zone_mask = None
        if self._zone is not None:
            in_zone_mask = self._zone.trigger(detections=sv_det)
            self._zone_count = int(in_zone_mask.sum()) if in_zone_mask is not None else 0

        # Rebuild detection dicts with tracker IDs
        tracked: List[Dict[str, Any]] = []
        for i in range(len(sv_det)):
            tid = int(sv_det.tracker_id[i]) if sv_det.tracker_id is not None else -1
            cid = int(sv_det.class_id[i])
            label_src = [d for d in detections if d["class_id"] == cid]
            label = label_src[0]["label"] if label_src else f"class_{cid}"

            in_zone = bool(in_zone_mask[i]) if in_zone_mask is not None else False

            # Track unique IDs entering the zone
            if in_zone and tid >= 0 and tid not in self._seen_ids:
                self._seen_ids.add(tid)
                self._total_entered = len(self._seen_ids)

            det: Dict[str, Any] = {
                "box": sv_det.xyxy[i].tolist(),
                "label": label,
                "score": float(sv_det.confidence[i]),
                "class_id": cid,
                "mask": sv_det.mask[i] if sv_det.mask is not None else None,
                "tracker_id": tid,
                "in_zone": in_zone,
            }
            tracked.append(det)

        return tracked

