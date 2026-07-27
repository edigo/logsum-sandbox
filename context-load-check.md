# Context Load Check

Source file: `CLAUDE.md`

## Project context
Tiny CLI that summarises synthetic `events.csv` logs. Input is always synthetic data; no real PII or production logs.

## Utilities to prefer
- Python 3.11 stdlib only; no third-party runtime deps.
- Linting via `ruff check` and `ruff format`.
- Tests via `pytest`; test files mirror `src/` names (`test_<module>.py`).

## Conventions
- Code in `src/`, tests in `tests/`, synthetic data fixtures in `data/`.

## Escalation gates
- Stop before adding dependencies — ask first.
- Synthetic data only — never use real event data.
- `spec.md` is frozen after sign-off — do not overwrite without explicit approval.
