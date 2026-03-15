# ============================================================
#  audio_engine.py  –  pygame-based polyphonic sound engine
# ============================================================

import os
import pygame
from config import SOUND_DIR, MASTER_VOLUME, MIXER_CHANNELS, MIXER_BUFFER


# Map from note name  ->  filename stem (# replaced by s for filesystem safety)
_NOTE_FILE_MAP: dict[str, str] = {
    "C" : "C",
    "C#": "Cs",
    "D" : "D",
    "D#": "Ds",
    "E" : "E",
    "F" : "F",
    "F#": "Fs",
    "G" : "G",
    "G#": "Gs",
    "A" : "A",
    "A#": "As",
    "B" : "B",
}


class AudioEngine:
    """
    Loads piano WAV files and plays them on demand with velocity sensitivity.
    Supports full polyphony (up to MIXER_CHANNELS simultaneous notes).
    """

    def __init__(self):
        # Low-latency mixer initialisation
        pygame.mixer.pre_init(
            frequency=44100,
            size=-16,               # signed 16-bit PCM
            channels=2,             # stereo
            buffer=MIXER_BUFFER,
        )
        pygame.mixer.init()
        pygame.mixer.set_num_channels(MIXER_CHANNELS)

        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self._load_sounds()

    # ── Sound loading ──────────────────────────────────────
    def _load_sounds(self) -> None:
        """Load every WAV file from SOUND_DIR into memory."""
        loaded = 0
        for note, stem in _NOTE_FILE_MAP.items():
            path = os.path.join(SOUND_DIR, f"{stem}.wav")
            if os.path.isfile(path):
                snd = pygame.mixer.Sound(path)
                snd.set_volume(MASTER_VOLUME)
                self.sounds[note] = snd
                loaded += 1
            else:
                print(f"[AudioEngine] WARNING – missing: {path}")

        if loaded == 0:
            print("[AudioEngine] No sounds loaded!  "
                  "Run  generate_sounds.py  first.")
        else:
            print(f"[AudioEngine] {loaded}/12 sounds loaded.")

    # ── Playback ──────────────────────────────────────────
    def play_note(self, note: str, velocity: float = 1.0) -> None:
        """
        Trigger note immediately.
        velocity: 0.0 – 1.0  (scales final volume).
        Each call gets its own mixer channel so chords work correctly.
        """
        snd = self.sounds.get(note)
        if snd is None:
            return
        vol = max(0.0, min(1.0, MASTER_VOLUME * velocity))
        snd.set_volume(vol)
        # play() finds a free channel automatically
        snd.play()

    # ── Cleanup ───────────────────────────────────────────
    def stop_all(self) -> None:
        pygame.mixer.stop()

    def close(self) -> None:
        pygame.mixer.quit()
