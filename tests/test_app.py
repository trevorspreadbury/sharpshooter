"""HTTP tests for the Sharpshooter app."""

from fastapi.testclient import TestClient

from sharpshooter.main import create_app
from sharpshooter.service import GameService


def test_index_renders_game() -> None:
    """The root page renders the game shell."""
    client = TestClient(create_app(service=GameService()))

    response = client.get("/")

    assert response.status_code == 200
    assert "Sharpshooter" in response.text
    assert "Ready to start level 1." in response.text
    assert 'data-post-url="/start"' in response.text
    assert 'data-async-post="/speed"' in response.text
    assert 'data-post-url="/restart"' in response.text
    assert 'data-async-post="/level"' in response.text


def test_fire_endpoint_updates_board() -> None:
    """Firing removes the clicked orange from the edge."""
    service = GameService()
    client = TestClient(create_app(service=service))
    service.start()
    service.countdown_remaining = None

    response = client.post("/fire/0/0")

    assert response.status_code == 200
    assert 'data-fire-url="/fire/0/0"' not in response.text
    assert service.state.level.projectiles


def test_restart_resets_state() -> None:
    """Restart creates a fresh level-one game."""
    service = GameService()
    client = TestClient(create_app(service=service))
    client.post("/fire/0/1")

    response = client.post("/restart")

    assert response.status_code == 200
    assert service.state.level.level_id == 1
    assert service.selected_level == 1
    assert len(service.state.level.edge_oranges) == 32
    assert service.speed_multiplier == 1.0
    assert service.started is False


def test_speed_endpoint_updates_multiplier() -> None:
    """Changing the dropdown updates the service speed."""
    service = GameService()
    client = TestClient(create_app(service=service))

    response = client.post("/speed", data={"speed": "0.25"})

    assert response.status_code == 200
    assert service.speed_multiplier == 0.25
    assert '<option value="0.25" selected>' in response.text


def test_level_endpoint_restarts_requested_level() -> None:
    """Selecting a level restarts the game at the chosen level."""
    service = GameService()
    client = TestClient(create_app(service=service))

    response = client.post("/level", data={"level": "2"})

    assert response.status_code == 200
    assert service.selected_level == 2
    assert service.state.level.level_id == 2
    assert "Ready to start level 2." in response.text


def test_pause_endpoint_toggles_paused_state() -> None:
    """Pause endpoint toggles paused playback state."""
    service = GameService()
    client = TestClient(create_app(service=service))
    service.start()
    service.countdown_remaining = None

    response = client.post("/pause")

    assert response.status_code == 200
    assert service.paused is True
    assert "Paused" in response.text


def test_start_endpoint_arms_countdown() -> None:
    """Start begins the five-second countdown instead of immediate play."""
    service = GameService()
    client = TestClient(create_app(service=service))

    response = client.post("/start")

    assert response.status_code == 200
    assert service.started is True
    assert service.countdown_remaining == 5.0
    assert "Starting in 5.0s" in response.text
