# Bingo Generator

CLI tool that generates bingo card images from a word or phrase. Uses Mistral AI to create humorous, relatable phrases and Pillow to render the card.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Copy the example config and add your Mistral API key:

```bash
cp bingo.example.yaml bingo.yaml
```

Edit `bingo.yaml` and set your API key:

```yaml
mistral:
  api_key: "your-api-key-here"
```

You can also set the key via environment variable:

```bash
export MISTRAL_API_KEY="your-api-key-here"
```

Config is loaded with precedence: CLI flags > `./bingo.yaml` > `~/.config/bingo-generator/config.yaml` > defaults.

## Usage

```bash
# Basic usage (5x5 grid, minimal style)
bingo-generator "introvert"

# Custom grid size (columns x rows)
bingo-generator "геймер" --size 4x5

# Custom output file
bingo-generator "coffee lover" -o my_card.png

# Custom style
bingo-generator "developer" --style pastel
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

## Examples

Input phrases and topics can be in any language. The generator adapts automatically:

| Input | Output |
|-------|--------|
| `bingo-generator "социофоб"` | Russian bingo card |
| `bingo-generator "cat person"` | English bingo card |

See `examples/` for sample outputs.

## Adding Styles

Create a new file in `bingo_generator/styles/` with a `render(title, phrases, cols, rows) -> PIL.Image` function, then register it in `bingo_generator/renderer.py`.
