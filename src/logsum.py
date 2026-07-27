import argparse
import csv
import sys
from datetime import datetime, timezone

_OUT_FMT = '%Y-%m-%dT%H:%M:%SZ'


def _parse_ts(raw):
    try:
        dt = datetime.fromisoformat(raw.strip())
    except (ValueError, AttributeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalise_level(raw):
    s = raw.strip().upper()
    return s if s else 'UNKNOWN'


def _normalise_service(raw):
    return raw.strip().lower()


def summarise(input_path, output_path):
    try:
        f_in = open(input_path, newline='', encoding='utf-8')
    except OSError as e:
        print(f'ERROR: cannot read {input_path}: {e}', file=sys.stderr)
        sys.exit(1)

    groups = {}

    with f_in:
        reader = csv.DictReader(f_in)
        for lineno, row in enumerate(reader, start=2):
            raw_level = row.get('level', '')
            raw_service = row.get('service', '')
            raw_ts = row.get('timestamp', '')

            if not raw_level.strip():
                print(f'WARNING: line {lineno}: blank level, using UNKNOWN', file=sys.stderr)
            level = _normalise_level(raw_level)
            service = _normalise_service(raw_service)

            dt = _parse_ts(raw_ts)
            if dt is None:
                print(f'WARNING: line {lineno}: malformed timestamp {raw_ts!r}, row skipped', file=sys.stderr)
                continue

            key = (level, service)
            if key not in groups:
                groups[key] = {'count': 0, 'first': dt, 'last': dt}
            g = groups[key]
            g['count'] += 1
            g['first'] = min(g['first'], dt)
            g['last'] = max(g['last'], dt)

    try:
        f_out = open(output_path, 'w', newline='', encoding='utf-8')
    except OSError as e:
        print(f'ERROR: cannot write {output_path}: {e}', file=sys.stderr)
        sys.exit(2)

    with f_out:
        writer = csv.writer(f_out)
        writer.writerow(['level', 'service', 'count', 'first_seen', 'last_seen'])
        for (level, service), g in groups.items():
            writer.writerow([
                level, service, g['count'],
                g['first'].strftime(_OUT_FMT),
                g['last'].strftime(_OUT_FMT),
            ])


def main():
    parser = argparse.ArgumentParser(description='Summarise event logs by level and service.')
    parser.add_argument('positional_input', nargs='?', default=None, metavar='INPUT')
    parser.add_argument('positional_output', nargs='?', default=None, metavar='OUTPUT')
    parser.add_argument('--input', '-i', default='events.csv', metavar='PATH')
    parser.add_argument('--output', '-o', default='summary.csv', metavar='PATH')
    args = parser.parse_args()
    summarise(args.positional_input or args.input, args.positional_output or args.output)


if __name__ == '__main__':
    main()
