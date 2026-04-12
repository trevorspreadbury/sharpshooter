"""FastAPI entrypoint for the Sharpshooter web app."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sharpshooter.service import GameService, SPEED_OPTIONS

ROOT_DIR = Path(__file__).resolve().parents[2]


def create_app(service: GameService | None = None) -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(title="Sharpshooter")
    templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))
    game_service = service or GameService()

    app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")

    def render(request: Request) -> HTMLResponse:
        snapshot = game_service.sync()
        return templates.TemplateResponse(
            request=request,
            name="game.html",
            context={
                "snapshot": snapshot,
                "speed_multiplier": game_service.speed_multiplier,
                "speed_options": SPEED_OPTIONS,
            },
        )

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        """Render the root page."""
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "snapshot": game_service.sync(),
                "speed_multiplier": game_service.speed_multiplier,
                "speed_options": SPEED_OPTIONS,
            },
        )

    @app.get("/snapshot", response_class=HTMLResponse)
    async def snapshot(request: Request) -> HTMLResponse:
        """Render the live game partial."""
        return render(request)

    @app.post("/fire/{row}/{col}", response_class=HTMLResponse)
    async def fire(request: Request, row: int, col: int) -> HTMLResponse:
        """Fire one orange tile and rerender the board."""
        snapshot = game_service.fire(row=row, col=col)
        return templates.TemplateResponse(
            request=request,
            name="game.html",
            context={
                "snapshot": snapshot,
                "speed_multiplier": game_service.speed_multiplier,
                "speed_options": SPEED_OPTIONS,
            },
        )

    @app.post("/restart", response_class=HTMLResponse)
    async def restart(request: Request) -> HTMLResponse:
        """Restart the game and rerender the board."""
        game_service.restart()
        return templates.TemplateResponse(
            request=request,
            name="game.html",
            context={
                "snapshot": game_service.sync(),
                "speed_multiplier": game_service.speed_multiplier,
                "speed_options": SPEED_OPTIONS,
            },
        )

    @app.post("/speed", response_class=HTMLResponse)
    async def set_speed(request: Request, speed: float = Form(...)) -> HTMLResponse:
        """Update game speed and rerender the board."""
        snapshot = game_service.set_speed(speed)
        return templates.TemplateResponse(
            request=request,
            name="game.html",
            context={
                "snapshot": snapshot,
                "speed_multiplier": game_service.speed_multiplier,
                "speed_options": SPEED_OPTIONS,
            },
        )

    return app


app = create_app()
