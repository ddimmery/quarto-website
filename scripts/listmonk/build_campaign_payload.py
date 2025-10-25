#!/usr/bin/env python3
"""Build JSON payload for Listmonk campaign creation."""

import sys
import json


def main():
    if len(sys.argv) < 5:
        print(
            "Usage: build_campaign_payload.py <campaign_name> <subject> <list_ids_json> "
            "<html_body_file> [from_email] [send_at] [altbody]",
            file=sys.stderr
        )
        sys.exit(1)

    campaign_name = sys.argv[1]
    subject = sys.argv[2]
    list_ids = json.loads(sys.argv[3])
    html_body_file = sys.argv[4]
    from_email = sys.argv[5] if len(sys.argv) > 5 else None
    send_at = sys.argv[6] if len(sys.argv) > 6 else None
    altbody = sys.argv[7] if len(sys.argv) > 7 else None

    # Read HTML body
    with open(html_body_file, 'r', encoding='utf-8') as f:
        body = f.read()

    data = {
        'name': campaign_name,
        'subject': subject,
        'lists': list_ids,
        'type': 'regular',
        'content_type': 'html',
        'body': body,
        'messenger': 'email'
    }

    # Add optional fields
    if from_email:
        data['from_email'] = from_email

    if send_at:
        data['send_at'] = send_at

    if altbody:
        data['altbody'] = altbody

    print(json.dumps(data))


if __name__ == '__main__':
    main()
