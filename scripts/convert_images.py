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
            "sips",
            "-s",
            "format",
            "png",
            "-Z",
            str(target_width),  # Resize to target width maintaining aspect ratio
            str(input_path),
            "--out",
            str(output_path),
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


def get_image_width(image_path):
    """Get the pixel width of an image using sips."""
    try:
        result = subprocess.run(
            ["sips", "-g", "pixelWidth", str(image_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "pixelWidth" in line:
                    return int(line.split(":")[1].strip())
    except Exception:
        pass
    return None


def main():
    import re

    posts_dir = Path("posts")
    target_width = 1200

    for post_dir in sorted(posts_dir.iterdir()):
        if not post_dir.is_dir():
            continue

        index_file = post_dir / "index.qmd"
        if not index_file.exists():
            continue

        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()

        image_match = re.search(r"^image:\s*(.+)$", content, re.MULTILINE)
        if not image_match:
            continue

        image_ref = image_match.group(1).strip()

        # Find the source image: use the referenced file, or search for common names
        source_image = None
        referenced_path = post_dir / image_ref
        if referenced_path.exists():
            source_image = referenced_path
        else:
            for ext in [".jpeg", ".jpg", ".png", ".webp"]:
                for name in ["main-image", "image_1"]:
                    candidate = post_dir / f"{name}{ext}"
                    if candidate.exists():
                        source_image = candidate
                        break
                if source_image:
                    break

        if not source_image:
            print(f"  {post_dir.name}: no image file found, skipping")
            continue

        target_image = post_dir / "main-image.png"

        # Check if already standardized (correct format, name, and width)
        current_width = get_image_width(source_image)
        already_standard = (
            source_image == target_image
            and source_image.suffix == ".png"
            and current_width == target_width
        )

        if already_standard:
            print(
                f"  {post_dir.name}: already standardized ({current_width}px), skipping"
            )
            continue

        print(
            f"  {post_dir.name}: {source_image.name} ({current_width}px) -> main-image.png ({target_width}px)"
        )

        if convert_image_to_png(source_image, target_image, target_width):
            # Update the index.qmd to reference main-image.png
            updated_content = re.sub(
                r"^image:\s*.+$", "image: main-image.png", content, flags=re.MULTILINE
            )
            if updated_content != content:
                with open(index_file, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                print(f"    Updated {index_file}")


if __name__ == "__main__":
    main()
