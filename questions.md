# Repo Q&A

## Files read
- `src/logsum.py`
- `.github/workflows/ci.yml`

---

## Where is the grouping rule?

Groups are keyed by `(level, service)` — a 2-tuple of the normalised log level and service name.
The key is constructed at `src/logsum.py:48`:

```python
key = (level, service)
```

Each group accumulates a count and tracks the earliest (`first`) and latest (`last`) timestamp
(`src/logsum.py:49-52`). After all rows are read, `summarise()` optionally filters groups by
`--min-count` (`src/logsum.py:77-78`) before writing output.

---

## How is missing level handled?

Two things happen, in order:

1. **Warning printed to stderr** — if the raw `level` cell is blank, a warning is emitted before
   any normalisation (`src/logsum.py:38-39`):
   ```
   WARNING: line N: blank level, using UNKNOWN
   ```

2. **Normalised to `"UNKNOWN"`** — `_normalise_level()` returns `'UNKNOWN'` when the stripped
   value is empty (`src/logsum.py:19-21`). The row is **not** skipped; it is grouped under
   `(UNKNOWN, <service>)`.

By contrast, a malformed timestamp causes the row to be **skipped entirely**
(`src/logsum.py:44-46`), so missing level and bad timestamp are treated differently.

---

## How do I run tests and CI locally?

**Tests:**
```bash
pytest -v
```

**Linting (matches CI):**
```bash
ruff check .
ruff format .   # auto-fix formatting
```

Install both tools first if needed:
```bash
pip install ruff pytest
```

This mirrors exactly what CI does (`.github/workflows/ci.yml:17-21`): install `ruff` and
`pytest`, run `ruff check .`, then `pytest -v`.

---

## What could not be verified

- Whether a `pyproject.toml` or `setup.cfg` configures ruff rules — no such file was found in
  the repo, so ruff runs with its defaults.
- The `tests/test_logsum.py` file was not read; test coverage claims are not made here.
