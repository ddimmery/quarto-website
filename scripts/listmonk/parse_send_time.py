#!/usr/bin/env python3
"""Parse flexible datetime input and convert to ISO 8601 UTC format."""

import sys
from dateparser import parse
import pytz


def main():
    if len(sys.argv) != 3:
        print("Usage: parse_send_time.py <input_time> <timezone>", file=sys.stderr)
        sys.exit(1)

    input_time = sys.argv[1]
    timezone = sys.argv[2]

    # Parse the input time
    parsed = parse(
        input_time,
        settings={'TIMEZONE': timezone, 'RETURN_AS_TIMEZONE_AWARE': True}
    )

    if parsed is None:
        print(f'Error: Could not parse time: {input_time}', file=sys.stderr)
        sys.exit(1)

    # Convert to UTC and format as ISO 8601
    utc_time = parsed.astimezone(pytz.UTC)
    iso_format = utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    print(iso_format)


if __name__ == '__main__':
    main()
