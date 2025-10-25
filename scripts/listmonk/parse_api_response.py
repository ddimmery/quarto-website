#!/usr/bin/env python3
"""Parse Listmonk API response and extract campaign ID."""

import sys
import json


def main():
    try:
        data = json.load(sys.stdin)
        if 'data' in data and 'id' in data['data']:
            print(data['data']['id'])
        else:
            print('Error: Invalid response format', file=sys.stderr)
            print(json.dumps(data, indent=2), file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f'Error parsing response: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
