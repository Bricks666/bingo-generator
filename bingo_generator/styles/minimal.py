import logging

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

FONT_BOLD = "/usr/share/fonts/open-sans/OpenSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/open-sans/OpenSans-Regular.ttf"

PADDING = 20
CELL_PADDING = 10
TITLE_HEIGHT = 70
BORDER_WIDTH = 2


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        logger.warning("Font not found at '%s', falling back to default", path)
        return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    lines = []
    for word in text.split():
        if not lines:
            lines.append(word)
        else:
            test = lines[-1] + " " + word
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                lines[-1] = test
            else:
                lines.append(word)
    return lines if lines else [""]


def render(title: str, phrases: list[str], cols: int, rows: int) -> Image.Image:
    logger.debug(
        "Minimal render: '%s' %dx%d, %d phrases", title, cols, rows, len(phrases)
    )
    cell_size = 180
    title_font = _load_font(FONT_BOLD, 28)
    cell_font = _load_font(FONT_REGULAR, 14)

    grid_w = cols * cell_size
    grid_h = rows * cell_size
    img_w = grid_w + 2 * PADDING
    img_h = grid_h + TITLE_HEIGHT + 2 * PADDING

    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)

    # Title
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = title_bbox[2] - title_bbox[0]
    tx = (img_w - tw) // 2
    draw.text((tx, PADDING), title, fill="black", font=title_font)

    # Grid
    grid_top = PADDING + TITLE_HEIGHT
    for row in range(rows):
        for col in range(cols):
            x = PADDING + col * cell_size
            y = grid_top + row * cell_size
            idx = row * cols + col

            draw.rectangle(
                [x, y, x + cell_size, y + cell_size],
                outline="black",
                width=BORDER_WIDTH,
            )

            if idx < len(phrases):
                max_w = cell_size - 2 * CELL_PADDING
                wrapped = _wrap_text(phrases[idx], cell_font, max_w, draw)
                line_h = draw.textbbox((0, 0), "Ay", font=cell_font)[3] + 4
                total_h = len(wrapped) * line_h
                ty = y + (cell_size - total_h) // 2
                for i, line in enumerate(wrapped):
                    draw.text(
                        (x + CELL_PADDING, ty + i * line_h),
                        line,
                        fill="black",
                        font=cell_font,
                    )

    return img
