# CI Notes — branch `ci-cd`

## Run result (2026-07-27)

All checks passed — 2 successful checks, no conflicts with base branch.

| Job | Trigger | Duration | Result |
|-----|---------|----------|--------|
| CI / test | pull_request | 11 s | success |
| CI / test | push | 10 s | success |

Merge can be performed automatically.

## Changes on this branch

- `tests/test_logsum.py` — added `check=False` to all four `subprocess.run()` calls.
- `src/logsum.py` — moved both `open()` calls inside `with` context managers; wrapped each `with open(...)` block in `try/except OSError` so the error handler still fires on open failures (ruff `SIM115` fix).
