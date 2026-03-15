# ============================================================
#  generate_sounds.py  –  Synthesise piano-like WAV files
# ============================================================
#
#  Run ONCE before starting main.py:
#      python generate_sounds.py
#
#  Generates all 12 chromatic notes into the  sounds/  folder
#  using additive synthesis + an ADSR-with-exponential-decay
#  envelope that approximates a real piano timbre.
# ============================================================

import os
import wave
import struct
import numpy as np


# ── Note frequencies (equal temperament, A4 = 440 Hz) ─────
NOTE_FREQUENCIES: dict[str, float] = {
    "C" : 261.63,
    "Cs": 277.18,   # C#
    "D" : 293.66,
    "Ds": 311.13,   # D#
    "E" : 329.63,
    "F" : 349.23,
    "Fs": 369.99,   # F#
    "G" : 392.00,
    "Gs": 415.30,   # G#
    "A" : 440.00,
    "As": 466.16,   # A#
    "B" : 493.88,
}

SAMPLE_RATE = 44100
DURATION    = 2.5   # seconds per note
CHANNELS    = 2     # stereo


# ── Synthesis ─────────────────────────────────────────────
def piano_tone(freq: float,
               duration: float = DURATION,
               sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Additive synthesis of a piano-like tone:
      • 6 harmonics with decreasing amplitudes
      • Slight inharmonicity (piano strings are stiff)
      • ADSR envelope  +  exponential decay

    Returns a float64 array normalised to ±1.
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Inharmonicity factor B (stretches upper partials slightly)
    B = 0.0001

    signal = np.zeros_like(t)
    harmonic_amps = [1.00, 0.50, 0.28, 0.14, 0.07, 0.035]

    for n, amp in enumerate(harmonic_amps, start=1):
        # Inharmonic partial frequency
        f_n = freq * n * np.sqrt(1 + B * n * n)
        # Slight random phase for realism
        phase = np.random.uniform(0, 0.15)
        signal += amp * np.sin(2 * np.pi * f_n * t + phase)

    # ── ADSR envelope ──────────────────────────────────────
    n_samples = len(t)
    attack_s  = int(0.008 * sr)         # 8 ms  attack
    decay_s   = int(0.12  * sr)         # 120 ms decay
    sustain_l = 0.55                    # sustain level
    release_s = int(0.55  * sr)         # 550 ms release

    envelope = np.ones(n_samples) * sustain_l

    # Attack
    if attack_s > 0:
        envelope[:attack_s] = np.linspace(0, 1, attack_s)

    # Decay
    d_end = attack_s + decay_s
    if d_end <= n_samples:
        envelope[attack_s:d_end] = np.linspace(1, sustain_l, decay_s)

    # Release (from end)
    r_start = max(n_samples - release_s, 0)
    envelope[r_start:] = np.linspace(sustain_l, 0, n_samples - r_start)

    # Global exponential decay (piano notes naturally fade)
    exp_decay = np.exp(-2.8 * t / duration)
    envelope  = np.minimum(envelope, np.ones_like(envelope))  # cap at 1
    envelope *= exp_decay

    signal *= envelope

    # Normalise to 90% of max amplitude
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal /= peak
    signal *= 0.90

    return signal


# ── WAV writer ────────────────────────────────────────────
def save_wav(filepath: str,
             signal: np.ndarray,
             sr: int = SAMPLE_RATE) -> None:
    """Write a mono float signal as 16-bit stereo WAV."""
    pcm = (signal * 32767).astype(np.int16)

    with wave.open(filepath, "w") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)          # 16-bit = 2 bytes
        wf.setframerate(sr)
        # Interleave L + R (identical for our mono source)
        stereo = np.column_stack([pcm, pcm])
        wf.writeframes(stereo.tobytes())


# ── Main ──────────────────────────────────────────────────
def main() -> None:
    out_dir = "sounds"
    os.makedirs(out_dir, exist_ok=True)

    print(f"Generating {len(NOTE_FREQUENCIES)} piano notes → {out_dir}/\n")

    for stem, freq in NOTE_FREQUENCIES.items():
        path = os.path.join(out_dir, f"{stem}.wav")
        print(f"  {stem:3s}  {freq:7.2f} Hz  →  {path}")
        tone = piano_tone(freq)
        save_wav(path, tone)

    print(f"\n✓  Done.  All WAV files are in  {out_dir}/")
    print("   You can now run:  python main.py\n")


if __name__ == "__main__":
    main()
