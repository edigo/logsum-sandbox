# logsum CLI — Specification

## Goal

`logsum` is a command-line tool that reads a structured event log (`events.csv`) and produces
a compact summary (`summary.csv`). It groups events by log level and service, then reports
how many events occurred in each group and when. The tool exists to give operators a quick,
machine-readable overview of which services are producing which severity of events, without
requiring a full log-analytics stack.

## 1. Inputs

Input file: `events.csv`. UTF-8, comma-separated, with a header row.

| Column | Type | Expected format |
|---|---|---|
| `timestamp` | string | ISO 8601 datetime, with or without UTC offset (e.g. `2024-01-15T08:00:00Z`, `2024-01-15T08:00:00+02:00`) |
| `level` | string | Log severity label (e.g. `INFO`, `WARN`, `ERROR`); may be mixed case |
| `service` | string | Name of the originating service; may be mixed case |
| `message` | string | Free-text log message; not used in aggregation |

Column order in the header row must match exactly. Additional columns beyond `message` are
ignored.

## 2. Group key

Each output row represents one unique `(level, service)` pair, evaluated after normalisation.

## 3. Normalisation

- `level`: strip surrounding whitespace, convert to uppercase (e.g. `info` → `INFO`).
- `service`: strip surrounding whitespace, convert to lowercase (e.g. `Auth` → `auth`).
- `timestamp` (input parsing): accept any valid ISO 8601 value with or without UTC offset.
- `first_seen` / `last_seen` (output): convert to UTC and write as `YYYY-MM-DDTHH:MM:SSZ`
  (no microseconds, no offset notation). Two events at the same instant always produce the
  same string regardless of how the source offset was expressed.

## 4. Aggregation

For each `(level, service)` group, compute:

- `count` — total number of input rows belonging to the group.
- `first_seen` — the earliest `timestamp` value in the group, after parsing and UTC conversion.
- `last_seen` — the latest `timestamp` value in the group, after parsing and UTC conversion.

Rows with a malformed timestamp are excluded from all three aggregates (see §6).

## 5. Output columns

`summary.csv` contains exactly these columns in this order:

| Column | Type | Description |
|---|---|---|
| `level` | string | Normalised log level |
| `service` | string | Normalised service name |
| `count` | integer | Number of matching rows in input |
| `first_seen` | string | Earliest timestamp in the group (UTC, ISO 8601 Z) |
| `last_seen` | string | Latest timestamp in the group (UTC, ISO 8601 Z) |

## 6. Missing level behaviour

If `level` is absent or blank, substitute `UNKNOWN`. Emit a warning to stderr including the
line number. Do not drop the row.

## 7. Malformed timestamp behaviour

Skip the row. Emit a warning to stderr including the line number. Continue processing all
remaining rows.

## 8. Empty input behaviour

If `events.csv` exists but contains no data rows (header only, or completely empty), write a
header-only `summary.csv` and exit 0. No error is raised.

## 9. CLI flags and exit codes

| Flag | Short | Default | Description |
|---|---|---|---|
| `--input` | `-i` | `events.csv` | Path to input CSV |
| `--output` | `-o` | `summary.csv` | Path to output CSV |

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 1 | Input file not found or unreadable |
| 2 | Output file not writable |

## 10. Out of scope

- Date-range filtering
- Streaming or real-time input
- Message deduplication or clustering
- Sorting of output rows
- Any output format other than CSV

## Signed off

EG — 2026-07-24

## Implementation notes

UTC offset conversion silently reverses the intuitive first/last order: `2024-01-15T09:30:00+02:00` normalises to `07:30Z`, making it *earlier* than a plain `08:00Z` row in the same group — the AI's draft preview table had `first_seen` and `last_seen` swapped as a result.
