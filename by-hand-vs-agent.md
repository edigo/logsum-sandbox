# by-hand-vs-agent.md

## Where the agent saved time

**Delta 1 — `check=False` on subprocess calls (2 fix commits vs. 0)**  
By hand: `subprocess.run(...)` was written without `check=False` in four places. When
`test_exit_one_on_missing_input_file` and `test_exit_two_on_unwritable_output` ran, pytest
raised `CalledProcessError` instead of returning a result, so both tests exploded. It took
two fix commits (`18855f5`, `17da79d`) across two CI cycles to track down all four call
sites. Agent: wrote `check=False` on every call at initial authorship — never triggered.

**Delta 2 — `open()` structure and ruff SIM115 (35-line restructure vs. 0)**  
By hand: the initial `summarise()` wrote `f_in = open(input_path, ...)` inside a `try`,
then used `with f_in:` *after* the `except OSError` block. Ruff SIM115 ("Use a context
manager for opening files") flagged it. Fix commit `2b482dd` was a 35-deletion / 39-addition
restructure that rewrote the whole function body to put the `with open(...)` inside the
`try`. Agent: wrote `with open(input_path, ...) as fh:` inside `try` from the start.
Zero restructure, zero CI cycle.

**Delta 3 — `ruff format --check` in CI (gap never closed vs. present from day one)**  
By hand: `ci.yml` only runs `ruff check .` + `pytest -v`. CLAUDE.md says both `ruff check`
*and* `ruff format` are required. The gap was never noticed and is still absent from the
`ci-cd` branch. Agent: added `ruff format --check .` as a separate step when writing the
workflow, which immediately surfaced that `tests/test_logsum.py` needed reformatting (missing
blank lines between module-level defs, implicit string concat style). Fixed before committing.

---

## Where the agent went wrong or came up shorter

**Delta 4 — PLR1730 (if-comparisons written, then immediately discarded)**  
The first draft of `_read_groups` used:
```python
if ts < groups[key]["first"]:
    groups[key]["first"] = ts
```
Ruff PLR1730 ("replace `if` statement with `min` call") caught this during the pre-commit
lint check. Fixed to `groups[key]["first"] = min(groups[key]["first"], ts)` before the
commit landed. By hand: the same fix appeared in `18855f5` — both made the same mistake,
agent just caught it a step earlier. Not a win; a draw at best.

**Delta 5 — Test file required a separate `ruff format` pass**  
`tests/test_logsum.py` was written in one shot and then linted — but `ruff format --check`
failed (blank-line rules between top-level definitions, multi-line string concat collapsing).
A manual `ruff format tests/test_logsum.py` was needed before the CI commit. The right
discipline would have been to pipe through `ruff format` immediately after writing, not as
a separate verification step two commits later.

**Delta 6 — Plan stated "28 tests"; actual count was 32**  
The explore agent read `refactor-notes.md`, which recorded "all 28 tests pass" — written
*before* the four `--min-count` tests were added. The plan description carried the stale
count forward. Not a code defect (32 tests ran and passed), but the plan was wrong on a
verifiable fact. Should have counted test functions in the file directly rather than
trusting a note.

---

## Where the agent did better

**Commit history is clean (5 deliberate commits vs. 3 "fix" commits)**  
`ci-cd` log: `add CI workflow` → `fix` → `fix` → `fix` → `add --min-count flag`. The fix
commits are opaque; the diffs require reconstruction to understand what each one addressed.
`replay/logsum` log: every commit has a purpose — implementation, tests, CI, refactor, note.
Each diff is readable standalone.

**Unused import never introduced**  
`ci-cd`'s initial `test_logsum.py` imported `pytest` (unused; ruff F401). It was caught and
removed in `18855f5`. The agent never imported `pytest` — the test file uses only `csv`,
`os`, `subprocess`, `sys`, and `pathlib`, all of which are exercised.

**`ruff format --check` is now a first-class CI gate**  
See Delta 3 above. The agent closed a gap that the original developer left open. Whether
intentional or not, `ci-cd` would silently accept unformatted code in perpetuity. `replay`
will not.

---

## Supervised vs. async lesson

The replay was supervised: each step produced output, ruff ran locally, tests ran locally,
then a commit was made. That loop is cheap — PLR1730 and the format gap were both caught
before any CI cycle started.

The `ci-cd` branch ran async: write a batch of code, commit, push, wait for CI. Each
iteration cost a full CI cycle (~10–11 s, but also context-switching out and back). The
`check=False` and SIM115 bugs each required a push-wait-fix-push cycle. At three fix
commits that is at least two unnecessary round trips to remote CI.

The sharper lesson: async works fine when the agent has a local gate (ruff, pytest) it
actually uses *before* committing. The `ci-cd` development skipped the local gate; the
replay ran it explicitly between every step. The CI feedback loop is not a substitute for
a local lint-and-test pass — it is the backstop for things that slip through.

---

## What you'd do differently

1. **Run `ruff check . && ruff format --check .` immediately after writing each file —
   not as a block at the end of a step.** Writing `tests/test_logsum.py` and then
   discovering formatting issues two commits later (when adding CI) broke the "one thing
   per commit" discipline. The formatter should be part of the write-file loop, not a
   separate verification loop.

2. **Verify countable facts from the code, not from notes.** The plan said "28 tests"
   because the explore agent read `refactor-notes.md`. Notes rot. A `grep -c "^def test_"`
   on the actual file would have returned 32. Before stating a number in a plan, derive it
   from source.

3. **Write the `ruff format` step into the CI template by default.** Both branches needed
   it; only one has it. It should be unremarkable boilerplate, not an upgrade the agent
   adds as a "gap closed" talking point.
