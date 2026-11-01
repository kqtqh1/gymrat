"""Coach Dagzz images (PNG files in assets/)."""

import base64
from functools import lru_cache
from pathlib import Path
from typing import Literal

Mood = Literal["ready", "thinking", "hold_on", "oops"]

ASSETS = Path(__file__).parent / "assets"
def coach_image(mood: Mood | None = None) -> Path:
    return ASSETS / ("coach.png" if mood is None else f"{mood}.png")


@lru_cache
def _data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def png_size(path: Path) -> tuple[int, int]:
    """(width, height) straight from the PNG header."""
    header = path.read_bytes()[16:24]
    return int.from_bytes(header[:4], "big"), int.from_bytes(header[4:], "big")


def img_tag(path: Path, size: int, alt: str = "", height: int | None = None) -> str:
    """Inline <img> for use inside st.markdown HTML (bubbles, tips, header)."""
    role = f'alt="{alt}"' if alt else 'alt="" aria-hidden="true"'
    return (
        f'<img src="{_data_uri(path)}" width="{size}" height="{height or size}" '
        f'{role} style="flex-shrink:0;display:block;object-fit:contain"/>'
    )


def coach_tag(height: int, mood: Mood | None = None, alt: str = "") -> str:
    """Flexing coach at a given height, width scaled to keep his proportions."""
    path = coach_image(mood)
    width, full_height = png_size(path)
    return img_tag(path, height * width // full_height, alt, height)
