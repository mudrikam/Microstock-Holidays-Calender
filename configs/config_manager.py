import json
import os
from pathlib import Path
from datetime import datetime


_CONFIG_PATH = Path(__file__).parent / "config.json"
_TEMP_DIR = Path(__file__).parent.parent / "temp"
_TEMP_DIR.mkdir(parents=True, exist_ok=True)
_SECRETS_PATH = _TEMP_DIR / "secrets.json"

_DEFAULTS = {
    "api": {
        "key": "",
        "base_url": "https://calendarific.com/api/v2",
        "default_country": "US"
    },
    "cache": {
        "expire_days": 7,
        "use_sqlite": True,
        "sqlite_path": "cache.db",
        "json_fallback_path": "temp/cache_fallback.json"
    },
    "ui": {
        "window_width": 1280,
        "window_height": 800,
        "sidebar_width": 200,
        "detail_panel_width": 300,
        "last_country": "US",
        "last_year": datetime.now().year,
        "last_month": datetime.now().month,
        "view_mode": "list"
    }
}

_config = {}


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load():
    global _config
    try:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            _config = _deep_merge(_DEFAULTS, loaded)
        else:
            _config = dict(_DEFAULTS)
            save()
    except Exception as e:
        print(f"Configuration load failed: {e}")
        _config = dict(_DEFAULTS)


def save():
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(_config, f, indent=2)


def get(section: str, key: str, fallback=None):
    return _config.get(section, {}).get(key, fallback)


def set_value(section: str, key: str, value):
    if section not in _config:
        _config[section] = {}
    _config[section][key] = value


def get_api_key() -> str:
    if _SECRETS_PATH.exists():
        try:
            with open(_SECRETS_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("api_key", "")
        except Exception:
            pass
    return get("api", "key", "")


def get_base_url() -> str:
    return get("api", "base_url", "https://calendarific.com/api/v2")


def get_default_country() -> str:
    return get("api", "default_country", "US")


def get_ui(key: str, fallback=None):
    return get("ui", key, fallback)


def set_ui(key: str, value):
    set_value("ui", key, value)


def get_cache(key: str, fallback=None):
    return get("cache", key, fallback)


def get_app(key: str, fallback="") -> str:
    return get("app", key, fallback)


load()
