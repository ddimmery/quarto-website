#!/usr/bin/env python3
"""
Convert Substack exported posts to Quarto markdown format.
"""
import csv
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
import html

def download_image(url, post_dir, img_counter):
    """Download an image and return the local path."""
    try:
        # Get file extension from URL or default to .jpg
        parsed_url = urllib.parse.urlparse(url)
        ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
        
        filename = f"image_{img_counter}{ext}"
        filepath = os.path.join(post_dir, filename)
        
        urllib.request.urlretrieve(url, filepath)
            
        return filename
    except Exception as e:
        print(f"Failed to download image {url}: {e}")
        return url  # Fallback to original URL

def extract_footnotes(html_content):
    """Extract footnotes and return them as a dictionary."""
    footnotes = {}
    
    # Find all footnote divs
    footnote_pattern = r'<div class="footnote"[^>]*>.*?<a[^>]*id="footnote-(\d+)"[^>]*>(\d+)</a>.*?<div class="footnote-content"><p>(.*?)</p></div>.*?</div>'
    
    for match in re.finditer(footnote_pattern, html_content, flags=re.DOTALL):
        footnote_id = match.group(1)
        footnote_num = match.group(2)
        footnote_text = match.group(3)
        
        # Convert links in footnotes first
        footnote_text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', footnote_text, flags=re.DOTALL)
        
        # Clean remaining HTML from footnote text
        footnote_text = re.sub(r'<[^>]+>', '', footnote_text)
        footnote_text = html.unescape(footnote_text)
        
        footnotes[footnote_num] = footnote_text
    
    return footnotes

