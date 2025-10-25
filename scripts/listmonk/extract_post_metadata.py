#!/usr/bin/env python3
"""Extract metadata from Quarto post YAML frontmatter."""

import sys
import yaml
import json


def main():
    if len(sys.argv) != 2:
        print("Usage: extract_post_metadata.py <post_path>", file=sys.stderr)
        sys.exit(1)

    post_path = sys.argv[1]

    try:
        with open(post_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract YAML frontmatter between --- delimiters
            parts = content.split('---')
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                # Output as JSON for easy parsing in shell
                output = {
                    'title': metadata.get('title', 'Untitled'),
                    'description': metadata.get('description', ''),
                    'date': metadata.get('date', '')
                }
                print(json.dumps(output))
            else:
                print(json.dumps({
                    'title': 'Untitled',
                    'description': '',
                    'date': ''
                }))
    except Exception as e:
        print(f"Error reading metadata: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
