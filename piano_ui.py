# ============================================================
#  piano_ui.py  –  Virtual piano rendering & hit-detection
# ============================================================

import cv2
import numpy as np
from config import *


# One octave: white and black note names in order
WHITE_NOTES = ["C", "D", "E", "F", "G", "A", "B"]
BLACK_NOTES = ["C#", "D#", "F#", "G#", "A#"]

# Maps each black note to the index of its LEFT neighbouring white key
#   C# sits between C(0) and D(1), so left-white = 0
_BLACK_LEFT_IDX = {
    "C#": 0,
    "D#": 1,
    "F#": 3,
    "G#": 4,
    "A#": 5,
}

# Ordered list: white keys first, then black (for z-order handling)
ALL_NOTES_ORDERED = WHITE_NOTES + BLACK_NOTES


class PianoUI:
    """
    Draws a one-octave piano across the lower portion of the frame
    and detects which key (if any) a pixel coordinate is inside.
    """

    def __init__(self, frame_width: int, frame_height: int):
        self.fw = frame_width
        self.fh = frame_height

        # Active state
        self.pressed_keys: set[str]   = set()    # keys currently held down
        self.glow_keys:    dict[str, float] = {}  # note -> glow intensity 0-1

        self._build_key_rects()

    # ── Layout calculation ─────────────────────────────────
    def _build_key_rects(self) -> None:
        """
        Compute (x1, y1, x2, y2) pixel rects for every key.
        Black keys are narrower and only cover the top 62% of the white key height.
        """
        piano_w  = int(self.fw * PIANO_WIDTH_RATIO)
        piano_h  = int(self.fh * PIANO_HEIGHT_RATIO)
        piano_x  = (self.fw - piano_w) // 2
        piano_y  = int(self.fh * PIANO_Y_RATIO)

        self.piano_rect = (piano_x, piano_y, piano_w, piano_h)

        n_white   = len(WHITE_NOTES)
        wk_w      = piano_w  // n_white
        wk_h      = piano_h
        bk_w      = int(wk_w * 0.58)
        bk_h      = int(wk_h * 0.62)

        self.wk_w, self.wk_h = wk_w, wk_h
        self.bk_w, self.bk_h = bk_w, bk_h

        self.key_rects: dict[str, tuple[int,int,int,int]] = {}

        # White keys
        for i, note in enumerate(WHITE_NOTES):
            x1 = piano_x + i * wk_w
            y1 = piano_y
            x2 = x1 + wk_w - 2          # 2-px gap between keys
            y2 = y1 + wk_h
            self.key_rects[note] = (x1, y1, x2, y2)

        # Black keys (positioned between adjacent white keys)
        for note, left_idx in _BLACK_LEFT_IDX.items():
            left_x = piano_x + left_idx * wk_w
            # centre the black key over the boundary
            x1 = left_x + wk_w - bk_w // 2
            y1 = piano_y
            x2 = x1 + bk_w
            y2 = y1 + bk_h
            self.key_rects[note] = (x1, y1, x2, y2)

    # ── Hit detection ──────────────────────────────────────
    def get_key_at(self, x: int, y: int) -> str | None:
        """
        Return the note name whose rectangle contains (x, y),
        or None.  Black keys take priority over white ones.
        """
        # Black keys first (they sit on top visually)
        for note in BLACK_NOTES:
            x1, y1, x2, y2 = self.key_rects[note]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return note
        # White keys
        for note in WHITE_NOTES:
            x1, y1, x2, y2 = self.key_rects[note]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return note
        return None

    def is_over_piano(self, x: int, y: int) -> bool:
        """True when (x,y) is inside or slightly above the piano region (hover zone)."""
        px, py, pw, ph = self.piano_rect
        return (px <= x <= px + pw) and (py - 70 <= y <= py + ph)

    # ── State management ──────────────────────────────────
    def set_key_pressed(self, note: str, pressed: bool = True) -> None:
        if pressed:
            self.pressed_keys.add(note)
            self.glow_keys[note] = 1.0      # reset glow to full on press
        else:
            self.pressed_keys.discard(note)

    def _decay_glow(self) -> None:
        """Gradually reduce glow each frame for a smooth fade-out."""
        for note in list(self.glow_keys):
            self.glow_keys[note] *= 0.82
            if self.glow_keys[note] < 0.04:
                del self.glow_keys[note]

    # ── Rendering ──────────────────────────────────────────
    def draw(self, frame: np.ndarray,
             hovering_notes: set[str] | None = None) -> None:
        """
        Render the full piano onto `frame` (in-place).
        hovering_notes: set of notes a fingertip is currently above.
        """
        if hovering_notes is None:
            hovering_notes = set()

        self._decay_glow()

        # ── Background shadow strip ──
        px, py, pw, ph = self.piano_rect
        shadow = frame.copy()
        cv2.rectangle(shadow, (px - 4, py - 4), (px + pw + 4, py + ph + 8),
                      (15, 15, 15), -1)
        cv2.addWeighted(shadow, 0.55, frame, 0.45, 0, frame)

        # Draw white keys first (lower z-order)
        for note in WHITE_NOTES:
            self._draw_key(frame, note, is_black=False, hovering_notes=hovering_notes)

        # Draw black keys on top
        for note in BLACK_NOTES:
            self._draw_key(frame, note, is_black=True, hovering_notes=hovering_notes)

        # Note labels on white keys
        for note in WHITE_NOTES:
            x1, y1, x2, y2 = self.key_rects[note]
            cx = (x1 + x2) // 2
            cy = y2 - 18
            label_color = (50, 50, 50)
            if note in self.pressed_keys or note in self.glow_keys:
                label_color = (0, 0, 0)
            cv2.putText(frame, note, (cx - 8, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                        label_color, 1, cv2.LINE_AA)

    def _draw_key(self, frame: np.ndarray, note: str,
                  is_black: bool, hovering_notes: set[str]) -> None:
        """Draw one key with correct colour, hover tint and glow."""
        x1, y1, x2, y2 = self.key_rects[note]

        pressed  = note in self.pressed_keys
        hovering = note in hovering_notes
        glow     = self.glow_keys.get(note, 0.0)

        # Base colours (BGR)
        if is_black:
            base = np.array([28,  28,  28],  dtype=float)
            glow_tgt = np.array([255, 160, 40], dtype=float)
            hover_c  = np.array([200, 140, 80], dtype=float)
        else:
            base = np.array([245, 245, 245], dtype=float)
            glow_tgt = np.array([255, 210, 60], dtype=float)
            hover_c  = np.array([255, 225, 190], dtype=float)

        # Mix colour
        factor = max(float(pressed), glow)
        if factor > 0.05:
            color = (base * (1 - factor) + glow_tgt * factor).clip(0, 255)
        elif hovering:
            color = hover_c
        else:
            color = base

        color_t = tuple(int(c) for c in color)

        # ── Fill ──
        cv2.rectangle(frame, (x1, y1), (x2, y2), color_t, -1)

        # ── Glow halo (drawn before outline so outline stays sharp) ──
        if glow > 0.15 or pressed:
            halo_intensity = max(glow, float(pressed))
            halo_color = tuple(int(c * halo_intensity) for c in (255, 200, 80))
            thickness = max(1, int(halo_intensity * 5))
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2),
                          halo_color, thickness)
            cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

        # ── Outline ──
        outline = (50, 50, 50) if is_black else (90, 90, 90)
        cv2.rectangle(frame, (x1, y1), (x2, y2), outline, 1)

        # ── 3-D bevel on white keys ──
        if not is_black:
            cv2.line(frame, (x1, y1), (x1, y2), (255, 255, 255), 1)  # left highlight
            cv2.line(frame, (x1, y2), (x2, y2), (160, 160, 160), 1)  # bottom shadow

    # ── Public info ───────────────────────────────────────
    @property
    def all_notes(self) -> list[str]:
        return ALL_NOTES_ORDERED
