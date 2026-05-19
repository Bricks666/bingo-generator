from PIL import Image
from bingo_generator.styles import minimal

STYLES = {
    "minimal": minimal,
}


def render_bingo(
    title: str,
    phrases: list[str],
    cols: int,
    rows: int,
    style: str = "minimal",
) -> Image.Image:
    if style not in STYLES:
        raise ValueError(f"Unknown style '{style}'. Available: {', '.join(STYLES)}")
    return STYLES[style].render(title, phrases, cols, rows)
