# Connections Studio Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a polished clipboard-first desktop solver and matching CLI.

**Architecture:** Shared validated puzzle models and OpenAI service, independent
image preparation, CLI entry point and PySide6 views. API work runs off the GUI
thread. All state remains local and in memory except explicit user exports.

**Tech Stack:** Python 3.11+, PySide6, Pillow, OpenAI SDK, Pydantic, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-10-30-connections-studio-design.md`

## Global constraints
- Default gpt-5.4-mini; no automatic paid retries; explicit extract and solve.
- Exactly 16 unique words, four groups of four, every input used once.
- Keys never committed or logged; demo never calls the network.
- Preserve old project; create new code in the empty current workspace.

## Review focus
- Malformed model output must never become a valid-looking partial solution.
- Old results/constraints must be cleared when words or screenshots change.
- Clipboard image must take precedence over text and must not be silently sent.
- API refusal, incomplete output, network/auth failures must unlock the UI.
- Close while a request runs must not destroy a running QThread.

### Task 1: Validated core and packaging
Files: `pyproject.toml`, `src/connections/{models,config,images,demo}.py`, tests.
Interfaces: `normalize_words`, `SolveRequest`, `Solution.validate_for`,
`prepare_image(bytes)->PreparedImage`, `Settings`, offline `demo_solution`.
- [x] Write tests rejecting blanks, duplicates, wrong partitions, conflicting locks,
      rejected groups, invalid/oversized images, and preserving multiword entries.
- [x] Run pytest to verify missing behavior; implement and rerun to green.

### Task 2: OpenAI adapter and CLI
Files: `service.py`, `cli.py`, `__main__.py`, service/CLI tests.
Interfaces: `SolverService.extract(image)`, `solve(request)`, `OperationResult`
with usage/cost and cached flag; CLI `main(argv)->int`.
- [x] Write boundary tests using the real SDK with HTTP mock transport: valid
      structured output, invalid coverage, refusal, incomplete, auth/quota errors,
      successful cache, mode caps and privacy flags. CLI demo and bad input tests.
- [x] Implement, verify focused tests then full suite; no live billable test.

### Task 3: Desktop
Files: `gui/{app,window,widgets,theme,worker}.py`, desktop tests.
Interfaces: `MainWindow(service=None)`, `load_demo`, `set_image`, `start_solve`.
- [x] Test edits invalidate results, paste does not invoke API, demo displays four
      categories, locks and rejects persist only for the current word set.
- [x] Implement sidebar, capture surface, word grid, result cards, settings,
      feedback, copy/export, shortcuts, background calls and safe lifecycle.
- [x] Run tests and render empty/review/results/settings at supported sizes.

### Task 4: Release
Files: README, LICENSE, CONTRIBUTING, architecture docs, `.github/workflows`,
`.env.example`, `launch.cmd`, `docs/images`.
- [x] Write exact install/API/usage and terminal clipboard instructions, costs,
      limitations, privacy and publishing checklist. Create offline sample image.
- [x] Run full tests, lint, build wheel and verify installed CLI/assets.
- [x] Request independent code review, address material findings, rerun checks.
- [x] Record test evidence and outstanding live API verification limitation.
