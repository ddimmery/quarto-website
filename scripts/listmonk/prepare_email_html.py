#!/usr/bin/env python3
"""Extract HTML content from rendered Quarto post and add email header/footer."""

import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def convert_relative_urls(content, base_url):
    """Convert all relative URLs in the content to absolute URLs."""
    # Get the base domain from the post URL
    parsed_base = urlparse(base_url)
    site_base = f"{parsed_base.scheme}://{parsed_base.netloc}"

    # Convert image src attributes
    for img in content.find_all('img'):
        if img.get('src'):
            img['src'] = urljoin(site_base, img['src'])

    # Convert link href attributes (but not anchors starting with #)
    for link in content.find_all('a'):
        if link.get('href') and not link['href'].startswith('#'):
            # Only convert relative URLs, leave absolute URLs as-is
            if not urlparse(link['href']).netloc:
                link['href'] = urljoin(site_base, link['href'])

    # Convert CSS background images in style attributes
    for elem in content.find_all(style=True):
        style = elem['style']
        if 'url(' in style:
            # Simple regex-free approach for common cases
            import re
            def replace_url(match):
                url = match.group(1).strip('\'"')
                if not urlparse(url).netloc:
                    return f'url({urljoin(site_base, url)})'
                return match.group(0)
            elem['style'] = re.sub(r'url\(([^)]+)\)', replace_url, style)

    return content


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

    # Convert all relative URLs to absolute URLs
    content = convert_relative_urls(content, post_url)

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
