"""Persist nonsecret preferences separately from OS-managed credentials."""

import json
from pathlib import Path

from platformdirs import user_config_path

from connections.providers import PROVIDERS


def preference_path() -> Path:
    return user_config_path("Connections Studio", appauthor=False) / "preferences.json"


def load_preferences(*, path: Path | None = None) -> dict:
    try:
        data = json.loads((path or preference_path()).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("provider") not in PROVIDERS:
            return {}
        model = data.get("model")
        if not isinstance(model, str) or not model.strip() or len(model) > 200:
            return {}
        return {"provider": data["provider"], "model": model.strip()}
    except (OSError, ValueError):
        return {}


def save_preferences(settings, *, path: Path | None = None) -> None:
    target = path or preference_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    # Never serialize Settings/asdict: that would include the credential.
    data = {"provider": settings.provider, "model": settings.model}
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(target)


def load_appearance() -> dict:
    defaults = {"theme": "light", "sidebar_collapsed": False}
    try:
        data = json.loads(
            preference_path().with_name("appearance.json").read_text(encoding="utf-8")
        )
        if isinstance(data, dict):
            if isinstance(data.get("theme"), str) and data["theme"] in {"light", "dark"}:
                defaults["theme"] = data["theme"]
            if isinstance(data.get("sidebar_collapsed"), bool):
                defaults["sidebar_collapsed"] = data["sidebar_collapsed"]
    except (OSError, ValueError):
        pass
    return defaults


def save_appearance(theme: str, sidebar_collapsed: bool) -> None:
    if theme not in {"light", "dark"}:
        raise ValueError("Choose light or dark appearance.")
    target = preference_path().with_name("appearance.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"theme": theme, "sidebar_collapsed": sidebar_collapsed}), encoding="utf-8"
    )
    temporary.replace(target)
