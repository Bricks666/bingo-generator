from pathlib import Path

from bingo_generator.config import DEFAULT_CONFIG, load_config


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
    # Mock home to a tmp dir so user config doesn't interfere
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    cfg = load_config()
    assert cfg["language"] == "en"
    assert cfg["mistral"]["model"] == "mistral-small"


def test_missing_config_file_uses_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Mock home to a tmp dir with no config
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
    cfg = load_config()
    assert cfg == DEFAULT_CONFIG
