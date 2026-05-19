# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Audio for the game.

Three short background tracks. If a matching audio file exists in
assets/music (e.g. Calm.ogg / Calm.wav) it is loaded; otherwise a
simple looping tune is generated procedurally in code, so the game
always has sound with no external asset dependency.
"""

import os
import struct
import wave
import io

import pygame

# Where real music files would live, if the user adds them later.
MUSIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "music",
)

SAMPLE_RATE = 22050

# Each track is a list of (note_frequency_hz, beats). 0 frequency = rest.
# Kept short; they loop seamlessly.
_A, _C, _D, _E, _G = 220.0, 261.6, 293.7, 329.6, 392.0
_TRACKS = {
    "Calm":    [(_C, 2), (_E, 2), (_G, 2), (_E, 2), (_D, 2), (_C, 4), (0, 2)],
    "Upbeat":  [(_G, 1), (_G, 1), (_E, 1), (_G, 1), (_A, 1), (_G, 1),
                (_E, 1), (_D, 1), (_C, 2), (_E, 2)],
    "Mystery": [(_A, 3), (0, 1), (_C, 2), (_D, 3), (0, 1), (_A, 4), (0, 2)],
}


def _build_wave_bytes(track, beat_seconds=0.32):
    """Render a note list into 16-bit mono WAV bytes (a soft sine tune)."""
    frames = bytearray()
    for freq, beats in track:
        n = int(SAMPLE_RATE * beat_seconds * beats)
        for i in range(n):
            if freq <= 0:
                sample = 0
            else:
                # Sine tone with a gentle fade in/out to avoid clicks.
                import math
                t = i / SAMPLE_RATE
                env = min(1.0, i / 400, (n - i) / 400)
                sample = int(9000 * env * math.sin(2 * math.pi * freq * t))
            frames += struct.pack("<h", sample)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(frames))
    buffer.seek(0)
    return buffer


class AudioManager:
    """Loads/generates tracks and controls playback."""

    def __init__(self):
        self._sounds = {}
        self._channel = None
        self._current = None
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE)
            self._ok = True
        except pygame.error:
            # Some environments have no audio device; fail silently.
            self._ok = False

    def _get_sound(self, name):
        """Return a Sound for `name`, building or loading it once."""
        if name in self._sounds:
            return self._sounds[name]

        sound = None
        # Prefer a real file the user may have dropped in.
        for ext in (".ogg", ".wav", ".mp3"):
            path = os.path.join(MUSIC_DIR, name + ext)
            if os.path.exists(path):
                try:
                    sound = pygame.mixer.Sound(path)
                except pygame.error:
                    sound = None
                break
        # Otherwise generate a procedural tune.
        if sound is None and name in _TRACKS:
            sound = pygame.mixer.Sound(_build_wave_bytes(_TRACKS[name]))

        self._sounds[name] = sound
        return sound

    def play(self, name):
        """Start looping track `name`, stopping anything already playing."""
        if not self._ok:
            return
        self.stop()
        sound = self._get_sound(name)
        if sound is not None:
            sound.set_volume(0.4)
            self._channel = sound.play(loops=-1)
            self._current = name

    def stop(self):
        if self._ok and self._channel is not None:
            self._channel.stop()
        self._channel = None
        self._current = None
