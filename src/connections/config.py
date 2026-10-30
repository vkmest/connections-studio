"""Explicit configuration; importing this module never reads a key."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_MODEL = "gpt-5.4-mini"
# Standard USD rates per million tokens, checked 2026-10-30. Not a billing guarantee.
MODEL_RATES = {DEFAULT_MODEL: (0.75, 0.075, 4.50)}


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    model: str = DEFAULT_MODEL

    @classmethod
    def from_environment(cls) -> "Settings":
        # Only the launch directory's .env is considered, never arbitrary parent files.
        load_dotenv(Path.cwd() / ".env", override=False)
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            model=os.getenv("CONNECTIONS_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        )
