# Bingo Generator

Generates bingo card images from a word or phrase. Uses Mistral AI to create humorous, relatable phrases and Pillow to render the card.

Available as a **CLI tool** and a **Telegram bot**.

## Setup

```bash
uv sync --extra dev
```

## Configuration

Copy the example config and add your API keys:

```bash
cp bingo.example.yaml bingo.yaml
```

Edit `bingo.yaml`:

```yaml
mistral:
  api_key: "your-mistral-api-key"

telegram:
  bot_token: "your-telegram-bot-token"  # only needed for the bot
```

You can also use environment variables: `MISTRAL_API_KEY`, `BINGO_TELEGRAM_TOKEN`.

Config is loaded with precedence: `./bingo.yaml` > `~/.config/bingo-generator/config.yaml` > defaults.

## CLI Usage

```bash
uv run bingo-generator "introvert"
uv run bingo-generator "геймер" --size 4x5
uv run bingo-generator "coffee lover" -o my_card.png
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `topic` | required | Word or phrase for the bingo card |
| `--size` | `5x5` | Grid size in `CxR` format (min 2x2) |
| `--style` | `minimal` | Visual style |
| `-o, --output` | `bingo_<topic>.png` | Output file path |

### Language

Language is auto-detected from the input. Cyrillic input produces Russian phrases, Latin input produces English phrases. Override in config:

```yaml
language: "ru"  # or "en", "auto"
```

## Telegram Bot

```bash
uv run bingo-bot
```

The bot responds to a single command:

```
/generate <topic>
```

Sends back a 5x5 bingo card image. Language is auto-detected from the topic.

### Logging

Set log level in config to see debug traces:

```yaml
log_level: "DEBUG"  # "INFO", "WARNING", "ERROR"
```

## Adding Styles

Create a new file in `bingo_generator/styles/` with a `render(title, phrases, cols, rows) -> PIL.Image` function, then register it in `bingo_generator/renderer.py`.

## Development

```bash
uv run pytest -v          # run tests
uv run ruff check .       # lint
uv run ruff format .      # format
```
