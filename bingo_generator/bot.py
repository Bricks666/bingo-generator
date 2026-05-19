import io
import logging
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from bingo_generator.config import load_config
from bingo_generator.generator import generate_phrases
from bingo_generator.renderer import render_bingo

logger = logging.getLogger(__name__)

GREETING = (
    "Hey! I'm Bingo Generator bot 🎱\n\n"
    "I create funny bingo cards on any topic.\n\n"
    "/generate <topic> — generate a 5x5 bingo card\n"
    "/help — show this message"
)

HELP_TEXT = (
    "🎱 *Bingo Generator Bot*\n\n"
    "I generate humorous bingo cards with absurdly specific observations "
    "about any topic.\n\n"
    "*Commands:*\n"
    "/generate <topic> — create a 5x5 bingo card image\n"
    "/help — show this message\n\n"
    "*Examples:*\n"
    "`/generate introvert`\n"
    "`/generate геймер`\n"
    "`/generate coffee addict`\n\n"
    "Language is auto-detected from your input. "
    "Cyrillic → Russian, Latin → English."
)


async def start_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(GREETING)


async def help_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /generate <topic>")
        return

    topic = " ".join(context.args)
    cols, rows = 5, 5
    count = cols * rows

    await update.message.chat.send_action("upload_photo")

    config = load_config()
    api_key = config["mistral"].get("api_key", "") or os.environ.get(
        "MISTRAL_API_KEY", ""
    )
    model = config["mistral"]["model"]

    logger.debug("Bot generate: topic='%s', model=%s", topic, model)

    try:
        phrases = generate_phrases(
            topic=topic,
            count=count,
            model=model,
            api_key=api_key,
            lang_hint=config.get("language", "auto"),
        )

        title = topic.upper()
        img = render_bingo(title, phrases, cols, rows, style="minimal")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        await update.message.reply_photo(photo=buf)
        logger.debug("Sent bingo image for '%s'", topic)

    except Exception:
        logger.warning("Failed to generate bingo for '%s'", topic, exc_info=True)
        await update.message.reply_text("Failed to generate bingo. Try again later.")


def main() -> None:
    config = load_config()

    log_level = config.get("log_level", "WARNING")
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.WARNING),
        format="%(levelname)s %(name)s: %(message)s",
    )
    for name in ("httpcore", "httpx", "mistralai"):
        logging.getLogger(name).setLevel(logging.WARNING)

    token = config.get("telegram", {}).get("bot_token", "") or os.environ.get(
        "BINGO_TELEGRAM_TOKEN", ""
    )
    if not token:
        logger.warning("No Telegram bot token configured")
        print(
            "Error: No Telegram bot token found. "
            "Set telegram.bot_token in bingo.yaml or BINGO_TELEGRAM_TOKEN env var.",
        )
        raise SystemExit(1)

    logger.debug("Starting Telegram bot")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("generate", generate_command))

    print("Bingo Generator bot is running...")
    app.run_polling()
