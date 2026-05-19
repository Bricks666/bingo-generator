# Bingo Generator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that takes a word/phrase, generates bingo cell content via Mistral AI, and renders a bingo card image.

**Architecture:** Single-package Python CLI. Config loaded from YAML, content generated via Mistral AI API, image rendered with Pillow. Styles are pluggable modules.

**Tech Stack:** Python 3.14, mistralai, Pillow, PyYAML, pytest

**Fonts available:** Open Sans at `/usr/share/fonts/open-sans/OpenSans-{Regular,Bold}.ttf` (Cyrillic+Latin support)

---

### Task 1: Project scaffold

**Files:**
- Create: `bingo_generator/__init__.py`
- Create: `bingo_generator/styles/__init__.py`
- Create: `pyproject.toml`

**Step 1: Create package structure**

```bash
mkdir -p bingo_generator/styles
touch bingo_generator/__init__.py bingo_generator/styles/__init__.py
```

**Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "bingo-generator"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "mistralai>=1.0",
    "Pillow>=10.0",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
bingo-generator = "bingo_generator.cli:main"
```

**Step 3: Install in editable mode**

Run: `source .venv/bin/activate && pip install -e ".[dev]"`
Expected: success

**Step 4: Commit**

```bash
git init
git add pyproject.toml bingo_generator/
git commit -m "feat: project scaffold with package structure"
```

---

### Task 2: Config loader

**Files:**
- Create: `bingo_generator/config.py`
- Create: `tests/test_config.py`

**Step 1: Write tests for config loading**

```python
# tests/test_config.py
import pytest
from bingo_generator.config import load_config, DEFAULT_CONFIG


def test_default_config_values():
    cfg = load_config()
    assert cfg["provider"] == "mistral"
    assert cfg["language"] == "auto"
    assert cfg["format"] == "png"
    assert "model" in cfg["mistral"]


def test_project_config_overrides_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_file = tmp_path / "bingo.yaml"
    cfg_file.write_text("language: en\nmistral:\n  model: mistral-small\n")
    cfg = load_config()
    assert cfg["language"] == "en"
    assert cfg["mistral"]["model"] == "mistral-small"


def test_missing_config_file_uses_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg == DEFAULT_CONFIG
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_config.py -v`
Expected: FAIL (module not found)

**Step 3: Implement config.py**

```python
# bingo_generator/config.py
from pathlib import Path
import yaml

DEFAULT_CONFIG = {
    "provider": "mistral",
    "mistral": {
        "api_key": "",
        "model": "mistral-large-latest",
    },
    "language": "auto",
    "format": "png",
}


