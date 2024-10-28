import os
import sys
import argparse
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import yaml
import subprocess
import shutil

@dataclass
class PaperSource:
    repo_url: str
    target_folder: str
    branch: Optional[str] = None
    commit: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Optional['PaperSource']:
        """Create a PaperSource from a dictionary, returning None if invalid."""
        # Check required fields
        if not all(k in data for k in ('repo_url', 'target_folder')):
            return None
            
        # Create with required fields
        try:
            return cls(
                repo_url=data['repo_url'],
                target_folder=data['target_folder'],
                branch=data.get('branch'),  # Optional fields use get()
                commit=data.get('commit')
            )
        except (KeyError, TypeError):
            return None

class PaperFetcher:
    def __init__(self, force_update: bool = False, debug: bool = False):
        self.force_update = force_update
        self.debug = debug
        self.setup_logging()
        self.script_dir = Path(__file__).parent
        self.script_path = self.script_dir / 'fetch_paper_template.sh'
        
    def setup_logging(self) -> None:
        level = logging.DEBUG if self.debug else logging.INFO
        handlers = [
            logging.StreamHandler(),
            logging.FileHandler(f"paper_fetch_{datetime.now():%Y%m%d}.log")
        ]
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)

    def load_papers(self) -> List[PaperSource]:
        config_path = self.script_dir / 'research/_paper_sources.yml'
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            sources = []
            for paper in config.get('papers', []):
                if source := PaperSource.from_dict(paper):
                    sources.append(source)
                else:
                    self.logger.warning(f"Invalid paper configuration: {paper}")
            return sources
        except Exception as e:
            self.logger.error(f"Failed to load paper sources: {e}")
            return []

    def process_paper(self, paper: PaperSource) -> bool:
        """Process a single paper with enhanced error handling."""
        self.logger.info(f"Processing {paper.repo_url}")
        
        env = {
            **os.environ,
            'PAPER_REPO_URL': paper.repo_url,
            'PAPER_TARGET_FOLDER': paper.target_folder,
            'PAPER_FORCE_UPDATE': str(self.force_update).lower(),
            'PAPER_DEBUG': str(self.debug).lower(),
            'PAPER_BRANCH': paper.branch or '',
            'PAPER_COMMIT': paper.commit or ''
        }
        
        try:
            result = subprocess.run(
                [self.script_path],
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
            
            if self.debug:
                self.logger.debug(f"Script output:\n{result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            error_context = (
                f"\nExit code: {e.returncode}"
                f"\nStdout:\n{e.stdout}"
                f"\nStderr:\n{e.stderr}"
                f"\nCommand: {e.cmd}"
                f"\nEnvironment:"
                f"\n  PAPER_REPO_URL={env['PAPER_REPO_URL']}"
                f"\n  PAPER_TARGET_FOLDER={env['PAPER_TARGET_FOLDER']}"
                f"\n  PAPER_FORCE_UPDATE={env['PAPER_FORCE_UPDATE']}"
            )
            
            self.logger.error(f"Failed to process paper: {e}{error_context}")
            
            # Clean up on failure
            try:
                for path in [
                    Path("research/papers") / paper.target_folder,
                    Path("_freeze/research/papers") / paper.target_folder
                ]:
                    if path.exists():
                        self.logger.debug(f"Cleaning up: {path}")
                        shutil.rmtree(path)
            except Exception as cleanup_error:
                self.logger.error(f"Cleanup failed: {cleanup_error}")
                
            return False

    def fetch_papers(self) -> None:
        if not self.script_path.exists():
            self.logger.error("Fetch script not found")
            return

        papers = self.load_papers()
        if not papers:
            self.logger.warning("No valid papers to process")
            return

        successful = 0
        failed = 0

        for paper in papers:
            if self.process_paper(paper):
                successful += 1
            else:
                failed += 1

        self.logger.info(f"Processing complete. Successful: {successful}, Failed: {failed}")

def main():
    parser = argparse.ArgumentParser(description="Fetch papers for Quarto website")
    parser.add_argument("--force", "-f", action="store_true", help="Force update")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    try:
        fetcher = PaperFetcher(force_update=args.force, debug=args.debug)
        fetcher.fetch_papers()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()