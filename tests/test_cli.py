import argparse

import pytest

from bingo_generator.cli import parse_size


def test_parse_size_valid():
    assert parse_size("5x5") == (5, 5)
    assert parse_size("4x5") == (4, 5)
    assert parse_size("3x3") == (3, 3)


def test_parse_size_invalid():
    with pytest.raises((ValueError, argparse.ArgumentTypeError)):
        parse_size("bad")
    with pytest.raises((ValueError, argparse.ArgumentTypeError)):
        parse_size("0x5")
