# Providers, private keys and local models

Connections Studio supports **OpenAI, Kimi/Moonshot, DeepSeek and local Ollama**
in both the desktop app and terminal. You can switch providers without changing
the screenshot → review words → solve workflow. No model downloads or API calls
happen just by opening Settings.

## Keep keys out of the repository

The recommended persistent setup is the **operating system credential store**.
On Windows this is Credential Manager; on macOS, Keychain; on Linux, Secret
Service with an unlocked desktop keyring. The app explicitly selects these native
backends and never falls back to a plaintext key file.

1. Open **Settings**, select the provider and paste **that provider's** key.
2. Leave **Remember key** unchecked for this session only, or check it to save
   the key in the OS credential store.
3. Leave the model at its default initially, then click **Save**.
4. Read a screenshot or solve reviewed words. Saving settings itself is free.

Each provider has a separate credential under service **Connections Studio**
and account `openai`, `kimi` or `deepseek`. Switching provider never copies an
OpenAI key to another provider. The input is masked. Forgetting a saved key
requires **Forget this provider's saved key → Save**; Cancel leaves it unchanged.
Unchecked Remember does **not** delete a previously saved key. Provider switches
discard unsaved edits in the dialog.

Provider/model preferences are written to your user configuration directory
(on Windows, normally `%LOCALAPPDATA%\Connections Studio\preferences.json`).
No key is included in that file, puzzle exports or the Settings representation.
Separate `appearance.json` stores only the light/dark theme and sidebar visibility.
Screenshots, puzzles and results stay in memory unless you explicitly export.
The app has no telemetry, key-upload service or bundled credentials.

**This does not make a key inaccessible to everyone.** The app must read it to
authenticate. Malware, administrators, a compromised process, or someone with
access to your unlocked user account may retrieve it. OS storage protects the
saved credential; it cannot protect a compromised computer. Copying a key can
also leave it in Windows clipboard history or clipboard sync. Clear that entry
after setup if those features are enabled. Do not share real-key screenshots,
terminal transcripts, environment dumps or `.env` files.

Cloud authentication sends the selected key to its provider over HTTPS. The
service pins official endpoints and ignores `OPENAI_BASE_URL`, system proxy
environment variables and HTTP redirects. Local Ollama receives **no cloud key**
and is pinned to `http://127.0.0.1:11434`. There is no automatic cloud fallback.
This is a local personal-use application, not a multi-user credential broker.

## Connect OpenAI