def clean_html_content(html_content, post_dir, post_slug):
    """Clean HTML content and convert to Quarto-friendly markdown."""
    # Extract footnotes first
    footnotes = extract_footnotes(html_content)
    
    # Remove Substack-specific elements
    html_content = re.sub(r'<p class="button-wrapper".*?</p>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<div><hr></div>', '\n\n---\n\n', html_content)
    
    # Handle footnote anchors - convert to Quarto footnotes
    def replace_footnote_anchor(match):
        footnote_num = match.group(1)
        if footnote_num in footnotes:
            return f'^[{footnotes[footnote_num]}]'
        else:
            return f'^[Footnote {footnote_num}]'
    
    html_content = re.sub(r'<a class="footnote-anchor"[^>]*href="#footnote-(\d+)"[^>]*>(\d+)</a>', replace_footnote_anchor, html_content)
    
    # Remove footnote divs at the end
    html_content = re.sub(r'<div class="footnote".*?</div>', '', html_content, flags=re.DOTALL)
    
    # Handle images - download them and convert to local references
    img_counter = 1
    def replace_image(match):
        nonlocal img_counter
        url = match.group(1)
        
        if url.startswith('http'):
            local_path = download_image(url, post_dir, img_counter)
            img_counter += 1
            return f'\n\n![Image]({local_path})\n\n'
        else:
            return f'\n\n![Image]({url})\n\n'
    
    # Match Substack image containers
    img_pattern = r'<div class="captioned-image-container">.*?<img[^>]*src="([^"]*)"[^>]*>.*?</div>'
    html_content = re.sub(img_pattern, replace_image, html_content, flags=re.DOTALL)
    
    # Also handle simpler img tags
    simple_img_pattern = r'<img[^>]*src="([^"]*)"[^>]*>'
    html_content = re.sub(simple_img_pattern, replace_image, html_content, flags=re.DOTALL)
    
    # Convert headings
    html_content = re.sub(r'<h1>(.*?)</h1>', r'# \1\n\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h2>(.*?)</h2>', r'## \1\n\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h3>(.*?)</h3>', r'### \1\n\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h4>(.*?)</h4>', r'#### \1\n\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h5>(.*?)</h5>', r'##### \1\n\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<h6>(.*?)</h6>', r'###### \1\n\n', html_content, flags=re.DOTALL)
    
    # Handle text formatting
    html_content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<em>(.*?)</em>', r'*\1*', html_content, flags=re.DOTALL)
    
    # Handle lists
    html_content = re.sub(r'<ul>\s*', '\n', html_content)
    html_content = re.sub(r'\s*</ul>', '\n\n', html_content)
    html_content = re.sub(r'<li><p>(.*?)</p></li>', r'- \1\n', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<li>(.*?)</li>', r'- \1\n', html_content, flags=re.DOTALL)
    
    # Handle blockquotes - support multiple paragraphs
    def replace_blockquote(match):
        blockquote_content = match.group(1)
        # Handle multiple paragraphs within blockquote
        paragraphs = re.findall(r'<p>(.*?)</p>', blockquote_content, flags=re.DOTALL)
        if paragraphs:
            # Join paragraphs with blockquote formatting
            formatted_paragraphs = []
            for p in paragraphs:
                # Clean up the paragraph content
                p_clean = re.sub(r'<[^>]+>', '', p)
                p_clean = html.unescape(p_clean).strip()
                if p_clean:  # Only add non-empty paragraphs
                    formatted_paragraphs.append(f'> {p_clean}')
            return '\n>\n'.join(formatted_paragraphs) + '\n\n'
        else:
            # Fallback for blockquotes without p tags
            content_clean = re.sub(r'<[^>]+>', '', blockquote_content)
            content_clean = html.unescape(content_clean).strip()
            return f'> {content_clean}\n\n'
    
    html_content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', replace_blockquote, html_content, flags=re.DOTALL)
    
    # Handle links - convert to markdown format
    html_content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', html_content, flags=re.DOTALL)
    
    # Handle paragraphs - convert to markdown with proper spacing
    html_content = re.sub(r'<p>(.*?)</p>', r'\1\n\n', html_content, flags=re.DOTALL)
    
    # Clean up remaining HTML tags
    html_content = re.sub(r'<[^>]+>', '', html_content)
    
    # Decode HTML entities
    html_content = html.unescape(html_content)
    
    # Clean up whitespace - multiple newlines to double newlines
    html_content = re.sub(r'\n{3,}', '\n\n', html_content)
    html_content = html_content.strip()
    
    return html_content

def process_posts():
    """Process all published Substack posts and convert to QMD format."""
    posts_csv_path = 'substack-export/posts.csv'
    posts_dir = 'substack-export/posts'
    output_dir = 'posts'
    
    # Read the posts CSV
    with open(posts_csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Skip unpublished posts
            if row['is_published'] != 'true':
                continue
                
            post_id = row['post_id']
            title = row['title'].strip() if row['title'] else 'Untitled'
            subtitle = row['subtitle'].strip() if row['subtitle'] else ''
            
            # Parse date
            if row['post_date']:
                date_obj = datetime.fromisoformat(row['post_date'].replace('Z', '+00:00'))
                date_str = date_obj.strftime('%Y-%m-%d')
            else:
                date_str = '2023-01-01'  # fallback date
            
            # Read HTML content
            html_file = os.path.join(posts_dir, f'{post_id}.html')
            if not os.path.exists(html_file):
                print(f"HTML file not found: {html_file}")
                continue
                
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create slug from title
            slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
            slug = re.sub(r'\s+', '-', slug).strip('-')
            if not slug:
                slug = f'post-{post_id.split(".")[0]}'
            
            # Create post directory
            post_dir = os.path.join(output_dir, slug)
            os.makedirs(post_dir, exist_ok=True)
            
            # Convert HTML to markdown
            markdown_content = clean_html_content(html_content, post_dir, slug)
            
            # Generate QMD content
            qmd_content = f"""---
title: "{title}"
"""
            if subtitle:
                qmd_content += f'description: "{subtitle}"\n'
            
            qmd_content += f"""date: "{date_str}"
categories:
  - substack
---

{markdown_content}
"""
            
            # Write QMD file
            qmd_file = os.path.join(post_dir, 'index.qmd')
            with open(qmd_file, 'w', encoding='utf-8') as f:
                f.write(qmd_content)
                
            print(f"Converted: {title} -> {qmd_file}")

if __name__ == '__main__':
    process_posts()