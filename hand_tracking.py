# ============================================================
#  hand_tracking.py  –  MediaPipe Hands (Tasks API)
#  For mediapipe 0.10.x which uses Tasks API only (no solutions)
# ============================================================

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks           import python      as mp_python
from mediapipe.tasks.python    import vision      as mp_vision

MODEL_PATH = "hand_landmarker.task"

# Hand connections for drawing skeleton (landmark index pairs)
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),          # thumb
    (0,5),(5,6),(6,7),(7,8),          # index
    (0,9),(9,10),(10,11),(11,12),     # middle
    (0,13),(13,14),(14,15),(15,16),   # ring
    (0,17),(17,18),(18,19),(19,20),   # pinky
    (5,9),(9,13),(13,17),             # palm
]

FINGERTIP_IDS  = [4, 8, 12, 16, 20]
FINGER_NAMES   = ["Thumb", "Index", "Middle", "Ring", "Pinky"]


class HandTracker:
    def __init__(self, max_hands: int = 2,
                 detection_conf: float = 0.75,
                 tracking_conf: float = 0.75):

        if not __import__("os").path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}\n"
                "Run:  python download_model.py  first."
            )

        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.HandLandmarkerOptions(
            base_options                   = base_options,
            running_mode                   = mp_vision.RunningMode.VIDEO,
            num_hands                      = max_hands,
            min_hand_detection_confidence  = detection_conf,
            min_hand_presence_confidence   = detection_conf,
            min_tracking_confidence        = tracking_conf,
        )
        self.detector  = mp_vision.HandLandmarker.create_from_options(options)
        self._frame_ts = 0

    def process(self, bgr_frame):
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._frame_ts += 33
        return self.detector.detect_for_video(mp_image, self._frame_ts)

    def get_fingertips(self, results, frame_shape: tuple) -> list:
        h, w = frame_shape[:2]
        tips = []
        if not results.hand_landmarks:
            return tips
        for hand_idx, hand_lms in enumerate(results.hand_landmarks):
            for finger_idx, tip_id in enumerate(FINGERTIP_IDS):
                lm = hand_lms[tip_id]
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
        if not results.hand_landmarks:
            return
        h, w = frame.shape[:2]
        for hand_lms in results.hand_landmarks:
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lms]
            for a, b in HAND_CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], (80, 200, 120), 2, cv2.LINE_AA)
            for pt in pts:
                cv2.circle(frame, pt, 4, (255, 255, 255), -1, cv2.LINE_AA)

    def draw_fingertips(self, frame, fingertips: list,
                        radius: int = 11,
                        fill_color: tuple = (0, 245, 180),
                        outline_color: tuple = (255, 255, 255)) -> None:
        for tip in fingertips:
            cx, cy = tip["x"], tip["y"]
            cv2.circle(frame, (cx, cy), radius,     fill_color,    -1, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), radius + 3, outline_color,  1, cv2.LINE_AA)

    def close(self) -> None:
        self.detector.close()