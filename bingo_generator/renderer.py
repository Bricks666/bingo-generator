import logging

from PIL import Image

from bingo_generator.styles import minimal

logger = logging.getLogger(__name__)

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
        logger.warning("Unknown style requested: '%s'", style)
        raise ValueError(f"Unknown style '{style}'. Available: {', '.join(STYLES)}")

    logger.debug(
        "Rendering bingo card: title='%s', grid=%dx%d, style='%s', phrases=%d",
        title,
        cols,
        rows,
        style,
        len(phrases),
    )
    img = STYLES[style].render(title, phrases, cols, rows)
    logger.debug("Rendered image size: %dx%d", img.size[0], img.size[1])
    return img
