import json

import pytest

from connections.config import Settings
from connections.credentials import CredentialError, CredentialStore
from connections.preferences import load_preferences, save_preferences


class MemoryVault:
    def __init__(self):
        self.entries = {}

    def get_password(self, service, user):
        return self.entries.get((service, user))

    def set_password(self, service, user, password):
        self.entries[service, user] = password

    def delete_password(self, service, user):
        self.entries.pop((service, user), None)


def test_vault_provider_isolation_and_forget():
    store = CredentialStore(backend=MemoryVault())
    store.save("openai", "openai-test-secret")
    store.save("kimi", "kimi-test-secret")
    assert store.get("kimi") == "kimi-test-secret"
    store.forget("openai")
    assert store.get("openai") == ""
    assert store.get("kimi") == "kimi-test-secret"
    with pytest.raises(CredentialError):
        store.save("ollama", "must-not-store")


def test_vault_error_never_exposes_backend_message():
    class BrokenVault(MemoryVault):
        def set_password(self, *args):
            raise RuntimeError("secret leaked by backend")

    with pytest.raises(CredentialError) as error:
        CredentialStore(backend=BrokenVault()).save("openai", "secret")
    assert "secret" not in str(error.value)


def test_preferences_never_serialize_key(tmp_path):
    path = tmp_path / "preferences.json"
    save_preferences(Settings(api_key="private-value", provider="kimi"), path=path)
    payload = json.loads(path.read_text())
    assert payload == {"provider": "kimi", "model": "kimi-k3.1-pro"}
    assert "private-value" not in path.read_text()
    assert load_preferences(path=path) == payload


def test_provider_env_never_borrows_openai_key(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-only")
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    monkeypatch.delenv("CONNECTIONS_MODEL", raising=False)
    store = CredentialStore(backend=MemoryVault())
    settings = Settings.from_environment(provider="kimi", store=store, preferences={})
    assert settings.api_key == ""
    assert "openai-only" not in repr(settings)


def test_ollama_discards_any_key():
    assert Settings(api_key="never-send", provider="ollama").api_key == ""


def test_saved_key_loaded_without_environment_leak(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    store = CredentialStore(backend=MemoryVault())
    store.save("deepseek", "saved-test-key")
    settings = Settings.from_environment(provider="deepseek", store=store, preferences={})
    assert settings.api_key == "saved-test-key"
    assert "saved-test-key" not in repr(settings)
