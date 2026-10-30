"""Keep automated Qt tests independent of desktop focus and accessibility clients."""

import os

import pytest

# Set before pytest-qt creates QApplication; native UI checks run separately.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def isolate_user_settings(monkeypatch, tmp_path):
    from test_security import MemoryVault

    from connections import credentials, preferences

    vault = MemoryVault()
    monkeypatch.chdir(tmp_path)
    for variable in (
        "OPENAI_API_KEY",
        "MOONSHOT_API_KEY",
        "DEEPSEEK_API_KEY",
        "CONNECTIONS_PROVIDER",
        "CONNECTIONS_MODEL",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(credentials, "native_backend", lambda: vault)
    monkeypatch.setattr(preferences, "preference_path", lambda: tmp_path / "preferences.json")
