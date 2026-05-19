import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "provider": "mistral",
    "mistral": {
        "api_key": "",
        "model": "mistral-large-latest",
    },
    "language": "auto",
    "format": "png",
    "log_level": "WARNING",
}


def _load_yaml(path: Path) -> dict:
    if path.exists():
        logger.debug("Loading config from %s", path)
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    logger.debug("Config file not found: %s", path)
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

    user_cfg = _load_yaml(Path.home() / ".config" / "bingo-generator" / "config.yaml")
    config = _deep_merge(config, user_cfg)

    project_cfg = _load_yaml(Path("bingo.yaml"))
    config = _deep_merge(config, project_cfg)

    logger.debug(
        "Final merged config: %s", {k: v for k, v in config.items() if k != "mistral"}
    )
    return config
