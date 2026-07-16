# Asteroids: Deep Space

An Asteroids-style game built with Pygame.

## Run

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```powershell
uv run python main.py
```

## Controls

| Keys | Action |
| --- | --- |
| W / S | Thrust forward / backward |
| A / D | Turn |
| Space | Fire |
| 1 / 2 / 3 | Select weapon |
| B | Drop a bomb |
| R | Restart after game over |
| Esc | Quit |

Shield and speed power-ups can drop from asteroids.

## Checks

```powershell
uv run python -m unittest discover -s tests -v
uv run ruff check .
```
