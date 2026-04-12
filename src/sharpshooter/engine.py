"""Game engine for the Sharpshooter board simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

BOARD_WIDTH = 16
BOARD_HEIGHT = 28
TICKS_PER_SECOND = 32
SECONDS_PER_BLUE_STEP = 6 / BOARD_WIDTH
SECONDS_PER_RED_STEP = 4 / BOARD_WIDTH
BLUE_STEP_TICKS = int(SECONDS_PER_BLUE_STEP * TICKS_PER_SECOND)
RED_STEP_TICKS = int(SECONDS_PER_RED_STEP * TICKS_PER_SECOND)
SECONDS_PER_LEVEL = 45.0
STARTING_LIVES = 5


class TileType(str, Enum):
    """Visible tile types on the board."""

    BLANK = "_"
    ORANGE = "O"
    BLUE = "B"
    RED = "R"


class Direction(int, Enum):
    """Movement direction for row-based actors."""

    LEFT = -1
    RIGHT = 1


class GamePhase(str, Enum):
    """High-level game phases."""

    PLAYING = "playing"
    GAME_OVER = "game_over"
    VICTORY = "victory"


@dataclass(slots=True, frozen=True)
class EdgeOrange:
    """An orange tile resting on the top or bottom edge."""

    row: int
    col: int
    direction: int


@dataclass(slots=True)
class Projectile:
    """A fired orange moving inward through the board."""

    origin_row: int
    row: int
    col: int
    direction: int


@dataclass(slots=True)
class MovingRow:
    """A row of autonomous actors that wrap across the board."""

    row: int
    cols: set[int]
    direction: Direction

    def step(self) -> None:
        """Advance the row by one wrapped column."""
        self.cols = {(col + self.direction.value) % BOARD_WIDTH for col in self.cols}


@dataclass(slots=True, frozen=True)
class LevelConfig:
    """Static configuration for a level."""

    level_id: int
    red_rows: tuple[MovingRow, ...]


@dataclass(slots=True)
class LevelState:
    """Mutable board state for one active level."""

    level_id: int
    blue_rows: list[MovingRow]
    red_rows: list[MovingRow]
    edge_oranges: dict[tuple[int, int], EdgeOrange]
    projectiles: list[Projectile] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    tick_counter: int = 0


@dataclass(slots=True, frozen=True)
class CellView:
    """Renderable state for one board cell."""

    row: int
    col: int
    tile: TileType
    clickable: bool = False


@dataclass(slots=True, frozen=True)
class GameSnapshot:
    """Renderable snapshot of the full game state."""

    board: tuple[tuple[CellView, ...], ...]
    level: int
    lives: int
    time_remaining: float
    phase: GamePhase
    status_text: str


def _copy_row(row: MovingRow) -> MovingRow:
    """Create a mutable copy of a moving row config."""
    return MovingRow(row=row.row, cols=set(row.cols), direction=row.direction)


LEVELS: dict[int, LevelConfig] = {
    1: LevelConfig(
        level_id=1,
        red_rows=(),
    ),
    2: LevelConfig(
        level_id=2,
        red_rows=(
            MovingRow(row=5, cols={4, 5, 6, 7, 12, 13, 14, 15}, direction=Direction.LEFT),
            MovingRow(row=22, cols={0, 1, 2, 3, 8, 9, 10, 11}, direction=Direction.RIGHT),
        ),
    ),
}


def _build_blue_rows() -> list[MovingRow]:
    """Create the two moving blue rows shared by both levels."""
    return [
        MovingRow(row=13, cols={0, 2, 4, 6, 8, 10, 12, 14}, direction=Direction.RIGHT),
        MovingRow(row=14, cols={1, 3, 5, 7, 9, 11, 13, 15}, direction=Direction.LEFT),
    ]


def _build_edge_oranges() -> dict[tuple[int, int], EdgeOrange]:
    """Create the full set of clickable top and bottom oranges."""
    oranges: dict[tuple[int, int], EdgeOrange] = {}
    for col in range(BOARD_WIDTH):
        oranges[(0, col)] = EdgeOrange(row=0, col=col, direction=1)
        oranges[(BOARD_HEIGHT - 1, col)] = EdgeOrange(
            row=BOARD_HEIGHT - 1, col=col, direction=-1
        )
    return oranges


def create_level_state(level_id: int) -> LevelState:
    """Create a fresh mutable state for the requested level."""
    config = LEVELS[level_id]
    return LevelState(
        level_id=level_id,
        blue_rows=_build_blue_rows(),
        red_rows=[_copy_row(row) for row in config.red_rows],
        edge_oranges=_build_edge_oranges(),
    )


@dataclass(slots=True)
class GameState:
    """Full mutable game state spanning both levels."""

    level: LevelState = field(default_factory=lambda: create_level_state(1))
    lives: int = STARTING_LIVES
    phase: GamePhase = GamePhase.PLAYING


class GameEngine:
    """Deterministic simulation engine for the Sharpshooter game."""

    def new_game(self) -> GameState:
        """Create a fresh game."""
        return GameState()

    def fire(self, state: GameState, row: int, col: int) -> None:
        """Fire an orange tile from the requested edge position."""
        if state.phase is not GamePhase.PLAYING:
            return

        orange = state.level.edge_oranges.pop((row, col), None)
        if orange is None:
            return

        next_row = row + orange.direction
        if 0 <= next_row < BOARD_HEIGHT:
            state.level.projectiles.append(
                Projectile(origin_row=row, row=next_row, col=col, direction=orange.direction)
            )

    def advance_ticks(self, state: GameState, ticks: int) -> None:
        """Advance the simulation by a fixed number of ticks."""
        for _ in range(ticks):
            if state.phase is not GamePhase.PLAYING:
                break
            self._advance_one_tick(state)

    def snapshot(self, state: GameState, elapsed_seconds: float | None = None) -> GameSnapshot:
        """Build a renderable snapshot for the web layer."""
        board = self._render_board(state.level)
        rendered_elapsed = state.level.elapsed_seconds if elapsed_seconds is None else elapsed_seconds
        time_remaining = max(0.0, SECONDS_PER_LEVEL - rendered_elapsed)
        if state.phase is GamePhase.GAME_OVER:
            if rendered_elapsed >= SECONDS_PER_LEVEL:
                status_text = "Time expired. Game over."
            else:
                status_text = "You lost all lives. Game over."
        elif state.phase is GamePhase.VICTORY:
            status_text = "All levels cleared."
        else:
            status_text = f"Level {state.level.level_id} in progress."
        return GameSnapshot(
            board=board,
            level=state.level.level_id,
            lives=state.lives,
            time_remaining=time_remaining,
            phase=state.phase,
            status_text=status_text,
        )

    def _advance_one_tick(self, state: GameState) -> None:
        """Advance the simulation by one engine tick."""
        level = state.level
        level.tick_counter += 1
        level.elapsed_seconds += 1 / TICKS_PER_SECOND
        if level.elapsed_seconds >= SECONDS_PER_LEVEL:
            state.phase = GamePhase.GAME_OVER
            return

        if level.tick_counter % BLUE_STEP_TICKS == 0:
            for blue_row in level.blue_rows:
                blue_row.step()

        if level.red_rows and level.tick_counter % RED_STEP_TICKS == 0:
            for red_row in level.red_rows:
                red_row.step()

        self._advance_projectiles(level)
        self._resolve_projectile_collisions(state)
        self._update_phase_after_collisions(state)

    def _advance_projectiles(self, level: LevelState) -> None:
        """Move all active projectiles inward by one row."""
        survivors: list[Projectile] = []
        for projectile in level.projectiles:
            if 0 <= projectile.row < BOARD_HEIGHT:
                survivors.append(projectile)

        level.projectiles = survivors
        for projectile in level.projectiles:
            projectile.row += projectile.direction

    def _resolve_projectile_collisions(self, state: GameState) -> None:
        """Resolve collisions after movement."""
        level = state.level
        blue_cells = {
            (row.row, col): row
            for row in level.blue_rows
            for col in row.cols
        }
        red_cells = {
            (row.row, col): row
            for row in level.red_rows
            for col in row.cols
        }
        survivors: list[Projectile] = []
        lives_lost = 0

        for projectile in level.projectiles:
            if not (0 <= projectile.row < BOARD_HEIGHT):
                continue

            position = (projectile.row, projectile.col)
            blue_row = blue_cells.get(position)
            if blue_row is not None:
                blue_row.cols.discard(projectile.col)
                continue

            red_row = red_cells.get(position)
            if red_row is not None:
                red_row.cols.discard(projectile.col)
                lives_lost += 1
                continue

            survivors.append(projectile)

        level.projectiles = survivors
        if lives_lost:
            state.lives = max(0, state.lives - lives_lost)

    def _update_phase_after_collisions(self, state: GameState) -> None:
        """Advance levels or end the run when win/lose conditions are met."""
        if state.lives <= 0:
            state.phase = GamePhase.GAME_OVER
            return

        remaining_blue = sum(len(row.cols) for row in state.level.blue_rows)
        if remaining_blue > 0:
            return

        if state.level.level_id == 1:
            state.level = create_level_state(2)
            return

        state.phase = GamePhase.VICTORY

    def _render_board(self, level: LevelState) -> tuple[tuple[CellView, ...], ...]:
        """Render runtime state into a board matrix for templates."""
        blue_cells = {(row.row, col) for row in level.blue_rows for col in row.cols}
        red_cells = {(row.row, col) for row in level.red_rows for col in row.cols}
        projectile_cells = {
            (path_row, projectile.col)
            for projectile in level.projectiles
            for path_row in self._projectile_path_rows(projectile)
        }

        board: list[tuple[CellView, ...]] = []
        for row in range(BOARD_HEIGHT):
            rendered_row: list[CellView] = []
            for col in range(BOARD_WIDTH):
                position = (row, col)
                if position in projectile_cells or position in level.edge_oranges:
                    rendered_row.append(
                        CellView(
                            row=row,
                            col=col,
                            tile=TileType.ORANGE,
                            clickable=position in level.edge_oranges,
                        )
                    )
                elif position in blue_cells:
                    rendered_row.append(CellView(row=row, col=col, tile=TileType.BLUE))
                elif position in red_cells:
                    rendered_row.append(CellView(row=row, col=col, tile=TileType.RED))
                else:
                    rendered_row.append(CellView(row=row, col=col, tile=TileType.BLANK))
            board.append(tuple(rendered_row))
        return tuple(board)

    def _projectile_path_rows(self, projectile: Projectile) -> range:
        """Return the visible path for a projectile from launch edge to current row."""
        start_row = projectile.origin_row + projectile.direction
        end_row = projectile.row
        step = projectile.direction
        return range(start_row, end_row + step, step)


def iter_live_blue_cells(level: LevelState) -> Iterable[tuple[int, int]]:
    """Yield all currently occupied blue cells."""
    for row in level.blue_rows:
        for col in row.cols:
            yield (row.row, col)
