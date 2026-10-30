"""Audited destinations. A model choice cannot change where a key is sent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    default_model: str
    key_variable: str
    setup_url: str


PROVIDERS = {
    "openai": Provider(
        "OpenAI",
        "https://api.openai.com/v1",
        "gpt-5.4-mini",
        "OPENAI_API_KEY",
        "https://platform.openai.com/api-keys",
    ),
    "kimi": Provider(
        "Kimi / Moonshot",
        "https://api.moonshot.ai/v1",
        "kimi-k3.1-pro",
        "MOONSHOT_API_KEY",
        "https://platform.kimi.ai/docs/get-your-api-key",
    ),
    "deepseek": Provider(
        "DeepSeek",
        "https://api.deepseek.com",
        "deepseek-flash",
        "DEEPSEEK_API_KEY",
        "https://platform.deepseek.com/api_keys",
    ),
    "ollama": Provider(
        "Ollama · local",
        "http://127.0.0.1:11434",
        "qwen3-vl:4b",
        "",
        "https://ollama.com/download/windows",
    ),
}
