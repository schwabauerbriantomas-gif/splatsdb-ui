# SPDX-License-Identifier: GPL-3.0
"""Audio mixin — UI sound effects (EZ-CorridorKey pattern)."""

from pathlib import Path
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl


SOUNDS_DIR = Path(__file__).parent.parent / "resources" / "sounds"

SOUNDS = {
    "click": "click.wav",
    "toggle": "toggle.wav",
    "success": "success.wav",
    "error": "error.wav",
    "search": "search.wav",
    "complete": "complete.wav",
    "notify": "notify.wav",
}


class AudioMixin:
    """UI audio feedback mixin for MainWindow."""

    def init_audio(self):
        """Pre-load sound effects."""
        self._sounds: dict[str, QSoundEffect] = {}
        if not self.state.ui.sounds_enabled:
            return

        for name, filename in SOUNDS.items():
            path = SOUNDS_DIR / filename
            if path.exists():
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(0.3)
                self._sounds[name] = effect

    def play_sound(self, name: str):
        """Play a named sound effect."""
        if self.state.ui.sounds_enabled and name in self._sounds:
            self._sounds[name].play()
