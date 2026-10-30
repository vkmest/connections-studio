# Contributing

Use Python 3.11 or newer. Create a virtual environment, then install:

```sh
python -m pip install -e ".[desktop,dev]"
python -m pytest -q
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
```

On Windows, use `.venv\Scripts\python` if the environment isn't activated.
For headless Linux tests, set `QT_QPA_PLATFORM=offscreen`.

Tests never require an API key. API boundary tests use the real OpenAI SDK
with an HTTP mock transport, covering serialization and parsing without charges.
Desktop tests use actual Qt widgets. Keep mocks at external boundaries and add
a regression test for meaningful bugs.

Before a PR, run the checks above, then `python -m build`. Inspect the UI at
1320×900 and 1060×740. `python scripts/render_previews.py` renders actual widgets
into `docs/images` and regenerates the original practice puzzle.

Keep invariants in `models.py`, networking in `service.py`, and UI state in
`gui/window.py`. Never commit credentials, personal screenshots, `.env`, raw API
logs or `.venv`. Comments should explain constraints or non-obvious choices.

For accuracy changes, evaluate on a fixed collection of puzzles you have rights
to use. Report exact-partition success, OCR accuracy, token cost and latency.
An HTTP success or the offline demo is not evidence of solving quality.

See [architecture](docs/architecture.md) and [verification](docs/verification.md).
