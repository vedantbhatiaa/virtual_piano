# ============================================================
#  hand_tracking.py  –  MediaPipe Hands wrapper
#  Compatible with mediapipe 0.10.x on Python 3.11 (no TF)
# ============================================================

import cv2
import mediapipe as mp

# ── Robust import: works across all mediapipe 0.10.x builds ─
try:
    # Standard public API (works when solutions namespace loads)
    _hands_mod  = mp.solutions.hands
    _draw_mod   = mp.solutions.drawing_utils
    _styles_mod = mp.solutions.drawing_styles
except AttributeError:
    # Direct submodule path (fallback for some 0.10.x installs)
    import importlib
    _hands_mod  = importlib.import_module("mediapipe.python.solutions.hands")
    _draw_mod   = importlib.import_module("mediapipe.python.solutions.drawing_utils")
    _styles_mod = importlib.import_module("mediapipe.python.solutions.drawing_styles")


class HandTracker:
    """Wraps MediaPipe Hands; exposes clean fingertip data per frame."""

    FINGERTIP_IDS = [4, 8, 12, 16, 20]
    FINGER_NAMES  = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

    def __init__(self, max_hands: int = 2,
                 detection_conf: float = 0.75,
                 tracking_conf: float = 0.75):

        self.hands = _hands_mod.Hands(
            static_image_mode        = False,
            max_num_hands            = max_hands,
            min_detection_confidence = detection_conf,
            min_tracking_confidence  = tracking_conf,
        )
        self._connections = _hands_mod.HAND_CONNECTIONS

    def process(self, bgr_frame):
        """Convert frame to RGB, run MediaPipe, return results."""
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        return self.hands.process(rgb)

    def get_fingertips(self, results, frame_shape: tuple) -> list:
        """Return list of dicts with x, y, z per visible fingertip."""
        h, w = frame_shape[:2]
        tips = []
        if not results.multi_hand_landmarks:
            return tips
        for hand_idx, hand_lms in enumerate(results.multi_hand_landmarks):
            for finger_idx, tip_id in enumerate(self.FINGERTIP_IDS):
                lm = hand_lms.landmark[tip_id]
                tips.append({
                    "hand_idx"   : hand_idx,
                    "finger_idx" : finger_idx,
                    "landmark_id": tip_id,
                    "x"          : int(lm.x * w),
                    "y"          : int(lm.y * h),
                    "z"          : lm.z,
                })
        return tips

    def draw_hands(self, frame, results) -> None:
        """Draw hand skeleton on frame in-place."""
        if not results.multi_hand_landmarks:
            return
        for hand_lms in results.multi_hand_landmarks:
            _draw_mod.draw_landmarks(
                frame,
                hand_lms,
                self._connections,
                _styles_mod.get_default_hand_landmarks_style(),
                _styles_mod.get_default_hand_connections_style(),
            )

    def draw_fingertips(self, frame, fingertips: list,
                        radius: int = 11,
                        fill_color: tuple = (0, 245, 180),
                        outline_color: tuple = (255, 255, 255)) -> None:
        """Draw circle markers at every fingertip."""
        for tip in fingertips:
            cx, cy = tip["x"], tip["y"]
            cv2.circle(frame, (cx, cy), radius,     fill_color,    -1, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), radius + 3, outline_color,  1, cv2.LINE_AA)

    def close(self) -> None:
        self.hands.close()