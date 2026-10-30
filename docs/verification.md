# Verification record

Verified locally on Windows, Python 3.13.2, October 31, 2026.

## Automated checks

- **117 tests pass**: board normalization, duplicate/blank rejection, full partition
  integrity, locks/rejected sets, safe image handling, service caching/costs,
  typed output via the real SDK, API error/refusal/incomplete responses, explicit
  reasoning/token settings, CLI output and desktop state/lifecycle. Provider tests
  cover Kimi/DeepSeek chat serialization, Ollama image transport, rejection of
  cloud-backed aliases before puzzle submission, malformed output, per-provider
  vault isolation, secret-free preferences, hidden CLI prompts and UI key handling.
  Rethink regressions cover remaining-only requests and exact group count, local
  confirmation merging, rejected-output refusal, selection resets, stale-card and
  export protection on failure, and neutral feedback after success.
  Individual submitted confirmations remain undoable, and replaced cards are
  hidden immediately to prevent overlap during deferred Qt widget deletion.
  Extended mode is tested through the real SDK's mocked HTTP boundary for OpenAI,
  Kimi and DeepSeek, and the local Ollama boundary: 16,000 tokens, longer request
  timeout, compatible reasoning and sufficient local context. Incomplete content-
  filtered/unknown responses never receive token-exhaustion advice. UI tests
  verify explicit selection and the increased-cost notice.
  History regressions verify previous groups in the outgoing payload, refusal of
  renamed/reordered previous partitions, allowance for partial group reuse when
  others change, retention of failed candidates, history reset, cross-board
  rejection and no network request for an impossible final-four rearrangement.
  JSON-mode regressions cover blank/malformed/schema-invalid responses with usage
  preserved and no retries, whole code-fence unwrapping without bypassing puzzle
  validation, examples valid for extraction/full/remaining schemas, and refusal
  to search surrounding prose for embedded JSON.
  Final-eight search tests cover all 35 unique complete partitions, exclusion of
  rejections/history, empty candidate pools, invalid selection IDs, exact-count
  category selection via all four provider boundaries, and no paid request when
  no options remain. These checks establish membership handling, not category
  quality or the accuracy of a live model's ranking.
  Long-tile regression verifies options reference word indexes rather than
  repeating full tile text in every candidate, bounding the local prompt size.
  Desktop regressions cover collapsible navigation, explicit screenshot-read
  popup, centered loading and failure recovery, Extended desktop default, theme
  persistence independent of provider settings, safe appearance defaults and
  completed-puzzle reset directly from the results action.
  Cancellation regressions cover immediate return to controls, ignored late
  results, overlapping old/new completion, window close after stopping and the
  completed-before-queued-signal cleanup race. Random fallback tests cover complete
  word usage, preserved locks, exclusions/history, exhausted final-four constraints,
  clear random-origin labeling and no invented words after extraction failure.
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
- Inspected light/dark workspace, result cards and Settings, collapsed navigation,
  all-confirmed New puzzle action, and both centered popup designs. The rendering
  script uses dummy credentials and offline demo data; it makes no API calls.
- Opened the real Windows app and clicked Reveal example groups, verifying the
  native window transitions to all four category cards and feedback controls.
- Image clipboard paste is exercised against the real QApplication clipboard in
  tests. It creates a preview without triggering API work.
- Background success/failure, cancellation and close-during-request behavior are
  tested with actual daemon request threads and queued Qt signals. Only the
  external service operation is replaced.
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

GitHub Actions passed all four Windows/Linux and Python 3.11/3.13 jobs on the
[first public revision](https://github.com/vkmest/connections-studio/actions/runs/41146397592).
Native macOS/Linux UI and
clipboard use have not been manually tested here. No bundled executable installer
has been built; desktop launch uses the documented Python environment.

## Public release checks

On October 31, 2026, Gitleaks 8.30.1 reported no credential detections in the
published Git history or tracked release files. A fresh public clone was checked
for excluded `.env`/environment folders and noreply-only commit identities. The
wheel and source archive were checked for private files; the source package uses
an explicit public-file allowlist. Documentation images use offline demo data and
empty key fields. Scanning is evidence of these checks, not a guarantee that every
possible secret format could be detected. OS credential stores were not read.

## First live check

1. Configure your key as described in the README.
2. Open `examples/practice-grid.png`, click Read words and verify all 16 tiles.
3. Click Find connections in Budget mode; inspect the category explanations and
   reported usage. This intentionally uses the live API rather than demo mode.
4. Test a new real puzzle and verify suggestions in the game. Do not infer general
   accuracy from the easy example.

For a real comparison of models/modes, use a fixed set of permitted puzzles and
record extraction accuracy, exact four-group match rate, latency and token usage.
