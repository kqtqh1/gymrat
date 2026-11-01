"""Build the header coach images from one flexing-rat drawing on a black background."""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "assets"
OUTPUT_WIDTH = 320  # shown ~158px wide in the header; 2x keeps it sharp on high-DPI screens

INK = (19, 13, 32)  # matches the drawing's outline
WHITE = (255, 255, 255)
YELLOW = (255, 201, 60)

# Positions are in the source drawing's pixels (1254 x 1254)
LEFT_RAYS = (90, 400, 240, 525)
RIGHT_RAYS = (1070, 400, 1215, 530)
BADGE_CENTER = (1150, 395)
BADGE_RADIUS = 105
LINE = 15
GLYPH = 28

MOODS = {
    # mood: (badge fill, left-ray color )
    "ready": ((47, 177, 102), YELLOW),
    "thinking": (WHITE, (182, 176, 210)),
    "hold_on": ((255, 190, 40), (255, 190, 40)),
    "oops": ((232, 72, 77), (232, 72, 77)),
}


def cut_out(path: Path) -> np.ndarray:
    """RGBA array with the black background removed and anti-aliased edges faded out."""
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(float)
    alpha = np.clip((rgb.sum(axis=2) - 6) / 24, 0, 1)
    rgb = np.clip(rgb / np.maximum(alpha, 1e-3)[..., None], 0, 255) * (alpha[..., None] > 0)
    return np.dstack([rgb, alpha * 255])


def ray_mask(img: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """Yellow ray pixels inside box."""
    x0, y0, x1, y1 = box
    mask = np.zeros(img.shape[:2], bool)
    r, g, b = img[y0:y1, x0:x1, 0], img[y0:y1, x0:x1, 1], img[y0:y1, x0:x1, 2]
    mask[y0:y1, x0:x1] = ((r + g) / 2 - b > 40) & (img[y0:y1, x0:x1, 3] > 0)
    return mask


def grow(mask: np.ndarray, px: int) -> np.ndarray:
    """Expand a mask by px pixels, to catch the rays' anti-aliased edges."""
    out = mask.copy()
    for dy in range(-px, px + 1):
        for dx in range(-px, px + 1):
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def dot(draw: ImageDraw.ImageDraw, xy: tuple[float, float], r: float, fill) -> None:
    x, y = xy
    draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def stroke(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], width: int, fill) -> None:
    """Thick line with round caps and joints."""
    draw.line(points, fill=fill, width=width, joint="curve")
    for p in points:
        dot(draw, p, width / 2, fill)


def draw_badge(draw: ImageDraw.ImageDraw, mood: str, fill) -> None:
    cx, cy = BADGE_CENTER
    r = BADGE_RADIUS
    if mood == "thinking":
        # Thought bubble trailing down toward the rat's head
        dot(draw, (1062, 492), 22, INK)
        dot(draw, (1062, 492), 22 - LINE * 0.8, fill)
        dot(draw, (1030, 526), 13, INK)
        dot(draw, (1030, 526), 13 - LINE * 0.7, fill)
        draw.ellipse((cx - r - 10, cy - r + 14, cx + r + 10, cy + r - 14), fill=fill, outline=INK, width=LINE)
        for dx in (-44, 0, 44):
            dot(draw, (cx + dx, cy), 15, INK)
        return

    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline=INK, width=LINE)
    if mood == "ready":
        stroke(draw, [(cx - 46, cy + 4), (cx - 12, cy + 38), (cx + 46, cy - 32)], GLYPH, WHITE)
    elif mood == "hold_on":
        stroke(draw, [(cx, cy - 56), (cx, cy + 14)], GLYPH, INK)
        dot(draw, (cx, cy + 50), 17, INK)
    elif mood == "oops":
        stroke(draw, [(cx - 38, cy - 38), (cx + 38, cy + 38)], GLYPH, WHITE)
        stroke(draw, [(cx + 38, cy - 38), (cx - 38, cy + 38)], GLYPH, WHITE)


def save(img: np.ndarray, crop: tuple[int, int, int, int], name: str) -> None:
    out = Image.fromarray(img.astype(np.uint8), "RGBA").crop(crop)
    out = out.resize((OUTPUT_WIDTH, round(out.height * OUTPUT_WIDTH / out.width)), Image.LANCZOS)
    # a flat cartoon fits in 256 colors; this keeps each file ~20 KB, since it is resent on every rerun
    out = out.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    out.save(ASSETS / name, optimize=True)
    print(f"{name}: {out.size[0]}x{out.size[1]}")


def main(source: Path) -> None:
    base = cut_out(source)
    # same crop for every image (union of the rat and the badge area) so they line up in the header
    crop = Image.fromarray(base.astype(np.uint8), "RGBA").getbbox()
    crop = (crop[0], min(crop[1], BADGE_CENTER[1] - BADGE_RADIUS - 8), max(crop[2], BADGE_CENTER[0] + BADGE_RADIUS + 20), crop[3])
    save(base, crop, "coach.png")

    left, right = ray_mask(base, LEFT_RAYS), grow(ray_mask(base, RIGHT_RAYS), 6)
    for mood, (badge_fill, ray_color) in MOODS.items():
        img = base.copy()
        img[left, :3] = ray_color
        img[right, 3] = 0
        layer = Image.new("RGBA", (img.shape[1], img.shape[0]))
        draw_badge(ImageDraw.Draw(layer), mood, badge_fill)
        composed = Image.alpha_composite(Image.fromarray(img.astype(np.uint8), "RGBA"), layer)
        save(np.asarray(composed).astype(float), crop, f"{mood}.png")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ASSETS / "coach.png")
