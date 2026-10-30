"""Explicit configuration; importing this module never reads a key."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

from connections.credentials import CredentialError, CredentialStore
from connections.preferences import load_preferences
from connections.providers import PROVIDERS

DEFAULT_MODEL = "gpt-5.4-mini"
# Standard USD rates per million tokens, checked 2026-10-30. Not a billing guarantee.
MODEL_RATES = {DEFAULT_MODEL: (0.75, 0.075, 4.50)}


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    model: str = ""
    provider: str = "openai"

    def __post_init__(self):
        if self.provider not in PROVIDERS:
            raise ValueError("Unknown provider. Choose OpenAI, Kimi, DeepSeek or Ollama.")
        model = self.model.strip() or PROVIDERS[self.provider].default_model
        if len(model) > 200 or any(character.isspace() for character in model):
            raise ValueError("Enter a valid model name without spaces (up to 200 characters).")
        object.__setattr__(self, "model", model)
        if self.provider == "ollama":
            object.__setattr__(self, "api_key", "")

    @classmethod
    def from_environment(
        cls, provider=None, model=None, *, store=None, preferences=None
    ) -> "Settings":
        # Only the launch directory's .env is considered, never arbitrary parent files.
        values = {**dotenv_values(Path.cwd() / ".env"), **os.environ}
        preferences = load_preferences() if preferences is None else preferences
        chosen = (
            provider or values.get("CONNECTIONS_PROVIDER") or preferences.get("provider", "openai")
        )
        if chosen not in PROVIDERS:
            raise ValueError("Unknown CONNECTIONS_PROVIDER. Use openai, kimi, deepseek or ollama.")
        saved_model = preferences.get("model", "") if preferences.get("provider") == chosen else ""
        # A CLI provider override must not inherit another provider's generic model override.
        env_model = (
            values.get("CONNECTIONS_MODEL", "")
            if not provider or chosen == (values.get("CONNECTIONS_PROVIDER") or "openai")
            else ""
        )
        key = ""
        if chosen != "ollama":
            key = (values.get(PROVIDERS[chosen].key_variable) or "").strip()
            if not key:
                try:
                    key = (store or CredentialStore()).get(chosen)
                except CredentialError:
                    pass  # Startup can still offer session-only keys when the vault is locked.
        return cls(api_key=key, provider=chosen, model=model or env_model or saved_model)
