"""OS-native credential storage. Never fall back to plaintext files."""

import sys

from connections.providers import PROVIDERS

SERVICE_NAME = "Connections Studio"


class CredentialError(Exception):
    pass


def native_backend():
    # Explicit selection ignores user-installed plaintext keyring plugins/configuration.
    if sys.platform == "win32":
        from keyring.backends.Windows import WinVaultKeyring

        return WinVaultKeyring()
    if sys.platform == "darwin":
        from keyring.backends.macOS import Keyring

        return Keyring()
    from keyring.backends.SecretService import Keyring

    return Keyring()


class CredentialStore:
    def __init__(self, backend=None):
        self._backend = backend

    def _access(self, provider: str, action: str, key: str = ""):
        if provider not in PROVIDERS or provider == "ollama":
            raise CredentialError("Choose a cloud provider to manage its API key.")
        try:
            backend = self._backend if self._backend is not None else native_backend()
            if action == "get":
                return backend.get_password(SERVICE_NAME, provider) or ""
            if action == "save":
                if not key.strip():
                    raise CredentialError("Enter an API key before saving it.")
                backend.set_password(SERVICE_NAME, provider, key.strip())
            elif backend.get_password(SERVICE_NAME, provider) is not None:
                backend.delete_password(SERVICE_NAME, provider)
        except CredentialError:
            raise
        except Exception:
            raise CredentialError(
                "The OS credential store is unavailable or locked. "
                "Use a session-only key, or unlock your OS keychain. Nothing was saved to a file."
            ) from None

    def get(self, provider: str) -> str:
        return self._access(provider, "get")

    def save(self, provider: str, key: str) -> None:
        self._access(provider, "save", key)

    def forget(self, provider: str) -> None:
        self._access(provider, "forget")
