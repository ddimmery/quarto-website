import os
import sys
import argparse
from dataclasses import dataclass
from typing import List
import yaml
from pathlib import Path
import subprocess
import stat


@dataclass
class PaperSource:
    repo_url: str
    target_folder: str

def check_environment():
    """Check if required environment variables are set."""
    if not os.getenv("QUARTO_PROJECT_RENDER_ALL"):
        print("QUARTO_PROJECT_RENDER_ALL is not set. Exiting.")
        sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description='Fetch papers for Quarto website')
    parser.add_argument('--force', '-f', 
                       action='store_true',
                       help='Force update regardless of commit hash')
    return parser.parse_args()


def load_paper_sources(config_file: Path) -> List[PaperSource]:
    """Load paper sources from a YAML configuration file."""
    with open(config_file) as f:
        config = yaml.safe_load(f)

    sources = []
    for paper in config.get("papers", []):
        sources.append(
            PaperSource(
                repo_url=paper["repo_url"], target_folder=paper["target_folder"]
            )
        )
    return sources

def ensure_script_executable(script_path: Path):
    """Ensure the script has executable permissions."""
    current_mode = script_path.stat().st_mode
    executable_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    script_path.chmod(executable_mode)

def run_fetch_script(
    paper_source: PaperSource,
    script_path: Path,
    force_update: bool
) -> None:
    """Run the fetch script with the appropriate environment variables."""
    # Ensure script is executable
    ensure_script_executable(script_path)
    
    env = os.environ.copy()
    env.update({
        'PAPER_REPO_URL': paper_source.repo_url,
        'PAPER_TARGET_FOLDER': paper_source.target_folder,
        'PAPER_FORCE_UPDATE': str(force_update).lower()
    })
    
    try:
        subprocess.run([str(script_path)], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching paper from {paper_source.repo_url}: {e}")
        raise


def main():
    args = parse_args()

    # Check environment variables first
    if not args.force:
        check_environment()
    
    # Define paths relative to the script location
    script_dir = Path(__file__).parent
    config_path = script_dir / '_paper_sources.yml'
    script_path = script_dir / 'fetch_paper_template.sh'
    
    # Verify required files exist
    if not config_path.exists():
        print(f"Configuration file {config_path} not found.")
        sys.exit(1)
    
    if not script_path.exists():
        print(f"Template file {script_path} not found.")
        sys.exit(1)
    
    try:
        paper_sources = load_paper_sources(config_path)
        
        for paper_source in paper_sources:
            run_fetch_script(paper_source, script_path, args.force)
                
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()