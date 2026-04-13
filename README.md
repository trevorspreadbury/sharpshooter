# Sharpshooter

Sharpshooter is a small local web game built with FastAPI and a pure Python game engine. You run it locally, open it in a browser, and clear blue targets by firing orange shots from the top and bottom edges of the board.

## Run the game

Requirements:

- Python 3.10+
- `uv`

Install dependencies and start the app:

```bash
uv run sharpshooter
```

Then open `http://127.0.0.1:8000` in your browser.

## Run tests

```bash
uv run --extra dev pytest
```

## How to play

When the page loads, the selected level is in a ready state. The game does not start automatically.

1. Choose a start level if needed.
2. Click `Start`.
3. Wait for the 5-second countdown.
4. Click orange edge tiles to fire them inward.

You can also:

- Change playback speed to `Normal`, `Half`, `Quarter`, or `Eighth`
- Pause and resume the simulation
- Restart the current selected level

## Game mechanics

Board rules:

- The board is `16` columns by `28` rows.
- Orange tiles begin on the top and bottom edges.
- Blue tiles move horizontally and wrap around the board.
- Level 2 also includes red tiles that move horizontally and wrap around.

Orange firing:

- Clicking an orange fires that specific tile inward.
- Top oranges move downward.
- Bottom oranges move upward.
- Active orange shots show their full path while traveling.
- Oranges cannot be fired before the countdown ends.

Collisions:

- Orange hit blue: both disappear.
- Orange hit red: both disappear and you lose one life.
- In level 2, red tiles also destroy oranges on contact.

Win and loss conditions:

- Clear all blue tiles to beat the level.
- Clearing level 1 advances to level 2.
- Clear level 2 to win the game.
- You start with 5 lives.
- Each level has a 45-second timer once gameplay begins.
- Running out of lives or time ends the game.

## Project layout

- `src/sharpshooter/engine.py`: game rules and simulation
- `src/sharpshooter/service.py`: session state, countdown, pause, and timing
- `src/sharpshooter/main.py`: FastAPI app and routes
- `templates/`: server-rendered HTML
- `static/`: CSS and browser-side interaction code
- `tests/`: engine and app tests
