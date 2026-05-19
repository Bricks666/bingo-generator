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
    import pytest

    phrases = [f"p{i}" for i in range(4)]
    with pytest.raises(ValueError):
        render_bingo("Test", phrases, cols=2, rows=2, style="nonexistent")
