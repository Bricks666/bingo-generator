# Bingo Generator — Design

## Purpose

CLI tool that takes a word or phrase and generates a bingo-style image. Uses Mistral AI to generate cell content, Pillow to render the image.

## Architecture

```
bingo_generator/
├── __init__.py
├── cli.py          # argparse CLI, config merge, orchestration
├── config.py       # YAML loader for provider/model/lang/format constants
├── generator.py    # Mistral AI prompt + response parsing
├── renderer.py     # Pillow drawing (style dispatch)
└── styles/
    ├── __init__.py
    └── minimal.py  # default style
```

Single entry point `bingo-generator` does 3 things in sequence:
1. **Generate content** — call Mistral AI with topic + grid size, get back a flat list of phrases
2. **Render image** — pass title + phrases + style to a renderer that draws the grid with Pillow
3. **Save output** — write PNG to specified file path

## CLI Interface

```
bingo-generator "социофоб"                       # default 5x5, minimal style
bingo-generator "introvert" --size 4x5            # 4 columns, 5 rows
bingo-generator "геймер" --style pastel -o my.png # custom output
```

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `topic` | positional | required | The word or phrase |
| `--size` | `CxR` | `5x5` | Grid dimensions |
| `--style` | string | `minimal` | Visual style |
| `-o / --output` | path | `bingo_<topic>.png` | Output file path |

## Config

YAML config for persistent settings only (provider, model, language, format). Loaded with precedence:

1. Project config: `./bingo.yaml`
2. User config: `~/.config/bingo-generator/config.yaml`
3. Built-in defaults

```yaml
provider: "mistral"
mistral:
  api_key: "..."
  model: "mistral-large-latest"
language: "auto"
format: "png"
```

CLI flags always override config values where applicable.

## Data Flow

1. CLI parses args → loads config → merges
2. Calls `generator.generate(topic, count, lang_hint)`
3. Generator sends structured prompt to Mistral: "generate N short bingo phrases about <topic> in <language>. Return JSON array of strings."
4. Response parsed into list of strings
5. Renderer dispatches to style module with `(title, phrases, cols, rows)`
6. Pillow draws grid, wraps text in cells, saves image

## Style System

Each style module exposes `render(title, phrases, cols, rows) -> PIL.Image`. Adding a style = adding a file + registering in a dict.

Default style (`minimal`): white background, black text, thin black borders, bold title. Matches example3 aesthetic.

## Error Handling

- No API key → clear error message
- Mistral returns fewer phrases than needed → retry once, then error
- Invalid `--size` format → argparse validation
- Font not found → fall back to Pillow default font

## Dependencies

- `mistralai` — AI content generation
- `Pillow` — image rendering
- `PyYAML` — config loading
