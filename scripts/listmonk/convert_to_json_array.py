#!/usr/bin/env python3
"""Convert comma-separated values to JSON array."""

import sys
import json


def main():
    # Read from stdin
    input_str = sys.stdin.read().strip()

    if not input_str:
        print("[]")
        return

    # Split and convert to appropriate type
    items = [x.strip() for x in input_str.split(',')]

    # Try to convert to integers if possible, otherwise keep as strings
    try:
        items = [int(x) for x in items]
    except ValueError:
        # Keep as strings if conversion fails
        pass

    print(json.dumps(items))


if __name__ == '__main__':
    main()
