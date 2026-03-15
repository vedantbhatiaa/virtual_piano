# 🎹 Virtual Piano – Real-Time Hand Tracking

A touchless, augmented-reality piano that uses your laptop webcam and **MediaPipe** hand tracking to detect all 10 fingers and play piano notes when a fingertip presses a virtual key on screen.

---

## ✨ Features

| Feature | Detail |
|---|---|
| Hand detection | MediaPipe Hands – both hands, all 21 landmarks, 10 fingertips |
| Press detection | Downward-motion trigger (not hover), debounced |
| Velocity sensitivity | Faster presses = louder note |
| Polyphonic playback | Up to 32 simultaneous notes / chords |
| Visual FX | Glow on press, hover tint, bevel, skeleton overlay |
| Piano sound | Additive synthesis (6 harmonics + ADSR + exp decay) |
| Performance | Targets ≥ 25 FPS on a mid-range laptop |

---

## 📁 File Structure

```
virtual_piano/
│
├── main.py              # Entry point – camera loop, press logic, HUD
├── hand_tracking.py     # MediaPipe Hands wrapper (detect + draw)
├── piano_ui.py          # Piano key layout, rendering, hit-detection
├── audio_engine.py      # pygame mixer – load & play WAV files
├── config.py            # All tunable constants (camera, layout, audio…)
│
├── generate_sounds.py   # ONE-TIME script to synthesise all 12 WAVs
│
├── requirements.txt
├── README.md
│
└── sounds/              # Auto-created by generate_sounds.py
    ├── C.wav
    ├── Cs.wav            # C#
    ├── D.wav
    ├── Ds.wav            # D#
    ├── E.wav
    ├── F.wav
    ├── Fs.wav            # F#
    ├── G.wav
    ├── Gs.wav            # G#
    ├── A.wav
    ├── As.wav            # A#
    └── B.wav
```

> **Why `Cs` instead of `C#`?**  
> The `#` character is unsafe in many filesystems and shells, so sharp notes are stored as `Cs`, `Ds`, etc.  The `AudioEngine` maps note names to filenames transparently.

---

## 🚀 Quick Start

### 1 – Install dependencies
```bash
pip install -r requirements.txt
```

### 2 – Generate sounds (run once)
```bash
python generate_sounds.py
```

### 3 – Launch the piano
```bash
python main.py
```

Your webcam opens immediately with the virtual keyboard at the bottom of the frame.

---

## 🎮 Controls

| Key | Action |
|---|---|
| `Q` / `ESC` | Quit |
| `R` | Reset all pressed-key state |

---

## 🎯 How Press Detection Works

```
Frame N-1:  fingertip at  y = 420
Frame N:    fingertip at  y = 435     ← delta_y = +15 (≥ threshold)

→  "downward motion into key" → note fires
→  debounce timer starts (0.28 s)
→  finger must leave & re-enter key before it can fire again
```

This prevents:
- Sustained hover falsely repeating notes
- Jitter-induced double-triggers
- Note spam when hand trembles

---

## ⚙️ Tuning via `config.py`

```python
PRESS_THRESHOLD_Y   = 12    # pixels of downward movement to trigger
DEBOUNCE_TIME       = 0.28  # seconds between repeated triggers (same key)
PIANO_WIDTH_RATIO   = 0.88  # piano width as fraction of screen width
PIANO_Y_RATIO       = 0.70  # vertical position (0 = top, 1 = bottom)
MASTER_VOLUME       = 0.82  # 0.0 – 1.0
MAX_HANDS           = 2     # 1 or 2
```

---

## 🔭 Extending the Project

| Idea | Where to start |
|---|---|
| Multi-octave keyboard | `piano_ui.py` – increase `NUM_WHITE_KEYS`, add octave offset |
| MIDI export | `main.py` – log `(note, timestamp, velocity)` tuples → `mido` library |
| Note recording / playback | `main.py` – buffer pressed notes, replay with `time.sleep` |
| Octave switching by hand height | `main.py` – detect wrist y-pos, shift frequencies in `audio_engine.py` |
| Sustain pedal (fist gesture) | `hand_tracking.py` – check finger curl landmarks |
| Use real piano samples | Replace `sounds/*.wav` with any 44100 Hz stereo WAVs |

---

## 📦 Libraries Used

- **opencv-python** – webcam capture, frame rendering
- **mediapipe** – real-time hand landmark detection
- **pygame** – low-latency audio mixer
- **numpy** – signal synthesis, fast array ops

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| Blank/black screen | Check `CAMERA_INDEX` in `config.py` (try 1 or 2) |
| No sound | Run `generate_sounds.py` first; check `sounds/` directory |
| High latency | Lower `MIXER_BUFFER` (e.g. 128) in `config.py` |
| Poor detection | Improve lighting; ensure hands are clearly visible |
| Low FPS | Reduce `FRAME_WIDTH` / `FRAME_HEIGHT` in `config.py` |
