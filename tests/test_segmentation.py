"""Test suite for RF-DETRSeg Large instance segmentation.

Uses OpenCV to create / load test frames and validates that the full
segmentation pipeline (model load → inference → annotation) works
correctly and within acceptable latency bounds.

Run:
    python -m pytest tests/test_segmentation.py -v
    # or standalone:
    python tests/test_segmentation.py
"""

import os
import sys
import time
import statistics

import cv2
import numpy as np
import pytest

# Ensure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from detector.rfdetr_detector import RFDETRDetector
from detector.annotate import draw_detections

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHECKPOINT_PATH = os.path.join(ROOT_DIR, "models", "checkpoint_best_total.pth")
MODEL_VARIANT = "RF-DETRSeg Large"
NUM_CLASSES = 1
CLASS_NAMES = ["defect"]

# Performance thresholds (seconds) — adjust for your hardware
MAX_COLD_INFERENCE_TIME = 30.0   # first inference can be slow (JIT / warm-up)
MAX_WARM_INFERENCE_TIME = 5.0    # subsequent inferences
WARM_UP_RUNS = 3
BENCHMARK_RUNS = 10


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def detector():
    """Load the RF-DETRSeg Large model once for the entire test module."""
    if not os.path.isfile(CHECKPOINT_PATH):
        pytest.skip(f"Checkpoint not found: {CHECKPOINT_PATH}")

    t0 = time.perf_counter()
    det = RFDETRDetector(
        checkpoint_path=CHECKPOINT_PATH,
        class_names=CLASS_NAMES,
        num_classes=NUM_CLASSES,
        model_variant=MODEL_VARIANT,
    )
    load_time = time.perf_counter() - t0
    print(f"\n[fixture] Model loaded in {load_time:.2f}s  "
          f"(resolution={det.resolution}, device={det.device})")
    return det


@pytest.fixture()
def synthetic_frame():
    """Create a synthetic BGR test frame with known shapes.

    A dark background with bright rectangles that a model *might*
    detect — mainly useful for exercising the full pipeline.
    """
    h, w = 720, 1280
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    # Add some simple shapes as pseudo-defects
    cv2.rectangle(frame, (200, 150), (400, 350), (0, 200, 200), -1)
    cv2.circle(frame, (800, 400), 80, (180, 180, 255), -1)
    cv2.ellipse(frame, (500, 500), (120, 60), 30, 0, 360, (200, 255, 200), -1)
    # Add noise for realism
    noise = np.random.randint(0, 30, (h, w, 3), dtype=np.uint8)
    frame = cv2.add(frame, noise)
    return frame


