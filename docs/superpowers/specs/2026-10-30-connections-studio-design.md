# Connections Studio design

## Intent
Replace the original single-file Tkinter/Tesseract prototype with a polished,
readable Python app for pasting a Connections screenshot, reviewing its words,
and finding four likely categories. The user requested planning and full
implementation together; implementation choices below are agent decisions.

## Approach
- Native PySide6 desktop app (selected): reliable image clipboard access, no
  browser server, a shared Python core for the terminal, and custom visual design.
- Local web app: flexible styling but adds a server and browser permissions.
- Retain Tkinter/Tesseract: fewer changes, but OCR installation and styling are
  the weaknesses of the original project.

## Product
Warm paper background, ink typography, violet primary actions, four muted
category colors, spacious cards, an editable 4x4 grid, and a persistent workflow
sidebar. Three steps: capture, review, connect. Use system fonts, vector art and
local styling; no remote UI assets. Minimum 1060x740 with scrollable content.

Paste with Ctrl+V (Cmd+V on macOS), open a local image, or enter text. Screenshot
preview precedes the explicit paid extraction action. Review all 16 words before
solving. Results include category, four words, a short explanation, and qualitative
model confidence, explicitly not a calibrated probability. Lock confirmed groups,
reject exact incorrect sets, and solve remaining words. No false claims that AI
suggestions match the publisher's answer. Demo mode works entirely offline.

## Core and API
Python >=3.11, Pydantic validation, OpenAI Responses structured outputs, Pillow
image preprocessing, PySide6 optional desktop extra. GPT-5.4 mini default;
budget reasoning low / 3500 output tokens, deeper medium / 6500 tokens,
image extraction none / 1200 tokens. No hidden retries or automatic escalation.
Validate 16 nonempty unique normalized words and exact 4x4 partition. Validate
locks and rejects before API calls. Cache successful identical requests in memory.
Bound image file size and pixel count, normalize orientation, downsize to 1600px,
strip metadata via re-encoding. Errors must preserve edits and permit recovery.
Threaded API work keeps UI responsive; suppress duplicate work and unsafe close.

API key from environment/.env or a masked session-only settings field, never
embedded in source or logs. Do not migrate the old config.py. No external API
call during tests. Store=False; OpenAI service retention policies still apply.

## Terminal
`connections` opens desktop; `connections gui --demo`; `connections solve
--image path`, `--clipboard`, `--words ...`, `--words-file path`, `--demo`,
`--json`, `--mode budget|deeper`. `extract` can export words for correction before
a text-only solve. Clear exit codes, errors on stderr, JSON only on stdout.

## Release and verification
README with Windows-first setup and macOS/Linux notes; .env.example, MIT license,
contributor guide, architecture, model pricing assumptions, GitHub Actions tests,
package installation, screenshots, and a Windows launcher. Test word validation,
partition integrity, constraints, image safety, API boundaries/errors/cache/usage,
CLI and desktop state transitions using mocks only at external boundaries.
Visually inspect real rendered desktop screenshots. Live accuracy requires a
working API key and separately recorded evaluation; don't invent benchmark claims.

## Non-goals
No game website automation, scraping, account login, public backend, bundled key,
guaranteed solve accuracy, or installer/signing infrastructure. Publishing to
GitHub remains the user's action; prepare the local repository for it.
