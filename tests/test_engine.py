"""Engine tests for Sharpshooter."""

from sharpshooter.engine import (
    BLUE_STEP_TICKS,
    BOARD_HEIGHT,
    GameEngine,
    GamePhase,
    RED_STEP_TICKS,
    STARTING_LIVES,
    create_level_state,
)


def test_level_one_initial_layout() -> None:
    """Level 1 starts with two blue rows and all edge oranges."""
    level = create_level_state(1)

    assert level.level_id == 1
    assert len(level.edge_oranges) == 32
    assert level.red_rows == []
    assert level.blue_rows[0].cols == {0, 2, 4, 6, 8, 10, 12, 14}
    assert level.blue_rows[1].cols == {1, 3, 5, 7, 9, 11, 13, 15}
    assert level.blue_rows[0].direction.value == 1
    assert level.blue_rows[1].direction.value == -1


def test_blue_rows_wrap_in_opposite_directions() -> None:
    """Blue rows move one step after the required number of ticks."""
    engine = GameEngine()
    state = engine.new_game()

    engine.advance_ticks(state, BLUE_STEP_TICKS)

    assert state.level.blue_rows[0].cols == {1, 3, 5, 7, 9, 11, 13, 15}
    assert state.level.blue_rows[1].cols == {0, 2, 4, 6, 8, 10, 12, 14}


def test_red_rows_move_on_level_two() -> None:
    """Red rows move according to the level-two speed."""
    engine = GameEngine()
    state = engine.new_game()
    state.level = create_level_state(2)

    engine.advance_ticks(state, RED_STEP_TICKS)

    assert state.level.red_rows[0].cols == {3, 4, 5, 6, 11, 12, 13, 14}
    assert state.level.red_rows[1].cols == {1, 2, 3, 4, 9, 10, 11, 12}


def test_firing_top_orange_creates_projectile() -> None:
    """Clicking an edge orange launches a projectile inward."""
    engine = GameEngine()
    state = engine.new_game()

    engine.fire(state, row=0, col=3)

    assert (0, 3) not in state.level.edge_oranges
    assert [
        (projectile.origin_row, projectile.row, projectile.col)
        for projectile in state.level.projectiles
    ] == [(0, 1, 3)]


def test_orange_removes_blue() -> None:
    """A projectile removes a blue tile on collision."""
    engine = GameEngine()
    state = engine.new_game()

    engine.fire(state, row=0, col=3)
    engine.advance_ticks(state, 12)

    assert 3 not in state.level.blue_rows[0].cols
    assert state.level.projectiles == []


def test_orange_hitting_red_costs_life_and_removes_red() -> None:
    """Orange-red collisions decrement lives and clear the red tile."""
    engine = GameEngine()
    state = engine.new_game()
    state.level = create_level_state(2)

    engine.fire(state, row=0, col=4)
    engine.advance_ticks(state, 4)

    assert state.lives == STARTING_LIVES - 1
    assert 4 not in state.level.red_rows[0].cols
    assert state.level.projectiles == []


def test_level_advances_when_all_blue_removed() -> None:
    """Clearing level one transitions to level two."""
    engine = GameEngine()
    state = engine.new_game()
    state.level.blue_rows[0].cols.clear()
    state.level.blue_rows[1].cols.clear()

    engine.advance_ticks(state, 1)

    assert state.phase is GamePhase.PLAYING
    assert state.level.level_id == 2


def test_timeout_causes_game_over() -> None:
    """The level timer ends the run immediately when it expires."""
    engine = GameEngine()
    state = engine.new_game()
    ticks_to_timeout = int(45 * 32)

    engine.advance_ticks(state, ticks_to_timeout)

    assert state.phase is GamePhase.GAME_OVER


def test_last_life_ends_run() -> None:
    """Dropping to zero lives ends the game."""
    engine = GameEngine()
    state = engine.new_game()
    state.level = create_level_state(2)
    state.lives = 1

    engine.fire(state, row=0, col=4)
    engine.advance_ticks(state, 4)

    assert state.phase is GamePhase.GAME_OVER
    assert state.lives == 0


def test_clearing_level_two_wins_game() -> None:
    """Clearing the second level ends in victory."""
    engine = GameEngine()
    state = engine.new_game()
    state.level = create_level_state(2)
    state.level.blue_rows[0].cols.clear()
    state.level.blue_rows[1].cols.clear()

    engine.advance_ticks(state, 1)

    assert state.phase is GamePhase.VICTORY
    assert state.level.level_id == 2


def test_bottom_orange_moves_upward() -> None:
    """Bottom-edge oranges fire upward through the board."""
    engine = GameEngine()
    state = engine.new_game()

    engine.fire(state, row=BOARD_HEIGHT - 1, col=5)
    engine.advance_ticks(state, 2)

    assert [(projectile.row, projectile.col) for projectile in state.level.projectiles] == [(24, 5)]


def test_snapshot_renders_full_active_orange_path() -> None:
    """The board shows the visible trail of an active orange shot."""
    engine = GameEngine()
    state = engine.new_game()

    engine.fire(state, row=0, col=6)
    engine.advance_ticks(state, 2)
    snapshot = engine.snapshot(state)

    assert snapshot.board[1][6].tile.value == "O"
    assert snapshot.board[2][6].tile.value == "O"
    assert snapshot.board[3][6].tile.value == "O"