@pytest.fixture()
def real_frame():
    """Try to capture a single frame from the default USB camera.

    Skips the test if no camera is available.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        pytest.skip("No camera available for real-frame test")
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        pytest.skip("Camera returned empty frame")
    return frame


# ---------------------------------------------------------------------------
# Tests — Model Loading
# ---------------------------------------------------------------------------

class TestModelLoading:
    """Verify model loads correctly and exposes expected attributes."""

    def test_model_loads_successfully(self, detector):
        assert detector is not None

    def test_model_variant(self, detector):
        assert detector.model_variant == MODEL_VARIANT

    def test_model_is_segmentation(self, detector):
        assert MODEL_VARIANT in RFDETRDetector.SEGMENTATION_MODELS

    def test_resolution_is_positive(self, detector):
        assert detector.resolution > 0
        print(f"  Model resolution: {detector.resolution}")

    def test_class_names_assigned(self, detector):
        assert detector.class_names == CLASS_NAMES

    def test_num_classes(self, detector):
        assert detector.num_classes == NUM_CLASSES

    def test_device_is_valid(self, detector):
        assert detector.device in ("cuda", "cpu")
        print(f"  Device: {detector.device}")


# ---------------------------------------------------------------------------
# Tests — Inference Output Format
# ---------------------------------------------------------------------------

class TestInferenceFormat:
    """Validate that predict() returns correctly structured results."""

    def test_returns_list(self, detector, synthetic_frame):
        results = detector.predict(synthetic_frame, confidence_threshold=0.1)
        assert isinstance(results, list)

    def test_detection_dict_keys(self, detector, synthetic_frame):
        results = detector.predict(synthetic_frame, confidence_threshold=0.1)
        required_keys = {"box", "label", "score", "class_id", "mask"}
        for det in results:
            assert required_keys.issubset(det.keys()), (
                f"Missing keys: {required_keys - det.keys()}"
            )

    def test_box_format(self, detector, synthetic_frame):
        results = detector.predict(synthetic_frame, confidence_threshold=0.1)
        for det in results:
            box = det["box"]
            assert isinstance(box, list) and len(box) == 4, (
                f"Box must be [x1,y1,x2,y2], got {box}"
            )
            x1, y1, x2, y2 = box
            assert x2 >= x1 and y2 >= y1, "Box coords must satisfy x2>=x1, y2>=y1"

    def test_score_range(self, detector, synthetic_frame):
        results = detector.predict(synthetic_frame, confidence_threshold=0.1)
        for det in results:
            assert 0.0 <= det["score"] <= 1.0, (
                f"Score out of range: {det['score']}"
            )

    def test_mask_shape_matches_frame(self, detector, synthetic_frame):
        """Segmentation masks must have the same H×W as the input frame."""
        results = detector.predict(synthetic_frame, confidence_threshold=0.1)
        h, w = synthetic_frame.shape[:2]
        for det in results:
            mask = det["mask"]
            if mask is not None:
                assert mask.shape == (h, w), (
                    f"Mask shape {mask.shape} != frame shape ({h}, {w})"
                )

    def test_high_threshold_reduces_detections(self, detector, synthetic_frame):
        low = detector.predict(synthetic_frame, confidence_threshold=0.01)
        high = detector.predict(synthetic_frame, confidence_threshold=0.99)
        assert len(high) <= len(low), (
            "Higher threshold should yield fewer or equal detections"
        )

    def test_empty_on_blank_frame(self, detector):
        """A solid black frame should (likely) produce no detections."""
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        results = detector.predict(blank, confidence_threshold=0.5)
        # Not a hard failure if model hallucinates, but flag it
        if len(results) > 0:
            print(f"  ⚠ Model produced {len(results)} detection(s) on blank frame")
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# Tests — Annotation Rendering
# ---------------------------------------------------------------------------

class TestAnnotation:
    """Verify that draw_detections works with segmentation output."""

    def test_annotate_with_masks(self, detector, synthetic_frame):
        results = detector.predict(synthetic_frame, confidence_threshold=0.1)
        annotated = draw_detections(
            synthetic_frame, results, draw_masks=True, mask_alpha=0.4,
        )
        assert annotated.shape == synthetic_frame.shape
        assert annotated.dtype == synthetic_frame.dtype

    def test_annotate_without_masks(self, detector, synthetic_frame):
        results = detector.predict(synthetic_frame, confidence_threshold=0.1)
        annotated = draw_detections(
            synthetic_frame, results, draw_masks=False,
        )
        assert annotated.shape == synthetic_frame.shape

    def test_annotate_empty_detections(self, synthetic_frame):
        annotated = draw_detections(synthetic_frame, [], draw_masks=True)
        # Should return a copy unchanged
        np.testing.assert_array_equal(annotated, synthetic_frame)

    def test_annotated_frame_differs_when_detections_exist(
        self, detector, synthetic_frame
    ):
        results = detector.predict(synthetic_frame, confidence_threshold=0.1)
        if not results:
            pytest.skip("No detections to annotate")
        annotated = draw_detections(
            synthetic_frame, results, draw_masks=True,
        )
        assert not np.array_equal(annotated, synthetic_frame), (
            "Annotated frame should differ from original when detections exist"
        )


# ---------------------------------------------------------------------------
# Tests — Performance / Speed
# ---------------------------------------------------------------------------

class TestPerformance:
    """Benchmark inference speed and ensure it stays within budget."""

    def test_cold_inference_time(self, detector, synthetic_frame):
        """First inference may include JIT compilation; allow more time."""
        t0 = time.perf_counter()
        detector.predict(synthetic_frame, confidence_threshold=0.5)
        elapsed = time.perf_counter() - t0
        print(f"  Cold inference: {elapsed:.3f}s")
        assert elapsed < MAX_COLD_INFERENCE_TIME, (
            f"Cold inference took {elapsed:.2f}s > {MAX_COLD_INFERENCE_TIME}s limit"
        )

    def test_warm_inference_time(self, detector, synthetic_frame):
        """After warm-up, each inference should be faster."""
        # Warm up
        for _ in range(WARM_UP_RUNS):
            detector.predict(synthetic_frame, confidence_threshold=0.5)

        times = []
        for _ in range(BENCHMARK_RUNS):
            t0 = time.perf_counter()
            detector.predict(synthetic_frame, confidence_threshold=0.5)
            times.append(time.perf_counter() - t0)

        avg = statistics.mean(times)
        med = statistics.median(times)
        mn = min(times)
        mx = max(times)
        std = statistics.stdev(times) if len(times) > 1 else 0.0

        print(
            f"  Warm inference ({BENCHMARK_RUNS} runs):\n"
            f"    avg={avg:.3f}s  median={med:.3f}s  "
            f"min={mn:.3f}s  max={mx:.3f}s  std={std:.3f}s\n"
            f"    ~{1/avg:.1f} FPS"
        )
        assert avg < MAX_WARM_INFERENCE_TIME, (
            f"Avg warm inference {avg:.2f}s exceeds {MAX_WARM_INFERENCE_TIME}s limit"
        )

    def test_inference_with_varying_resolutions(self, detector):
        """Inference should handle different frame sizes gracefully."""
        resolutions = [(640, 480), (1280, 720), (1920, 1080)]
        for w, h in resolutions:
            frame = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
            t0 = time.perf_counter()
            results = detector.predict(frame, confidence_threshold=0.5)
            elapsed = time.perf_counter() - t0
            print(f"  {w}x{h}: {elapsed:.3f}s  ({len(results)} dets)")
            assert isinstance(results, list)

    def test_end_to_end_pipeline_speed(self, detector, synthetic_frame):
        """Full pipeline: inference + annotation must complete in time."""
        # Warm up
        for _ in range(WARM_UP_RUNS):
            r = detector.predict(synthetic_frame, confidence_threshold=0.5)
            draw_detections(synthetic_frame, r, draw_masks=True)

        times = []
        for _ in range(BENCHMARK_RUNS):
            t0 = time.perf_counter()
            results = detector.predict(synthetic_frame, confidence_threshold=0.5)
            draw_detections(synthetic_frame, results, draw_masks=True)
            times.append(time.perf_counter() - t0)

        avg = statistics.mean(times)
        print(
            f"  End-to-end pipeline ({BENCHMARK_RUNS} runs): "
            f"avg={avg:.3f}s  ~{1/avg:.1f} FPS"
        )
        # Allow slightly more time for annotation overhead
        assert avg < MAX_WARM_INFERENCE_TIME + 1.0


# ---------------------------------------------------------------------------
# Tests — Real Camera (optional)
# ---------------------------------------------------------------------------

class TestRealCamera:
    """Run inference on a real camera frame (skipped if no camera)."""

    def test_inference_on_real_frame(self, detector, real_frame):
        results = detector.predict(real_frame, confidence_threshold=0.3)
        print(f"  Real frame: {len(results)} detection(s)")
        assert isinstance(results, list)
        for det in results:
            assert "box" in det and "mask" in det

    def test_annotate_real_frame(self, detector, real_frame):
        results = detector.predict(real_frame, confidence_threshold=0.3)
        annotated = draw_detections(real_frame, results, draw_masks=True)
        assert annotated.shape == real_frame.shape
        # Optionally save for visual inspection
        out_path = os.path.join(ROOT_DIR, "tests", "output_real_annotated.png")
        cv2.imwrite(out_path, annotated)
        print(f"  Saved annotated frame → {out_path}")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("RF-DETRSeg Large — Instance Segmentation Test")
    print("=" * 70)

    if not os.path.isfile(CHECKPOINT_PATH):
        print(f"ERROR: Checkpoint not found: {CHECKPOINT_PATH}")
        sys.exit(1)

    # --- Load model ---
    print(f"\n[1/5] Loading model: {MODEL_VARIANT}")
    t0 = time.perf_counter()
    det = RFDETRDetector(
        checkpoint_path=CHECKPOINT_PATH,
        class_names=CLASS_NAMES,
        num_classes=NUM_CLASSES,
        model_variant=MODEL_VARIANT,
    )
    load_time = time.perf_counter() - t0
    print(f"      Loaded in {load_time:.2f}s  |  resolution={det.resolution}  "
          f"|  device={det.device}")

    # --- Create test frame ---
    print("\n[2/5] Creating synthetic test frame (1280×720)")
    h, w = 720, 1280
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.rectangle(frame, (200, 150), (400, 350), (0, 200, 200), -1)
    cv2.circle(frame, (800, 400), 80, (180, 180, 255), -1)
    noise = np.random.randint(0, 30, (h, w, 3), dtype=np.uint8)
    frame = cv2.add(frame, noise)

    # --- Cold inference ---
    print("\n[3/5] Running cold inference …")
    t0 = time.perf_counter()
    results = det.predict(frame, confidence_threshold=0.1)
    cold_time = time.perf_counter() - t0
    print(f"      {len(results)} detection(s) in {cold_time:.3f}s")
    for r in results:
        mask_info = f"mask={r['mask'].shape}" if r["mask"] is not None else "no mask"
        print(f"        {r['label']} score={r['score']:.2%}  box={r['box']}  {mask_info}")

    # --- Warm benchmark ---
    print(f"\n[4/5] Warm benchmark ({WARM_UP_RUNS} warm-up + {BENCHMARK_RUNS} timed) …")
    for _ in range(WARM_UP_RUNS):
        det.predict(frame, confidence_threshold=0.5)

    times = []
    for i in range(BENCHMARK_RUNS):
        t0 = time.perf_counter()
        det.predict(frame, confidence_threshold=0.5)
        t = time.perf_counter() - t0
        times.append(t)
        print(f"      Run {i+1:2d}: {t:.3f}s")

    avg = statistics.mean(times)
    med = statistics.median(times)
    print(f"      ────────────────────────")
    print(f"      avg={avg:.3f}s  median={med:.3f}s  "
          f"min={min(times):.3f}s  max={max(times):.3f}s")
    print(f"      ~{1/avg:.1f} FPS")

    # --- Annotation test ---
    print("\n[5/5] Drawing annotated output …")
    results = det.predict(frame, confidence_threshold=0.1)
    annotated = draw_detections(frame, results, draw_masks=True, mask_alpha=0.4)

    os.makedirs(os.path.join(ROOT_DIR, "tests"), exist_ok=True)
    out_path = os.path.join(ROOT_DIR, "tests", "output_segmentation_test.png")
    cv2.imwrite(out_path, annotated)
    print(f"      Saved → {out_path}")

    # --- Camera test (optional) ---
    print("\n[bonus] Attempting camera capture …")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, cam_frame = cap.read()
        cap.release()
        if ret and cam_frame is not None:
            t0 = time.perf_counter()
            cam_results = det.predict(cam_frame, confidence_threshold=0.3)
            t = time.perf_counter() - t0
            annotated_cam = draw_detections(
                cam_frame, cam_results, draw_masks=True, mask_alpha=0.4
            )
            cam_out = os.path.join(ROOT_DIR, "tests", "output_camera_test.png")
            cv2.imwrite(cam_out, annotated_cam)
            print(f"      Camera: {len(cam_results)} det(s) in {t:.3f}s → {cam_out}")
        else:
            print("      Camera returned empty frame — skipped")
    else:
        cap.release()
        print("      No camera available — skipped")

    print("\n" + "=" * 70)
    print("ALL DONE ✓")
    print("=" * 70)

