#!/usr/bin/env python3
"""
Convert all main images to PNG format and standardize sizes.
"""
import os
import subprocess
from pathlib import Path

def convert_image_to_png(input_path, output_path, target_width=1200):
    """Convert an image to PNG format and resize to consistent width."""
    try:
        # Using macOS sips command
        # First convert to PNG
        cmd = [
            'sips', 
            '-s', 'format', 'png',
            '-Z', str(target_width),  # Resize to target width maintaining aspect ratio
            str(input_path),
            '--out', str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Converted {input_path} -> {output_path}")
            return True
        else:
            print(f"Failed to convert {input_path}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False

def main():
    posts_dir = Path('posts')
    
    # Dictionary mapping posts to their main image files
    main_images = {}
    
    # Find all posts and their referenced images
    for post_dir in posts_dir.iterdir():
        if post_dir.is_dir():
            index_file = post_dir / 'index.qmd'
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for image reference in metadata
                import re
                image_match = re.search(r'^image:\s*(.+)$', content, re.MULTILINE)
                if image_match:
                    image_ref = image_match.group(1).strip()
                    
                    # Skip absolute paths (existing converted images)
                    if image_ref.startswith('/'):
                        continue
                        
                    main_images[post_dir.name] = {
                        'reference': image_ref,
                        'post_dir': post_dir
                    }
    
    print(f"Found {len(main_images)} posts with main images to process:")
    for post_name, info in main_images.items():
        print(f"  {post_name}: {info['reference']}")
    
    # Process each post's main image
    for post_name, info in main_images.items():
        post_dir = info['post_dir']
        image_ref = info['reference']
        
        # Find the actual image file
        potential_files = []
        
        # Check for main-image files
        for ext in ['.jpeg', '.jpg', '.png', '.webp']:
            main_img_path = post_dir / f'main-image{ext}'
            if main_img_path.exists():
                potential_files.append(main_img_path)
        
        # Check for image_1 files (fallback)
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            img1_path = post_dir / f'image_1{ext}'
            if img1_path.exists():
                potential_files.append(img1_path)
        
        if not potential_files:
            print(f"No main image found for {post_name}")
            continue
            
        # Use the first available image
        source_image = potential_files[0]
        target_image = post_dir / 'main-image.png'
        
        print(f"Processing {post_name}:")
        print(f"  Source: {source_image}")
        print(f"  Target: {target_image}")
        
        # Convert to PNG
        if convert_image_to_png(source_image, target_image):
            # Update the index.qmd file to reference the new PNG
            index_file = post_dir / 'index.qmd'
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update the image reference
            updated_content = re.sub(
                r'^image:\s*.+$', 
                'image: main-image.png', 
                content, 
                flags=re.MULTILINE
            )
            
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            print(f"  Updated {index_file} to reference main-image.png")
    
    # Also convert the existing JPG images
    jpg_images = [
        ('posts/quarto-website/tobias-meme.jpg', 'posts/quarto-website/main-image.png'),
        ('posts/softblock-demo/three-designs.jpg', 'posts/softblock-demo/main-image.png')
    ]
    
    for source_path, target_path in jpg_images:
        source = Path(source_path)
        target = Path(target_path)
        
        if source.exists():
            print(f"Converting existing JPG: {source_path}")
            if convert_image_to_png(source, target):
                # Update the corresponding index.qmd files
                post_dir = target.parent
                index_file = post_dir / 'index.qmd'
                
                if index_file.exists():
                    with open(index_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Update the image reference to be relative
                    updated_content = re.sub(
                        r'image:\s*/posts/[^/]+/[^/\s]+',
                        'image: main-image.png',
                        content
                    )
                    
                    with open(index_file, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                        
                    print(f"  Updated {index_file} to reference main-image.png")

if __name__ == '__main__':
    main()