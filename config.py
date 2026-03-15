# ============================================================
#  config.py  –  Central configuration for Virtual Piano
# ============================================================

# ── Camera ──────────────────────────────────────────────────
CAMERA_INDEX       = 0
FRAME_WIDTH        = 1280
FRAME_HEIGHT       = 720
FLIP_HORIZONTAL    = True          # mirror-mode for natural interaction

# ── Hand Tracking ───────────────────────────────────────────
MAX_HANDS              = 2
DETECTION_CONFIDENCE   = 0.75
TRACKING_CONFIDENCE    = 0.75

# ── Piano Layout (fractions of screen) ──────────────────────
PIANO_WIDTH_RATIO  = 0.88          # width relative to frame
PIANO_HEIGHT_RATIO = 0.24          # height relative to frame
PIANO_Y_RATIO      = 0.70          # top-edge y relative to frame

NUM_WHITE_KEYS     = 7             # C D E F G A B  (one octave)

# ── Visual ──────────────────────────────────────────────────
FINGERTIP_RADIUS        = 11
WHITE_KEY_COLOR         = (245, 245, 245)
BLACK_KEY_COLOR         = (28,  28,  28)
KEY_HOVER_WHITE_COLOR   = (190, 225, 255)
KEY_HOVER_BLACK_COLOR   = (80,  140, 200)
KEY_PRESSED_COLOR       = (80,  210, 255)
KEY_OUTLINE_COLOR       = (70,  70,  70)
FINGERTIP_COLOR         = (0,   245, 180)
FINGERTIP_OUTLINE_COLOR = (255, 255, 255)

# ── Press Detection ─────────────────────────────────────────
PRESS_THRESHOLD_Y  = 12            # min downward pixels in one frame to trigger
DEBOUNCE_TIME      = 0.28          # seconds before same note can fire again

# ── Audio ───────────────────────────────────────────────────
SOUND_DIR          = "sounds"
MASTER_VOLUME      = 0.82
MIXER_CHANNELS     = 32            # simultaneous note polyphony
MIXER_BUFFER       = 256           # lower = less latency

# ── UI Text ─────────────────────────────────────────────────
SHOW_FPS           = True
SHOW_HAND_COUNT    = True
