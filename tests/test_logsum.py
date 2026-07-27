"""Tests derived exclusively from spec.md. Do not import implementation details."""

import csv
import subprocess
import sys
from pathlib import Path

import pytest

import os

FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"
PROJECT_ROOT = Path(__file__).parent.parent
LOGSUM = [sys.executable, "-m", "src.logsum"]

def _cwd_env(cwd: Path) -> dict:
    """Env with PROJECT_ROOT on PYTHONPATH so src.logsum is importable from any cwd."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(PROJECT_ROOT) + (";" + existing if existing else "")
    return env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_logsum(input_path: Path, output_path: Path, extra_args=None):
    cmd = LOGSUM + ["--input", str(input_path), "--output", str(output_path)]
    if extra_args:
        cmd += extra_args
    return subprocess.run(cmd, capture_output=True, text=True)


def read_summary(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# §5 — Output columns
# ---------------------------------------------------------------------------

def test_output_columns(tmp_path):
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "happy_path.csv", out)
    with out.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == ["level", "service", "count", "first_seen", "last_seen"]


# ---------------------------------------------------------------------------
# §2 & §3 — Grouping and normalisation
# ---------------------------------------------------------------------------

def test_grouping_by_normalised_level_and_service(tmp_path):
    """'info', 'INFO' and ' auth ', 'Auth' must collapse into one group each."""
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "happy_path.csv", out)
    assert result.returncode == 0

    rows = read_summary(out)
    keys = {(r["level"], r["service"]) for r in rows}
    # 'info' and 'INFO' normalise to INFO; 'auth'/'Auth'/' auth ' normalise to auth
    assert ("INFO", "auth") in keys
    assert ("ERROR", "auth") in keys
    # No un-normalised variants should appear
    assert ("info", "auth") not in keys
    assert ("INFO", "Auth") not in keys


def test_level_normalised_to_uppercase(tmp_path):
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "happy_path.csv", out)
    rows = read_summary(out)
    for row in rows:
        assert row["level"] == row["level"].upper()


def test_service_normalised_to_lowercase(tmp_path):
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "happy_path.csv", out)
    rows = read_summary(out)
    for row in rows:
        assert row["service"] == row["service"].lower()


def test_level_whitespace_stripped(tmp_path):
    """Levels with surrounding spaces must still normalise correctly."""
    csv_content = (
        "timestamp,level,service,message\n"
        "2024-01-15T08:00:00Z, INFO ,svc,msg\n"
    )
    inp = tmp_path / "ws_level.csv"
    inp.write_text(csv_content, encoding="utf-8")
    out = tmp_path / "summary.csv"
    run_logsum(inp, out)
    rows = read_summary(out)
    assert len(rows) == 1
    assert rows[0]["level"] == "INFO"


def test_service_whitespace_stripped(tmp_path):
    csv_content = (
        "timestamp,level,service,message\n"
        "2024-01-15T08:00:00Z,INFO, MyService ,msg\n"
    )
    inp = tmp_path / "ws_svc.csv"
    inp.write_text(csv_content, encoding="utf-8")
    out = tmp_path / "summary.csv"
    run_logsum(inp, out)
    rows = read_summary(out)
    assert rows[0]["service"] == "myservice"


# ---------------------------------------------------------------------------
# §3 & §4 — UTC normalisation and first_seen / last_seen ordering
# ---------------------------------------------------------------------------

def test_timestamps_written_in_utc_z_format(tmp_path):
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "happy_path.csv", out)
    rows = read_summary(out)
    for row in rows:
        assert row["first_seen"].endswith("Z"), row["first_seen"]
        assert row["last_seen"].endswith("Z"), row["last_seen"]
        assert "+" not in row["first_seen"]
        assert "+" not in row["last_seen"]


def test_no_microseconds_in_output(tmp_path):
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "happy_path.csv", out)
    rows = read_summary(out)
    for row in rows:
        assert "." not in row["first_seen"]
        assert "." not in row["last_seen"]


def test_utc_offset_normalisation_first_last_order(tmp_path):
    """
    spec §3 implementation note: +02:00 offset makes a nominally 'later'
    wall-clock time actually *earlier* in UTC.

    utc_offset.csv:
      row1: 09:30+02:00  → 07:30Z
      row2: 08:00Z       → 08:00Z

    first_seen must be 07:30Z (the offset row), last_seen must be 08:00Z.
    """
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "utc_offset.csv", out)
    assert result.returncode == 0

    rows = read_summary(out)
    assert len(rows) == 1
    row = rows[0]
    assert row["first_seen"] == "2024-01-15T07:30:00Z"
    assert row["last_seen"] == "2024-01-15T08:00:00Z"


def test_same_instant_different_offset_produces_same_string(tmp_path):
    """Two events at identical UTC instants but different offset notation → same output string."""
    csv_content = (
        "timestamp,level,service,message\n"
        "2024-01-15T10:00:00+02:00,INFO,svc,a\n"
        "2024-01-15T08:00:00Z,INFO,svc,b\n"
    )
    inp = tmp_path / "same_instant.csv"
    inp.write_text(csv_content, encoding="utf-8")
    out = tmp_path / "summary.csv"
    run_logsum(inp, out)
    rows = read_summary(out)
    assert len(rows) == 1
    assert rows[0]["first_seen"] == rows[0]["last_seen"] == "2024-01-15T08:00:00Z"


# ---------------------------------------------------------------------------
# §4 — Count aggregation
# ---------------------------------------------------------------------------

def test_count_value(tmp_path):
    """happy_path.csv has 2 INFO/auth rows and 2 ERROR/auth rows."""
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "happy_path.csv", out)
    rows = read_summary(out)
    by_key = {(r["level"], r["service"]): r for r in rows}
    assert by_key[("INFO", "auth")]["count"] == "2"
    assert by_key[("ERROR", "auth")]["count"] == "2"


def test_count_excludes_malformed_timestamp_rows(tmp_path):
    """malformed_ts.csv has 4 rows for ERROR/svc, 2 malformed → count must be 2."""
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "malformed_ts.csv", out)
    rows = read_summary(out)
    assert len(rows) == 1
    assert rows[0]["count"] == "2"


# ---------------------------------------------------------------------------
# §6 — Missing / blank level → UNKNOWN
# ---------------------------------------------------------------------------

def test_blank_level_becomes_unknown(tmp_path):
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "missing_level.csv", out)
    assert result.returncode == 0

    rows = read_summary(out)
    keys = {r["level"] for r in rows}
    assert "UNKNOWN" in keys


def test_blank_level_row_not_dropped(tmp_path):
    """The blank-level row must contribute to count, not be silently skipped."""
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "missing_level.csv", out)
    rows = read_summary(out)
    by_key = {(r["level"], r["service"]): r for r in rows}
    assert ("UNKNOWN", "auth") in by_key
    assert by_key[("UNKNOWN", "auth")]["count"] == "1"


def test_blank_level_emits_stderr_warning_with_line_number(tmp_path):
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "missing_level.csv", out)
    # Line 2 is the blank-level row (line 1 is header)
    assert "2" in result.stderr


# ---------------------------------------------------------------------------
# §7 — Malformed timestamp
# ---------------------------------------------------------------------------

def test_malformed_timestamp_row_skipped(tmp_path):
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "malformed_ts.csv", out)
    assert result.returncode == 0

    rows = read_summary(out)
    # Only 2 valid rows → count == 2
    assert rows[0]["count"] == "2"


def test_malformed_timestamp_emits_stderr_warning_with_line_number(tmp_path):
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "malformed_ts.csv", out)
    stderr = result.stderr
    # Rows 2 and 4 (data lines 1 and 3) are malformed; at least one line number must appear
    assert any(n in stderr for n in ("2", "4"))


def test_malformed_timestamp_processing_continues(tmp_path):
    """Valid rows after a bad row must still be counted (not halted)."""
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "malformed_ts.csv", out)
    rows = read_summary(out)
    assert int(rows[0]["count"]) >= 2


# ---------------------------------------------------------------------------
# §8 — Empty input
# ---------------------------------------------------------------------------

def test_header_only_input_exits_zero(tmp_path):
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "header_only.csv", out)
    assert result.returncode == 0


def test_header_only_input_writes_header_only_output(tmp_path):
    out = tmp_path / "summary.csv"
    run_logsum(FIXTURES / "header_only.csv", out)
    rows = read_summary(out)
    assert rows == []
    # But the file must exist with the correct header
    with out.open(newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == ["level", "service", "count", "first_seen", "last_seen"]


def test_completely_empty_file_exits_zero(tmp_path):
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "empty_file.csv", out)
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# §9 — Exit codes and CLI flags
# ---------------------------------------------------------------------------

def test_exit_zero_on_success(tmp_path):
    out = tmp_path / "summary.csv"
    result = run_logsum(FIXTURES / "happy_path.csv", out)
    assert result.returncode == 0


def test_exit_one_on_missing_input_file(tmp_path):
    out = tmp_path / "summary.csv"
    result = run_logsum(tmp_path / "nonexistent.csv", out)
    assert result.returncode == 1


def test_exit_two_on_unwritable_output(tmp_path):
    """Output path inside a non-existent directory → not writable → exit 2."""
    out = tmp_path / "no_such_dir" / "summary.csv"
    result = run_logsum(FIXTURES / "happy_path.csv", out)
    assert result.returncode == 2


def test_short_flags(tmp_path):
    out = tmp_path / "summary.csv"
    cmd = LOGSUM + ["-i", str(FIXTURES / "happy_path.csv"), "-o", str(out)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    rows = read_summary(out)
    assert len(rows) > 0


def test_default_input_filename_used_when_no_flag(tmp_path):
    """When --input is omitted, tool should look for events.csv in cwd."""
    import shutil
    shutil.copy(FIXTURES / "happy_path.csv", tmp_path / "events.csv")
    out = tmp_path / "summary.csv"
    cmd = LOGSUM + ["--output", str(out)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp_path), env=_cwd_env(tmp_path))
    assert result.returncode == 0


def test_default_output_filename_used_when_no_flag(tmp_path):
    """When --output is omitted, tool should write summary.csv in cwd."""
    import shutil
    shutil.copy(FIXTURES / "happy_path.csv", tmp_path / "events.csv")
    cmd = LOGSUM
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp_path), env=_cwd_env(tmp_path))
    assert result.returncode == 0
    assert (tmp_path / "summary.csv").exists()


# ---------------------------------------------------------------------------
# Additional columns beyond 'message' are ignored (§1)
# ---------------------------------------------------------------------------

def test_extra_columns_ignored(tmp_path):
    csv_content = (
        "timestamp,level,service,message,extra_col,another\n"
        "2024-01-15T08:00:00Z,INFO,svc,msg,x,y\n"
    )
    inp = tmp_path / "extra_cols.csv"
    inp.write_text(csv_content, encoding="utf-8")
    out = tmp_path / "summary.csv"
    result = run_logsum(inp, out)
    assert result.returncode == 0
    rows = read_summary(out)
    assert len(rows) == 1
    assert rows[0]["level"] == "INFO"
