# Verification record

Verified locally on Windows, Python 3.13.2, October 30, 2026.

## Automated checks

- **62 tests pass**: board normalization, duplicate/blank rejection, full partition
  integrity, locks/rejected sets, safe image handling, service caching/costs,
  typed output via the real SDK, API error/refusal/incomplete responses, explicit
  reasoning/token settings, CLI output and desktop state/lifecycle. Provider tests
  cover Kimi/DeepSeek chat serialization, Ollama image transport, rejection of
  cloud-backed aliases before puzzle submission, malformed output, per-provider
  vault isolation, secret-free preferences, hidden CLI prompts and UI key handling.
- Ruff lint and format checks pass.
- Wheel and source distribution build successfully. Their contents were checked
  for required source and absence of `.env` / virtual environments.
- Installed the wheel in a fresh virtual environment. The CLI demo returned four
  groups and zero usage without Qt installed. Adding only PySide6 Essentials was
  sufficient to instantiate the desktop and reveal all four demo groups.
- Exercised the native Windows Credential Manager with a uniquely named dummy
  test entry: write/read succeeded and the entry was deleted afterward. No real
  API key was accessed. Automated tests use an isolated fake vault, temporary
  preferences/launch directory and cleared provider environment variables.

## Visual and interaction checks

- Rendered actual Qt widgets at 1320×900 and 1060×740, including empty workspace,
  word review, results and settings. Inspected saved screenshots in `docs/images`.
- Opened the real Windows app and clicked Reveal example groups, verifying the
  native window transitions to all four category cards and feedback controls.
- Image clipboard paste is exercised against the real QApplication clipboard in
  tests. It creates a preview without triggering API work.
- Background success/failure and close-during-request behavior are tested with
  actual QThreads. Only the external service operation is replaced.
- Automated Qt tests default to the offscreen platform, keeping them independent
  of native accessibility inspectors and desktop focus. Native UI verification is
  performed separately. A Windows COM diagnostic during a visible test run led
  to this isolation; the offscreen suite completes without that diagnostic.

## Independent review

A separate read-only review found no critical or important defects. Two minor
findings were reproduced with failing tests and fixed: pasted entries longer than
80 characters are rejected before QLineEdit can truncate them, and whitespace-only
category titles/explanations are rejected. Reviewer's lifecycle probe was added
as a permanent regression test.

Additional credential routing check: an unrelated `OPENAI_BASE_URL` environment
variable cannot redirect this app's API key; the service explicitly uses the
official OpenAI endpoint. The constructor-level check makes no network request.

A second independent review covered the provider/security extension. Two recovery
issues were reproduced with failing tests and fixed: preference-file failure now
clearly reports an already-completed credential change, and invalid environment
configuration opens a visible recovery UI with no credentials loaded. The reviewer
confirmed both fixes and reported no additional findings in those changes.

## What this does not establish

No provider API key was configured, so **no live paid image extraction or puzzle
solve was performed**. Ollama/model weights were not installed or downloaded;
local inference has not been benchmarked. Mock API tests establish request/response handling, not
model availability, account access, solving accuracy, latency or real charges.
The example is intentionally predefined and makes no accuracy claim.

GitHub CI is configured but has not been run remotely. Native macOS/Linux UI and
clipboard use have not been manually tested here. No bundled executable installer
has been built; desktop launch uses the documented Python environment.

## First live check

1. Configure your key as described in the README.
2. Open `examples/practice-grid.png`, click Read words and verify all 16 tiles.
3. Click Find connections in Budget mode; inspect the category explanations and
   reported usage. This intentionally uses the live API rather than demo mode.
4. Test a new real puzzle and verify suggestions in the game. Do not infer general
   accuracy from the easy example.

For a real comparison of models/modes, use a fixed set of permitted puzzles and
record extraction accuracy, exact four-group match rate, latency and token usage.
