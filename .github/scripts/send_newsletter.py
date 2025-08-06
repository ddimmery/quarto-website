#!/usr/bin/env python3
"""
Newsletter sender script for Quarto blog posts.
Uses already-rendered HTML files from _site directory.
"""

import os
import sys
import json
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict
from bs4 import BeautifulSoup
import html2text


def load_email_list() -> List[Dict]:
    """Load the email list from the decrypted JSON file."""
    try:
        with open('email_list.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: email_list.json not found. Make sure decryption succeeded.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in email list file.")
        sys.exit(1)


def process_html_for_email(html_path: str, site_url: str = "https://ddimmery.com") -> tuple[str, str, str]:
    """Process the rendered HTML file for email sending."""
    if not os.path.exists(html_path):
        print(f"Error: HTML file {html_path} not found.")
        sys.exit(1)
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract title
    title_elem = soup.find('title')
    title = title_elem.get_text().strip() if title_elem else "Blog Post"
    
    # Extract the main content (adjust selector based on your Quarto theme)
    # Common selectors for Quarto content
    content_selectors = [
        'main',
        '.quarto-container main',
        '#quarto-content',
        '.content',
        'article'
    ]
    
    content_elem = None
    for selector in content_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            break
    
    if not content_elem:
        # Fallback: use body content but remove nav/footer
        content_elem = soup.find('body')
        if content_elem:
            # Remove navigation and footer elements
            for elem in content_elem.find_all(['nav', 'footer', '.navbar', '.footer']):
                elem.decompose()
    
    if not content_elem:
        print("Error: Could not find main content in HTML file.")
        sys.exit(1)
    
    # Convert relative URLs to absolute
    for link in content_elem.find_all('a', href=True):
        href = link['href']
        if href.startswith('/'):
            link['href'] = site_url + href
        elif href.startswith('./') or not href.startswith(('http://', 'https://', 'mailto:')):
            # Handle relative links
            link['href'] = site_url + '/' + href.lstrip('./')
    
    for img in content_elem.find_all('img', src=True):
        src = img['src']
        if src.startswith('/'):
            img['src'] = site_url + src
        elif src.startswith('./') or not src.startswith(('http://', 'https://')):
            img['src'] = site_url + '/' + src.lstrip('./')
    
    # Create email-friendly HTML
    email_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{ color: #2c3e50; margin-top: 1.5em; }}
        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        pre, code {{ 
            background: #f8f9fa; 
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
        }}
        pre {{ 
            padding: 15px; 
            border-radius: 5px; 
            overflow-x: auto;
            border: 1px solid #e9ecef;
        }}
        code {{ 
            padding: 2px 4px; 
            border-radius: 3px; 
        }}
        blockquote {{ 
            border-left: 4px solid #3498db;
            margin: 0;
            padding-left: 20px;
            font-style: italic;
            color: #555;
        }}
        img {{ 
            max-width: 100%; 
            height: auto;
            display: block;
            margin: 1em auto;
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 8px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 14px;
        }}
        .content {{ margin-bottom: 2em; }}
    </style>
</head>
<body>
    <div class="content">
        {content_elem}
    </div>
    
    <div class="footer">
        <p>
            <a href="{site_url}">Visit the blog</a> • 
            <a href="{site_url}/about.html">About</a>
        </p>
        <p><small>You're receiving this because you subscribed to Drew Dimmery's newsletter.</small></p>
    </div>
</body>
</html>
"""
    
    # Create plain text version
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 78
    h.ignore_images = False
    text_content = h.handle(email_html)
    
    return email_html, text_content, title


def send_email(to_email: str, subject: str, html_content: str, text_content: str):
    """Send an email via SMTP."""
    msg = MIMEMultipart('alternative')
    msg['From'] = f"{os.environ['FROM_NAME']} <{os.environ['FROM_EMAIL']}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add both plain text and HTML versions
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    html_part = MIMEText(html_content, 'html', 'utf-8')
    
    msg.attach(text_part)
    msg.attach(html_part)
    
    # Send the email
    with smtplib.SMTP(os.environ['SMTP_SERVER'], int(os.environ['SMTP_PORT'])) as server:
        server.starttls()
        server.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
        server.send_message(msg)


def main():
    parser = argparse.ArgumentParser(description='Send newsletter from rendered Quarto HTML')
    parser.add_argument('--post-path', required=True, help='Path to the rendered HTML file')
    parser.add_argument('--subject-override', help='Override email subject')
    parser.add_argument('--test-mode', action='store_true', help='Send to test email only')
    
    args = parser.parse_args()
    
    # Required environment variables
    required_env_vars = [
        'SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD',
        'FROM_EMAIL', 'FROM_NAME'
    ]
    
    if args.test_mode:
        required_env_vars.append('TEST_EMAIL')
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Process the HTML file
    print(f"Processing HTML file: {args.post_path}")
    html_content, text_content, title = process_html_for_email(args.post_path)
    
    # Determine subject
    subject = args.subject_override or f"New post: {title}"
    
    if args.test_mode:
        # Send to test email only
        print(f"Sending test email to: {os.environ['TEST_EMAIL']}")
        send_email(os.environ['TEST_EMAIL'], f"[TEST] {subject}", html_content, text_content)
        print("Test email sent successfully!")
    else:
        # Load email list and send to all subscribers
        email_list = load_email_list()
        print(f"Sending to {len(email_list)} subscribers...")
        
        success_count = 0
        for subscriber in email_list:
            try:
                email_addr = subscriber.get('email')
                if not email_addr:
                    print(f"Warning: Skipping subscriber with no email address")
                    continue
                
                print(f"Sending to: {email_addr}")
                send_email(email_addr, subject, html_content, text_content)
                success_count += 1
                
            except Exception as e:
                print(f"Failed to send to {email_addr}: {str(e)}")
        
        print(f"Newsletter sent successfully to {success_count}/{len(email_list)} subscribers!")


if __name__ == "__main__":
    main()