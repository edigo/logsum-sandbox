import argparse
import csv
import sys
from datetime import datetime, timezone


def _parse_ts(raw):
    try:
        dt = datetime.fromisoformat(raw.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.replace(microsecond=0)
    except (ValueError, AttributeError):
        return None


def _normalise_level(raw):
    v = raw.strip().upper()
    return v if v else "UNKNOWN"


def _normalise_service(raw):
    return raw.strip().lower()


def _read_groups(input_path):
    groups = {}
    try:
        with open(input_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for lineno, row in enumerate(reader, start=2):
                raw_level = row.get("level", "")
                if not raw_level.strip():
                    print(
                        f"WARNING: line {lineno}: blank level, substituting UNKNOWN",
                        file=sys.stderr,
                    )
                raw_ts = row.get("timestamp", "")
                ts = _parse_ts(raw_ts)
                if ts is None:
                    print(
                        f"WARNING: line {lineno}: malformed timestamp {raw_ts!r}, skipping row",
                        file=sys.stderr,
                    )
                    continue
                level = _normalise_level(raw_level)
                service = _normalise_service(row.get("service", ""))
                key = (level, service)
                groups.setdefault(key, {"count": 0, "first": ts, "last": ts})
                groups[key]["count"] += 1
                groups[key]["first"] = min(groups[key]["first"], ts)
                groups[key]["last"] = max(groups[key]["last"], ts)
    except OSError as exc:
        print(f"ERROR: cannot read input: {exc}", file=sys.stderr)
        sys.exit(1)
    return groups


def _write_summary(output_path, groups):
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["level", "service", "count", "first_seen", "last_seen"])
            for (level, service), data in groups.items():
                writer.writerow(
                    [
                        level,
                        service,
                        data["count"],
                        data["first"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                        data["last"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    ]
                )
    except OSError as exc:
        print(f"ERROR: cannot write output: {exc}", file=sys.stderr)
        sys.exit(2)


def summarise(input_path, output_path, min_count=None):
    groups = _read_groups(input_path)
    if min_count is not None:
        groups = {k: v for k, v in groups.items() if v["count"] >= min_count}
    _write_summary(output_path, groups)


def main():
    parser = argparse.ArgumentParser(description="Summarise events.csv logs.")
    parser.add_argument("input_pos", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("output_pos", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("-i", "--input", default="events.csv")
    parser.add_argument("-o", "--output", default="summary.csv")
    parser.add_argument("--min-count", type=int, default=None)
    args = parser.parse_args()

    input_path = args.input_pos if args.input_pos is not None else args.input
    output_path = args.output_pos if args.output_pos is not None else args.output

    summarise(input_path, output_path, min_count=args.min_count)


if __name__ == "__main__":
    main()
