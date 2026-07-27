# Test notes

## Isolation method

All tests invoke the CLI as a subprocess (`python -m src.logsum`) so the test suite
exercises the public interface defined in spec.md without importing implementation
internals. Fixtures live in `data/fixtures/` and are read-only; each test writes
output to pytest's `tmp_path`.

## PYTHONPATH failure and fix

Two tests (`test_default_input_filename_used_when_no_flag`,
`test_default_output_filename_used_when_no_flag`) change the subprocess `cwd` to
`tmp_path` to verify that the CLI resolves default filenames relative to the working
directory. When `cwd` is changed, `src` is no longer on the Python module search path,
so `python -m src.logsum` raises `ModuleNotFoundError` before the CLI runs at all.

**Decision: test bug, not implementation or spec issue.**  
The fix is to inject `PYTHONPATH=<project_root>` into the subprocess environment via
`_cwd_env()` so the module is importable regardless of `cwd`. The implementation and
the spec default-path behaviour are untouched.
