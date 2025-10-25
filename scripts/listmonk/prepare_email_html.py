#!/usr/bin/env python3
"""Extract HTML content from rendered Quarto post and add email header/footer."""

import sys
from bs4 import BeautifulSoup


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: prepare_email_html.py <html_file> <post_title> <post_url>",
            file=sys.stderr
        )
        sys.exit(1)

    html_file = sys.argv[1]
    post_title = sys.argv[2]
    post_url = sys.argv[3]

    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Try to find the main content area
    content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')

    if not content:
        # Fallback to body if no main content found
        content = soup.find('body')
        if not content:
            content = soup

    # Create header with link to post
    header = soup.new_tag('div', style='margin-bottom: 2em;')
    title_heading = soup.new_tag('h1', style='margin-bottom: 0.5em;')
    title_link = soup.new_tag('a', href=post_url, style='color: #0066cc; text-decoration: none;')
    title_link.string = post_title
    title_heading.append(title_link)
    header.append(title_heading)

    # Create reading note
    reading_note = soup.new_tag('p', style='font-style: italic; color: #666; margin-top: 0.5em;')
    reading_note.string = 'For the best reading experience, '
    read_link = soup.new_tag('a', href=post_url, style='color: #0066cc;')
    read_link.string = 'read this post in its original format on the web'
    reading_note.append(read_link)
    reading_note.append('.')

    # Create wrapper div
    wrapper = soup.new_tag('div')
    wrapper.append(header)
    wrapper.append(reading_note)

    # Add horizontal rule to separate header from content
    hr = soup.new_tag('hr', style='margin: 2em 0; border: none; border-top: 1px solid #ddd;')
    wrapper.append(hr)

    # Add the main content
    wrapper.append(content)

    print(str(wrapper))


if __name__ == '__main__':
    main()
