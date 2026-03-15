# ============================================================
#  main.py  –  Virtual Piano using Hand Tracking (entry point)
# ============================================================
#
#  Controls
#  --------
#    Q / ESC   quit
#    +  /  -   increase / decrease piano size
#    R         reset pressed state
#
# ============================================================

import sys
import time
import cv2
import numpy as np

from config import (
    CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, FLIP_HORIZONTAL,
    MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE,
    PRESS_THRESHOLD_Y, DEBOUNCE_TIME,
    FINGERTIP_RADIUS, FINGERTIP_COLOR, FINGERTIP_OUTLINE_COLOR,
    SHOW_FPS, SHOW_HAND_COUNT,
)
from hand_tracking import HandTracker
from piano_ui      import PianoUI
from audio_engine  import AudioEngine


# ── Helper: translucent HUD rectangle ─────────────────────
def draw_hud_box(frame: np.ndarray,
                 x1: int, y1: int, x2: int, y2: int,
                 alpha: float = 0.55) -> None:
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (8, 8, 8), -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


# ── Helper: velocity from downward speed ──────────────────
def speed_to_velocity(dy: float) -> float:
    """Map pixel-per-frame speed -> 0.4 – 1.0 velocity range."""
    return float(np.clip(0.4 + (dy - PRESS_THRESHOLD_Y) / 35.0, 0.4, 1.0))


# ══════════════════════════════════════════════════════════
def main() -> None:

    # ── Camera setup ──────────────────────────────────────
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.  Check CAMERA_INDEX in config.py")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)            # reduce internal buffer lag

    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Camera] Resolution: {fw} × {fh}")

    # ── Module init ───────────────────────────────────────
    tracker = HandTracker(MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE)
    piano   = PianoUI(fw, fh)
    audio   = AudioEngine()

    # ── Per-finger state ──────────────────────────────────
    # Maps (hand_idx, finger_idx) -> last known y-position
    prev_y:        dict[tuple, int]   = {}
    # Maps (hand_idx, finger_idx) -> note name currently held
    inside_key:    dict[tuple, str]   = {}
    # Maps note -> timestamp of last trigger (debounce)
    last_triggered: dict[str, float]  = {}

    # ── FPS state ─────────────────────────────────────────
    fps_frame_count = 0
    fps_timer       = time.time()
    fps_display     = 0

    print("[Piano] Starting – press Q or ESC to quit.\n")

    # ══════════════════════════════════════════════════════
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Frame capture failed.")
            break

        # Mirror for natural / mirror interaction
        if FLIP_HORIZONTAL:
            frame = cv2.flip(frame, 1)

        # ── Hand tracking ─────────────────────────────────
        results   = tracker.process(frame)
        fingertips = tracker.get_fingertips(results, frame.shape)

        # Draw skeleton underneath everything
        tracker.draw_hands(frame, results)

        # ── Key interaction logic ─────────────────────────
        hovering_notes: set[str] = set()
        notes_to_play:  list[tuple[str, float]] = []

        active_fids: set[tuple] = set()

        for tip in fingertips:
            fid = (tip["hand_idx"], tip["finger_idx"])
            x, y = tip["x"], tip["y"]
            active_fids.add(fid)

            note = piano.get_key_at(x, y)

            if note:
                hovering_notes.add(note)

                if fid in prev_y:
                    dy = y - prev_y[fid]            # positive = finger moving DOWN

                    if dy >= PRESS_THRESHOLD_Y:
                        now    = time.time()
                        last_t = last_triggered.get(note, 0.0)
                        prev_note = inside_key.get(fid)

                        # Fire only if debounce cleared AND not already holding this key
                        if (now - last_t) >= DEBOUNCE_TIME and prev_note != note:
                            velocity = speed_to_velocity(dy)
                            notes_to_play.append((note, velocity))
                            last_triggered[note] = now
                            inside_key[fid]      = note
                            piano.set_key_pressed(note, True)

            else:
                # Finger moved off any key
                if fid in inside_key:
                    old_note = inside_key.pop(fid)
                    piano.set_key_pressed(old_note, False)

            prev_y[fid] = y

        # ── Cleanup vanished fingers ──────────────────────
        for fid in list(inside_key.keys()):
            if fid not in active_fids:
                piano.set_key_pressed(inside_key.pop(fid), False)
        for fid in list(prev_y.keys()):
            if fid not in active_fids:
                del prev_y[fid]

        # ── Trigger audio ─────────────────────────────────
        for note, vel in notes_to_play:
            audio.play_note(note, vel)

        # ── Render piano ──────────────────────────────────
        piano.draw(frame, hovering_notes)

        # ── Draw fingertip markers ────────────────────────
        tracker.draw_fingertips(
            frame, fingertips,
            radius        = FINGERTIP_RADIUS,
            fill_color    = FINGERTIP_COLOR,
            outline_color = FINGERTIP_OUTLINE_COLOR,
        )

        # ── FPS counter ───────────────────────────────────
        fps_frame_count += 1
        if time.time() - fps_timer >= 1.0:
            fps_display     = fps_frame_count
            fps_frame_count = 0
            fps_timer       = time.time()

        # ── HUD overlay ───────────────────────────────────
        hand_count = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0

        draw_hud_box(frame, 0, 0, 360, 90)

        cv2.putText(frame, "Virtual Piano  |  Hand Tracking",
                    (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.60,
                    (0, 230, 175), 2, cv2.LINE_AA)

        if SHOW_FPS:
            cv2.putText(frame, f"FPS: {fps_display}",
                        (12, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                        (200, 200, 200), 1, cv2.LINE_AA)

        if SHOW_HAND_COUNT:
            cv2.putText(frame, f"Hands: {hand_count}",
                        (12, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                        (200, 200, 200), 1, cv2.LINE_AA)

        # Active notes label
        if notes_to_play:
            played_str = "  ".join(n for n, _ in notes_to_play)
            cv2.putText(frame, f"  {played_str}",
                        (fw // 2 - 60, int(fh * PIANO_Y_RATIO) - 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.70,
                        (50, 230, 255), 2, cv2.LINE_AA)

        # Quit hint (bottom-right corner)
        cv2.putText(frame, "Q / ESC : quit",
                    (fw - 165, fh - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                    (120, 120, 120), 1, cv2.LINE_AA)

        cv2.imshow("Virtual Piano – Hand Tracking", frame)

        # ── Keyboard shortcuts ────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):     # Q or ESC
            break
        elif key == ord("r"):                    # reset
            inside_key.clear()
            prev_y.clear()
            for note in piano.all_notes:
                piano.set_key_pressed(note, False)

    # ── Cleanup ───────────────────────────────────────────
    cap.release()
    tracker.close()
    audio.close()
    cv2.destroyAllWindows()
    print("[Piano] Closed cleanly.")


# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Import PIANO_Y_RATIO for active-note label positioning
    from config import PIANO_Y_RATIO
    main()