1. Create/select a project in the [OpenAI platform](https://platform.openai.com/).
2. Check [API billing](https://platform.openai.com/settings/organization/billing/overview).
   Check API billing separately from your ChatGPT subscription.
3. Create a key on the [API keys page](https://platform.openai.com/api-keys), with
   permission to make Responses API calls.
4. In Settings choose **OpenAI**, paste the key, optionally remember it and Save.
5. Start with **`gpt-5.4-mini` / Budget**. Monitor the
   [usage dashboard](https://platform.openai.com/usage).

The default supports images and structured Responses output. Reference standard
rates checked October 30, 2026: $0.75 input, $0.075 cached input, $4.50 output per
million tokens. App estimates are not invoices or spending limits; failed
requests can still cost money. [Official model and pricing](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

## Run a free local model with Ollama

Local weights have **no per-request API charge**. You supply disk space, memory,
compute and electricity. The initial application/model downloads need internet;
inference can then run offline. Quality and speed depend on the model/hardware.
Small local models may struggle with subtle Connections wordplay, so review
their output and use cloud models when useful.

### Windows setup

1. Install [Ollama for Windows](https://ollama.com/download/windows).
   Use a current version; Qwen3-VL requires at least Ollama 0.12.7.
2. For an explicitly local-only installation, run this in PowerShell:

   ```powershell
   [Environment]::SetEnvironmentVariable("OLLAMA_NO_CLOUD", "1", "User")
   ```

   Quit Ollama from its tray icon, then reopen it so it picks up this setting.
   Keep its default loopback binding; do not expose port 11434 to your network.
   See [Ollama local/cloud controls](https://docs.ollama.com/faq).
3. Open a **new** terminal and download the model:

   ```powershell
   ollama pull qwen3-vl:4b
   ollama list
   ```

4. Open Connections Studio → **Settings → Ollama · local**.
   Keep model **`qwen3-vl:4b`** and click Save. No API key is needed.
5. Paste a screenshot, click Read words, correct the tiles, then Find connections.
   The first request can be slower while the model loads.

The 4B model is a sensible first trial on a 32 GB RAM laptop with an RTX 3070 Ti
Laptop GPU. This is a hardware-based starting recommendation, not a benchmark.
Model file sizes below exclude context memory, runtime overhead and application
storage. A model fitting in RAM does not guarantee full GPU acceleration.

| Model | Approximate download | Use |
| --- | ---: | --- |
| `qwen3-vl:2b` | 1.9 GB | Smaller/faster first experiment; weaker reasoning likely |
| `qwen3-vl:4b` | 3.3 GB | Recommended local starting point |
| `qwen3-vl:8b` | 6.2 GB | Optional quality comparison; needs more memory |

All three accept images. Install another with `ollama pull MODEL`, then change
the model in Settings or pass `--model MODEL`. To remove downloaded weights,
use `ollama rm MODEL`. [Official Qwen3-VL model library](https://ollama.com/library/qwen3-vl).

The app checks `/api/show` **before sending puzzle data**, rejects remote/cloud
model metadata and accepts local GGUF models only. Image reading additionally
requires a model reporting vision capability. A local text-only model can solve
manually entered words. Local mode requests JSON schema output with an 8,192-token
context and disables optional thinking; Deeper raises the output allowance.
The API cost display is zero, not a measurement of electricity costs. A local
request times out after 180 seconds; timeout does not guarantee that Ollama has
stopped computing. Start with a smaller model if it repeatedly times out.

**Extended mode** raises the solve allowance to 16,000 tokens and the request
timeout to 300 seconds for all providers. OpenAI still uses medium reasoning,
Kimi/DeepSeek use high; local optional thinking remains disabled. Ollama's context
increases to 20,096 tokens in this mode, which can require substantially more
memory. Ordinary modes retain the 8,192-token context. Prefer Budget locally first.

If you want cheaper cloud experiments, choose DeepSeek → `deepseek-flash` and
start with Budget. Current rates checked October 30, 2026 are $0.15–$0.30 per
million uncached input tokens and $0.60–$1.20 per million output tokens, depending
on off-peak/peak hours. This is cheaper per token than GPT-5.4 mini, but puzzle
accuracy has not been compared. See [official pricing](https://api-docs.deepseek.com/quick_start/pricing/).

macOS/Linux: install Ollama from its official site, apply its documented
`OLLAMA_NO_CLOUD` configuration for your service/launcher, and use the same pull
command. Connections Studio requires Ollama on the **same computer**, at its
default loopback port. [Windows installation details](https://docs.ollama.com/windows).

## Kimi and DeepSeek

| Provider | App default | Key | Billing |
| --- | --- | --- | --- |
| Kimi / Moonshot | `kimi-k3.1-pro` | [Kimi API platform](https://platform.kimi.ai/docs/get-your-api-key) | Hosted API is paid; check current account pricing |
| DeepSeek | `deepseek-flash` | [DeepSeek API platform](https://platform.deepseek.com/api_keys) | Hosted API is paid; check current account pricing |

Create an account/API key with the chosen provider, arrange API credits if
required, select that provider in Settings, paste its key and Save. Keys and
models are provider-specific. These integrations use their official
OpenAI-compatible Chat Completions endpoints, JSON mode and local schema/partition
validation. Their defaults currently support image input. Budget uses low Kimi
reasoning or disables DeepSeek thinking; Deeper uses high reasoning. See
[Kimi models](https://platform.kimi.ai/docs/models),
[DeepSeek API](https://api-docs.deepseek.com/) and
[DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/).

Free consumer chat access is **not** a free API entitlement. Trial credits or
free tiers can change; none are assumed by this app. Kimi K2.5's hosted API was
retired August 31, 2026, so it is not the default. Its open weights are a
one-trillion-parameter model; running the full model locally is not a practical
choice on an ordinary laptop. Open weights also do not make hosted inference
free. [Kimi K2.5 model repository](https://github.com/MoonshotAI/Kimi-K2.5).

Costs for Kimi/DeepSeek/custom models display as **unavailable**, not zero.
Check the provider's usage dashboard. Cloud inputs are subject to that provider's
data policies. OpenAI requests use `store=False`, which itself is not a
zero-retention guarantee. [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).

DeepSeek JSON mode can return a blank/space-only final answer even when its finish
status says stop. The app provides both schema and concrete examples as recommended
by [DeepSeek's JSON guide](https://api-docs.deepseek.com/guides/json_mode/).
Errors distinguish that case from malformed JSON and readable JSON that fails the
required answer format. A complete surrounding JSON code fence is safely removed;
missing fields, invented words or incorrect groups are still rejected. There is
no automatic paid formatting retry. Error messages omit raw responses, which are
not logged by the app.

## Terminal setup and use

Install the project as described in the README. These examples assume an
activated environment; on Windows use `.venv\Scripts\connections` otherwise.

```sh
# Secure hidden prompt; the key is never a command-line argument
connections auth set --provider openai
connections auth set --provider kimi
connections auth set --provider deepseek

# Checks only OS storage, never prints the key
connections auth status --provider openai
connections auth forget --provider openai

# Choose a provider explicitly, independent of desktop preferences
connections solve --clipboard --provider openai
connections solve --image "grid.png" --provider kimi
connections extract --image "grid.png" --provider deepseek

# Local inference, including screenshot reading, no cloud credentials
connections solve --clipboard --provider ollama
connections solve --image "grid.png" --provider ollama --model qwen3-vl:8b
```

The hidden prompt requires an interactive terminal and refuses an echoing
fallback. Do not pipe a key into it. Use the desktop Settings if your IDE cannot
provide a secure prompt. The CLI does not require Qt unless you launch `gui`.

For advanced automation, environment variables remain supported:
`OPENAI_API_KEY`, `MOONSHOT_API_KEY`, `DEEPSEEK_API_KEY`, `CONNECTIONS_PROVIDER`
and `CONNECTIONS_MODEL`. Process environment overrides the launch directory's
`.env`; a nonempty provider key there overrides the OS credential store.
Explicit CLI provider/model flags override selection; otherwise environment
selection overrides saved preferences. A provider override does not inherit a
different provider's environment model. With no selection, OpenAI is the default.

`.env` is **optional plaintext**, Git-ignored but not encrypted. The app never
creates it. Prefer the OS store for everyday use; if you choose a `.env`, copy
`.env.example` and edit it locally. Never commit it, include it in an archive,
or paste its contents into a report. Forgetting an OS-stored key does not remove
environment variables or `.env` entries. Revoke a leaked key at its provider;
deleting it from a new Git commit does not remove it from Git history.

## Scope of verification

Automated tests cover routing, credential isolation, redacted errors, JSON
validation and local/cloud separation with simulated provider responses. No real
paid keys were used and no local model was downloaded as part of development.
Availability, model accuracy and local speed still need your first real puzzle
check. See [verification](verification.md).
