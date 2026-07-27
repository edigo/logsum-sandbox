# Provenance note — --min-count feature

## Model

claude-sonnet-4-6

## Context loaded

- `src/logsum.py` — full file read before edit
- `spec.md` — full file read before edit
- `tests/test_logsum.py` — full file read before edit
- `data/fixtures/` — structure described by Explore agent (6 fixture files)
- `data/sample_events.csv` + `data/summary.csv` — described by Explore agent
- `CLAUDE.md` — loaded as project instructions

## Files changed

| File | Change |
|---|---|
| `src/logsum.py` | `summarise()` gains `min_count=None`; `main()` adds `--min-count` arg |
| `spec.md` | `--min-count` row added to CLI flags table; "Date-range filtering" bullet extended to "…or per-row filtering" |
| `tests/test_logsum.py` | 4 new tests added under `§9 — --min-count flag` |

## Plan deviations

- Plan said to remove `filtering` from the Out-of-scope list and replace it with "per-row filtering / deduplication". The original bullet was already `Date-range filtering` (not a bare `filtering` entry), so instead the existing line was extended to `Date-range filtering or per-row filtering`. The intent (narrowing the exclusion to make room for the new flag) is preserved; the wording differs.

## Untested items

- `--min-count 0` — argparse accepts it (no lower-bound validation); behaviour (keeps all groups, since count ≥ 0 always) is correct but unverified by a test.
- Negative N — same gap; `--min-count -1` would keep everything silently.
- Interaction with malformed-timestamp rows — count used for filtering is the post-skip valid count, which is the correct behaviour, but no test exercises `--min-count` against `malformed_ts.csv` directly.
- `summarise()` API — the new `min_count` parameter is only exercised via CLI subprocess tests; no direct unit call to `summarise()` with `min_count` set.
