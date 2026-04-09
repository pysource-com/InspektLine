"""Bounding-box crop utility for extracting object regions from frames.

Pure function — no Qt or model dependency.
"""

from typing import List

import numpy as np


def extract_object_crop(
    frame: np.ndarray,
    box: List[float],
    padding: int = 0,
) -> np.ndarray:
    """Extract a rectangular crop from the frame using the bounding box.

    Parameters
    ----------
    frame : np.ndarray
        BGR image (H, W, 3).
    box : list[float]
        Bounding box as ``[x1, y1, x2, y2]`` in pixel coordinates.
    padding : int
        Optional pixel padding around the box (clamped to frame bounds).

    Returns
    -------
    np.ndarray
        Cropped BGR image region.  Always at least 1×1.
    """
    h, w = frame.shape[:2]

    x1 = max(0, int(box[0]) - padding)
    y1 = max(0, int(box[1]) - padding)
    x2 = min(w, int(box[2]) + padding)
    y2 = min(h, int(box[3]) + padding)

    # Ensure at least 1×1 crop
    if x2 <= x1:
        x2 = x1 + 1
    if y2 <= y1:
        y2 = y1 + 1

    return frame[y1:y2, x1:x2].copy()

