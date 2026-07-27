# logsum-sandbox

## Project context
Tiny CLI that summarises synthetic `events.csv` logs. Input is always synthetic data; no real PII or production logs.

## Utilities to prefer
- Python 3.11 standard library only; no third-party runtime deps.
- Linting: `ruff check` and `ruff format`.
- Tests: `pytest`; keep test files mirroring `src/` names (`test_<module>.py`).

## Conventions
- Code in `src/`, tests in `tests/`, synthetic data fixtures in `data/`.

## Escalation gates
- **Stop before adding dependencies** — ask first; stdlib must stay sufficient.
- **Synthetic data only** — never use or reference real event data.
- **spec.md is frozen after sign-off** — do not overwrite it without explicit user approval.
