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
    user_cfg = _load_yaml(
        Path.home() / ".config" / "bingo-generator" / "config.yaml"
    )
    config = _deep_merge(config, user_cfg)

    # Project config: ./bingo.yaml
    project_cfg = _load_yaml(Path("bingo.yaml"))
    config = _deep_merge(config, project_cfg)

    return config
