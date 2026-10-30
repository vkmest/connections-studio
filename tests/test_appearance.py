import json

import pytest

from connections import preferences
from connections.config import Settings
from connections.preferences import (
    load_appearance,
    load_preferences,
    save_appearance,
    save_preferences,
)


def test_appearance_and_provider_settings_do_not_overwrite_each_other():
    save_preferences(Settings(provider="deepseek", api_key="never-write-this"))
    save_appearance("dark", True)
    save_preferences(Settings(provider="kimi", api_key="also-secret"))
    assert load_appearance() == {"theme": "dark", "sidebar_collapsed": True}
    assert load_preferences() == {"provider": "kimi", "model": "kimi-k3.1-pro"}
    appearance = preferences.preference_path().with_name("appearance.json").read_text()
    assert json.loads(appearance) == {"theme": "dark", "sidebar_collapsed": True}
    assert "secret" not in appearance and "never-write" not in appearance


@pytest.mark.parametrize("payload", ['{"theme": [], "sidebar_collapsed": "yes"}', "[]", "bad json"])
def test_invalid_appearance_file_uses_safe_defaults(payload):
    path = preferences.preference_path().with_name("appearance.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload)
    assert load_appearance() == {"theme": "light", "sidebar_collapsed": False}
