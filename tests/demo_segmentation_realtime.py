"""Real-time RF-DETRSeg instance segmentation demo with OpenCV.

Opens a Daheng industrial camera (gxipy) and runs the RF-DETRSeg Large
model on every frame, displaying annotated results with masks in a live
OpenCV window.

Usage:
    python tests/demo_segmentation_realtime.py

Controls:
    Q / ESC   — Quit
    M         — Toggle mask overlay on/off
    +/-       — Increase/decrease confidence threshold by 5%
    S         — Save current annotated frame as PNG
    SPACE     — Pause/resume
"""

import os
import sys
import time
from collections import deque

import cv2

# Ensure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from detector.rfdetr_detector import RFDETRDetector
from detector.annotate import draw_detections
from camera.daheng import DahengCamera

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CHECKPOINT_PATH = os.path.join(ROOT_DIR, "models", "checkpoint_best_total.pth")
MODEL_VARIANT = "RF-DETRSeg Large"
NUM_CLASSES = 1
CLASS_NAMES = ["defect"]
DAHENG_DEVICE_INDEX = 1          # gxipy uses 1-based device index
INITIAL_THRESHOLD = 0.5
WINDOW_NAME = "InspektLine — Segmentation Demo"


def draw_hud(frame, fps, threshold, n_dets, masks_on, paused):
    """Draw a translucent heads-up display bar at the top of the frame."""
    h, w = frame.shape[:2]
    bar_h = 36
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, bar_h), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    status = "PAUSED" if paused else "LIVE"
    mask_txt = "MASKS ON" if masks_on else "MASKS OFF"
    text = (
        f"FPS: {fps:5.1f}  |  Threshold: {threshold:.0%}  |  "
        f"Detections: {n_dets}  |  {mask_txt}  |  {status}"
    )
    cv2.putText(
        frame, text, (10, 24),
        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 200), 1, cv2.LINE_AA,
    )

    # Controls hint at the bottom
    hint = "Q:Quit  M:Masks  +/-:Threshold  S:Save  SPACE:Pause"
    cv2.putText(
        frame, hint, (10, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 160), 1, cv2.LINE_AA,
    )


def main():
    # ------------------------------------------------------------------
    # Load model
    # ------------------------------------------------------------------
    print(f"Loading model: {MODEL_VARIANT}")
    print(f"  Checkpoint : {CHECKPOINT_PATH}")
    if not os.path.isfile(CHECKPOINT_PATH):
        print(f"ERROR: Checkpoint not found: {CHECKPOINT_PATH}")
        sys.exit(1)

    t0 = time.perf_counter()
    detector = RFDETRDetector(
        checkpoint_path=CHECKPOINT_PATH,
        class_names=CLASS_NAMES,
        num_classes=NUM_CLASSES,
        model_variant=MODEL_VARIANT,
    )
    print(f"  Loaded in {time.perf_counter() - t0:.2f}s  "
          f"(resolution={detector.resolution}, device={detector.device})")

    # ------------------------------------------------------------------
    # Open Daheng industrial camera (gxipy)
    # ------------------------------------------------------------------
    print(f"Opening Daheng camera (device index {DAHENG_DEVICE_INDEX}) ...")
    cam = DahengCamera(device_index=DAHENG_DEVICE_INDEX)
    if not cam.start():
        print("ERROR: Cannot open Daheng camera. Check connection and Galaxy SDK.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    threshold = INITIAL_THRESHOLD
    masks_on = True
    paused = False
    fps_history = deque(maxlen=60)
    frame_count = 0
    save_counter = 0

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 720)

    print("\n--- Demo started. Press Q or ESC to quit. ---\n")

    last_frame = None
    last_results = []

    while True:
        if not paused:
            frame = cam.get_bgr_frame()
            if frame is None:
                # Daheng can occasionally return None; just retry
                time.sleep(0.01)
                continue

            # Run inference
            t0 = time.perf_counter()
            results = detector.predict(frame, confidence_threshold=threshold)
            inf_time = time.perf_counter() - t0
            fps_history.append(1.0 / inf_time if inf_time > 0 else 0)

            last_frame = frame
            last_results = results
            frame_count += 1
        else:
            # While paused, re-use the last frame
            if last_frame is None:
                last_frame = cam.get_bgr_frame()
                if last_frame is None:
                    time.sleep(0.01)
                    continue
                last_results = detector.predict(
                    last_frame, confidence_threshold=threshold
                )

        # Annotate
        annotated = draw_detections(
            last_frame, last_results,
            draw_masks=masks_on, mask_alpha=0.45,
        )

        # HUD overlay
        avg_fps = sum(fps_history) / len(fps_history) if fps_history else 0
        draw_hud(annotated, avg_fps, threshold, len(last_results), masks_on, paused)

        cv2.imshow(WINDOW_NAME, annotated)

        # ------------------------------------------------------------------
        # Key handling (waitKey returns -1 if no key pressed)
        # ------------------------------------------------------------------
        key = cv2.waitKey(1) & 0xFF

        if key in (ord("q"), ord("Q"), 27):  # Q or ESC
            break

        elif key in (ord("m"), ord("M")):
            masks_on = not masks_on
            print(f"  Masks {'ON' if masks_on else 'OFF'}")

        elif key in (ord("+"), ord("="), 43):
            threshold = min(threshold + 0.05, 1.0)
            print(f"  Threshold → {threshold:.0%}")

        elif key in (ord("-"), ord("_"), 45):
            threshold = max(threshold - 0.05, 0.0)
            print(f"  Threshold → {threshold:.0%}")

        elif key == ord(" "):
            paused = not paused
            print(f"  {'PAUSED' if paused else 'RESUMED'}")

        elif key in (ord("s"), ord("S")):
            save_counter += 1
            out_dir = os.path.join(ROOT_DIR, "tests")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"demo_capture_{save_counter:03d}.png")
            cv2.imwrite(out_path, annotated)
            print(f"  Saved → {out_path}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    cam.stop()
    cv2.destroyAllWindows()

    if fps_history:
        avg = sum(fps_history) / len(fps_history)
        print(f"\nSession: {frame_count} frames processed, avg {avg:.1f} FPS")
    print("Done.")


if __name__ == "__main__":
    main()