def _load_yaml(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    return {}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()

    # User config: ~/.config/bingo-generator/config.yaml
    user_cfg = _load_yaml(Path.home() / ".config" / "bingo-generator" / "config.yaml")
    config = _deep_merge(config, user_cfg)

    # Project config: ./bingo.yaml
    project_cfg = _load_yaml(Path("bingo.yaml"))
    config = _deep_merge(config, project_cfg)

    return config
```

**Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bingo_generator/config.py tests/test_config.py
git commit -m "feat: YAML config loader with merge precedence"
```

---

### Task 3: Generator (Mistral AI content)

**Files:**
- Create: `bingo_generator/generator.py`
- Create: `tests/test_generator.py`

**Step 1: Write tests**

```python
# tests/test_generator.py
import json
import pytest
from unittest.mock import patch, MagicMock
from bingo_generator.generator import generate_phrases


@patch("bingo_generator.generator.Mistral")
def test_generate_phrases_returns_correct_count(MockMistral):
    mock_client = MagicMock()
    MockMistral.return_value = mock_client
    phrases = ["phrase one", "phrase two", "phrase three"]
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(phrases)))]
    )

    result = generate_phrases("introvert", count=3, model="mistral-large-latest")
    assert len(result) == 3
    assert result[0] == "phrase one"


@patch("bingo_generator.generator.Mistral")
def test_generate_phrases_language_hint(MockMistral):
    mock_client = MagicMock()
    MockMistral.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(["а", "б"])))]
    )

    generate_phrases("социофоб", count=2, model="mistral-large-latest", lang_hint="Russian")

    call_args = mock_client.chat.complete.call_args
    prompt = call_args[1]["messages"][1]["content"]
    assert "Russian" in prompt
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_generator.py -v`
Expected: FAIL

**Step 3: Implement generator.py**

```python
# bingo_generator/generator.py
import json
from mistralai import Mistral


def _detect_lang_hint(topic: str) -> str:
    has_cyrillic = any("Ѐ" <= c <= "ӿ" for c in topic)
    if has_cyrillic:
        return "Russian"
    return "English"


def generate_phrases(
    topic: str,
    count: int,
    model: str,
    api_key: str = "",
    lang_hint: str = "",
) -> list[str]:
    if not lang_hint or lang_hint == "auto":
        lang_hint = _detect_lang_hint(topic)

    prompt = (
        f"Generate exactly {count} short, funny, relatable bingo phrases about '{topic}'. "
        f"Each phrase should be 2-8 words. "
        f"Write them in {lang_hint}. "
        f"Return ONLY a JSON array of strings, no other text. Example: [\"phrase1\", \"phrase2\"]"
    )

    client = Mistral(api_key=api_key) if api_key else Mistral()

    response = client.chat.complete(
        model=model,
        messages=[
            {"role": "system", "content": "You are a creative assistant that generates humorous bingo card content. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    content = response.choices[0].message.content.strip()
    phrases = json.loads(content)

    if not isinstance(phrases, list):
        raise ValueError("Expected a JSON array of strings")

    return [str(p) for p in phrases[:count]]
```

**Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_generator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bingo_generator/generator.py tests/test_generator.py
git commit -m "feat: Mistral AI phrase generator with language detection"
```

---

### Task 4: Minimal style renderer

**Files:**
- Create: `bingo_generator/renderer.py`
- Create: `bingo_generator/styles/minimal.py`
- Create: `tests/test_renderer.py`

**Step 1: Write tests**

```python
# tests/test_renderer.py
from PIL import Image
from bingo_generator.renderer import render_bingo


def test_render_bingo_returns_image():
    phrases = [f"phrase {i}" for i in range(9)]
    img = render_bingo("Test Bingo", phrases, cols=3, rows=3, style="minimal")
    assert isinstance(img, Image.Image)
    assert img.size[0] > 0 and img.size[1] > 0


def test_render_bingo_5x5():
    phrases = [f"item {i}" for i in range(25)]
    img = render_bingo("Big Bingo", phrases, cols=5, rows=5, style="minimal")
    assert isinstance(img, Image.Image)


def test_render_bingo_invalid_style():
    phrases = [f"p{i}" for i in range(4)]
    try:
        render_bingo("Test", phrases, cols=2, rows=2, style="nonexistent")
        assert False, "Should have raised"
    except ValueError:
        pass
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_renderer.py -v`
Expected: FAIL

**Step 3: Implement styles/minimal.py**

```python
# bingo_generator/styles/minimal.py
from PIL import Image, ImageDraw, ImageFont
import textwrap

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
```

**Step 4: Implement renderer.py (style dispatcher)**

```python
# bingo_generator/renderer.py
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
```

**Step 5: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_renderer.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add bingo_generator/renderer.py bingo_generator/styles/minimal.py tests/test_renderer.py
git commit -m "feat: minimal bingo card renderer with Pillow"
```

---

### Task 5: CLI entry point

**Files:**
- Create: `bingo_generator/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write tests**

```python
# tests/test_cli.py
import pytest
from unittest.mock import patch, MagicMock
from bingo_generator.cli import parse_size


def test_parse_size_valid():
    assert parse_size("5x5") == (5, 5)
    assert parse_size("4x5") == (4, 5)
    assert parse_size("3x3") == (3, 3)


def test_parse_size_invalid():
    with pytest.raises(ValueError):
        parse_size("bad")
    with pytest.raises(ValueError):
        parse_size("0x5")
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_cli.py -v`
Expected: FAIL

**Step 3: Implement cli.py**

```python
# bingo_generator/cli.py
import argparse
import re
import sys
from pathlib import Path

from bingo_generator.config import load_config
from bingo_generator.generator import generate_phrases
from bingo_generator.renderer import render_bingo


def parse_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", value)
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid size '{value}'. Use format CxR, e.g. 5x5")
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
    parser.add_argument("--size", type=parse_size, default=(5, 5), help="Grid size CxR (default: 5x5)")
    parser.add_argument("--style", default="minimal", help="Visual style (default: minimal)")
    parser.add_argument("-o", "--output", default=None, help="Output file path")

    args = parser.parse_args()

    config = load_config()

    api_key = config["mistral"].get("api_key", "")
    if not api_key:
        print("Error: No Mistral API key found. Set it in bingo.yaml or MISTRAL_API_KEY env var.", file=sys.stderr)
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

    output = args.output or f"bingo_{args.topic.replace(' ', '_')}.{config.get('format', 'png')}"
    img.save(output)
    print(f"Saved to {output}")
```

**Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_cli.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bingo_generator/cli.py tests/test_cli.py
git commit -m "feat: CLI entry point with argparse"
```

---

### Task 6: End-to-end smoke test

**Files:**
- None new

**Step 1: Install the package**

Run: `source .venv/bin/activate && pip install -e .`
Expected: success

**Step 2: Test help output**

Run: `source .venv/bin/activate && bingo-generator --help`
Expected: shows usage with topic, --size, --style, -o args

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: finalize v0.1.0 package setup"
```

---

### Task 7: Create .gitignore

**Files:**
- Create: `.gitignore`

**Step 1: Create .gitignore**

```
.venv/
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.pytest_cache/
*.png
!examples/*.png
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```
