# Security and credentials

Connections Studio is a local, personal-use desktop/CLI app. Each person must use
their own cloud API credentials, or choose local Ollama without a cloud key.
No hosted backend, shared key or browser-exposed credential is provided.

## Store keys locally

- Prefer **Settings → Remember key** or `connections auth set --provider openai`
  (substitute `kimi` or `deepseek`). The app explicitly uses the native OS store:
  Windows Credential Manager, macOS Keychain or Linux Secret Service.
- Unchecked Remember keeps the supplied key in memory for the session. Existing
  remembered keys remain until explicitly forgotten.
- Provider keys are separate. Local Ollama receives no cloud key. Provider URLs
  are pinned; redirects and environment proxy/base-URL overrides are disabled.
- `.env` is optional plaintext configuration. It is ignored by Git, not encrypted.
  `.env.example` contains empty key fields only.
- Provider/model preferences and appearance preferences contain no API key.
  Screenshots/results stay in memory unless explicitly exported.

OS storage cannot protect an unlocked account from malware or an administrator.
Cloud providers receive the input you explicitly submit and have their own data
policies. Stop waiting does not guarantee server-side cancellation or stop billing.

## Before sharing

Never attach `.env`, credential-store exports, environment dumps, private keys,
raw API traces or screenshots showing credentials to commits or issues. Documentation
screenshots use the original offline demo and empty key fields. Crop personal game
screenshots before sharing. An ignored file can still be force-added to Git, so
review staged files and scan history before pushing.
Git commit metadata can also expose an email address. Use your GitHub noreply
identity for public commits and review metadata before publishing additional branches.

If a key leaks, revoke it with its provider and create a replacement. Removing it
from the latest commit alone does not remove it from Git history or invalidate it.

## Report a vulnerability

Use GitHub's **Security → Report a vulnerability** if private reporting is available.
Otherwise open an issue containing only a high-level, non-sensitive description
and request a private reporting channel. Do not post secrets or exploit material
that would expose someone's credentials in a public issue.

For setup details, see [providers and keys](docs/providers-and-keys.md).
