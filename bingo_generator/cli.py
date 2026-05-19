import argparse
import logging
import os
import re
import sys

from bingo_generator.config import load_config
from bingo_generator.generator import generate_phrases
from bingo_generator.renderer import render_bingo

logger = logging.getLogger(__name__)


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.WARNING),
        format="%(levelname)s %(name)s: %(message)s",
    )
    # Suppress noisy third-party loggers
    for name in ("httpcore", "httpx", "mistralai"):
        logging.getLogger(name).setLevel(logging.WARNING)


def parse_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", value)
    if not match:
        raise argparse.ArgumentTypeError(
            f"Invalid size '{value}'. Use format CxR, e.g. 5x5"
        )
    cols, rows = int(match.group(1)), int(match.group(2))
    if cols < 2 or rows < 2:
        raise argparse.ArgumentTypeError("Grid must be at least 2x2")
    return cols, rows


def main():
    parser = argparse.ArgumentParser(
        prog="bingo-generator",
        description="Generate bingo card images from a word or phrase",
    )
    parser.add_argument("topic", help="Word or phrase for the bingo card")
    parser.add_argument(
        "--size",
        type=parse_size,
        default=(5, 5),
        help="Grid size CxR (default: 5x5)",
    )
    parser.add_argument(
        "--style", default="minimal", help="Visual style (default: minimal)"
    )
    parser.add_argument("-o", "--output", default=None, help="Output file path")

    args = parser.parse_args()

    config = load_config()
    _setup_logging(config.get("log_level", "WARNING"))

    logger.debug(
        "CLI args: topic='%s', size=%s, style='%s'", args.topic, args.size, args.style
    )

    api_key = config["mistral"].get("api_key", "") or os.environ.get(
        "MISTRAL_API_KEY", ""
    )
    if not api_key:
        logger.warning("No Mistral API key configured")
        print(
            "Error: No Mistral API key found. Set it in bingo.yaml or MISTRAL_API_KEY env var.",
            file=sys.stderr,
        )
        sys.exit(1)

    cols, rows = args.size
    count = cols * rows

    print(f"Generating {count} bingo phrases about '{args.topic}'...")
    phrases = generate_phrases(
        topic=args.topic,
        count=count,
        model=config["mistral"]["model"],
        api_key=api_key,
        lang_hint=config.get("language", "auto"),
    )

    title = args.topic.upper()
    img = render_bingo(title, phrases, cols, rows, style=args.style)

    output = (
        args.output
        or f"bingo_{args.topic.replace(' ', '_')}.{config.get('format', 'png')}"
    )
    img.save(output)
    logger.debug("Image saved to '%s'", output)
    print(f"Saved to {output}")
