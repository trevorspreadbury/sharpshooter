"""Stateful service wrapper around the game engine."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from sharpshooter.engine import (
    GameEngine,
    GameSnapshot,
    GameState,
    SECONDS_PER_LEVEL,
    TICKS_PER_SECOND,
)

SPEED_OPTIONS: tuple[float, ...] = (1.0, 0.5, 0.25, 0.125)


@dataclass(slots=True)
class GameService:
    """Own the single local game session used by the web app."""

    engine: GameEngine = field(default_factory=GameEngine)
    state: GameState = field(init=False)
    speed_multiplier: float = field(default=1.0, init=False)
    _last_tick_time: float = field(init=False)
    _remainder: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """Initialize service state."""
        self.restart()

    def restart(self) -> None:
        """Reset the local game."""
        self.state = self.engine.new_game()
        self.speed_multiplier = 1.0
        self._last_tick_time = time.monotonic()
        self._remainder = 0.0

    def sync(self) -> GameSnapshot:
        """Advance the simulation to the current wall-clock time and return a snapshot."""
        now = time.monotonic()
        elapsed = ((now - self._last_tick_time) * self.speed_multiplier) + self._remainder
        ticks = int(elapsed * TICKS_PER_SECOND)
        self._remainder = elapsed - (ticks / TICKS_PER_SECOND)
        self._last_tick_time = now
        if ticks > 0:
            self.engine.advance_ticks(self.state, ticks)
        return self.engine.snapshot(self.state, elapsed_seconds=self._display_elapsed_seconds())

    def fire(self, row: int, col: int) -> GameSnapshot:
        """Fire one orange after syncing runtime state."""
        self.sync()
        self.engine.fire(self.state, row=row, col=col)
        return self.engine.snapshot(self.state, elapsed_seconds=self._display_elapsed_seconds())

    def set_speed(self, speed_multiplier: float) -> GameSnapshot:
        """Update simulation speed and return the latest snapshot."""
        self.sync()
        if speed_multiplier in SPEED_OPTIONS:
            self.speed_multiplier = speed_multiplier
        self._last_tick_time = time.monotonic()
        return self.engine.snapshot(self.state, elapsed_seconds=self._display_elapsed_seconds())

    def _display_elapsed_seconds(self) -> float:
        """Return elapsed level time including fractional progress between ticks."""
        return min(self.state.level.elapsed_seconds + self._remainder, SECONDS_PER_LEVEL)
