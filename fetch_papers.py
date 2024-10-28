import argparse
import logging
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

import yaml


class PaperResult(NamedTuple):
    success: bool
    error: Optional[str] = None
    cleanup_needed: bool = False


@dataclass
class PaperSource:
    repo_url: str
    target_folder: str
    branch: Optional[str] = None
    commit: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> Optional["PaperSource"]:
        try:
            required_fields = ["repo_url", "target_folder"]
            if not all(field in data for field in required_fields):
                raise ValueError(f"Missing required fields: {required_fields}")

            return cls(
                repo_url=data["repo_url"],
                target_folder=data["target_folder"],
                branch=data.get("branch"),
                commit=data.get("commit"),
            )
        except (KeyError, ValueError):
            return None


class PaperFetcher:
    def __init__(self, force_update: bool = False, debug: bool = False):
        self.force_update = force_update
        self.debug = debug  # Store debug flag
        self.setup_logging(debug)
        self.script_dir = Path(__file__).parent
        self.config_path = self.script_dir / "_paper_sources.yml"
        self.script_path = self.script_dir / "fetch_paper_template.sh"

    def setup_logging(self, debug: bool) -> None:
        """Configure logging with timestamps and appropriate level."""
        level = logging.DEBUG if debug else logging.INFO
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f"paper_fetch_{datetime.now():%Y%m%d}.log"),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def check_environment(self) -> PaperResult:
        """Check if required environment variables and dependencies are set."""
        try:
            if not os.getenv("QUARTO_PROJECT_RENDER_ALL"):
                raise EnvironmentError("QUARTO_PROJECT_RENDER_ALL must be set")

            # Check for required dependencies
            for dep in ["git", "yq"]:
                try:
                    subprocess.run(["which", dep], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    raise EnvironmentError(f"{dep} is not installed")

            return PaperResult(success=True)

        except Exception as e:
            return PaperResult(success=False, error=str(e))

    def verify_files(self) -> PaperResult:
        """Verify that required files exist."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    f"Configuration file {self.config_path} not found"
                )

            if not self.script_path.exists():
                raise FileNotFoundError(f"Template script {self.script_path} not found")

            return PaperResult(success=True)

        except Exception as e:
            return PaperResult(success=False, error=str(e))

    def load_paper_sources(self) -> List[PaperSource]:
        """Load and validate paper sources from YAML configuration."""
        valid_sources = []
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)

            if not config or "papers" not in config:
                self.logger.warning("No papers defined in configuration")
                return valid_sources

            for paper in config["papers"]:
                source = PaperSource.from_dict(paper)
                if source is not None:
                    valid_sources.append(source)
                else:
                    self.logger.warning(
                        f"Skipping invalid paper configuration: {paper}"
                    )

            return valid_sources

        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML configuration: {e}")
            return valid_sources

    def cleanup_paper_directory(self, paper_source: PaperSource) -> None:
        """Clean up paper directory in case of failure."""
        try:
            # Define paths to clean up
            paper_dir = Path("research/papers") / paper_source.target_folder
            freeze_dir = Path("_freeze/research/papers") / paper_source.target_folder

            # Remove directories if they exist
            if paper_dir.exists():
                self.logger.debug(f"Cleaning up paper directory: {paper_dir}")
                shutil.rmtree(paper_dir)

            if freeze_dir.exists():
                self.logger.debug(f"Cleaning up freeze directory: {freeze_dir}")
                shutil.rmtree(freeze_dir)

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def ensure_script_executable(self) -> PaperResult:
        """Ensure the fetch script has executable permissions."""
        try:
            current_mode = self.script_path.stat().st_mode
            executable_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            self.script_path.chmod(executable_mode)
            return PaperResult(success=True)
        except Exception as e:
            return PaperResult(
                success=False, error=f"Failed to set script permissions: {e}"
            )

    def run_fetch_script(self, paper_source: PaperSource) -> PaperResult:
        """Run the fetch script with error handling and logging."""
        self.logger.info(f"Fetching paper from {paper_source.repo_url}")

        env = os.environ.copy()
        env.update(
            {
                "PAPER_REPO_URL": paper_source.repo_url,
                "PAPER_TARGET_FOLDER": paper_source.target_folder,
                "PAPER_FORCE_UPDATE": str(self.force_update).lower(),
                "PAPER_BRANCH": paper_source.branch or "",
                "PAPER_COMMIT": paper_source.commit or "",
                "PAPER_DEBUG": str(
                    self.debug
                ).lower(),  # Pass debug flag to bash script
            }
        )

        try:
            result = subprocess.run(
                [str(self.script_path)],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            # Log bash script output based on debug level
            if self.debug:
                self.logger.debug(f"Bash script stdout:\n{result.stdout}")
            else:
                self.logger.info(result.stdout)

            return PaperResult(success=True)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error fetching paper: {e}")
            self.logger.debug(f"Bash script stdout:\n{e.stdout}")
            self.logger.debug(f"Bash script stderr:\n{e.stderr}")
            return PaperResult(
                success=False, error=f"Failed to fetch paper: {e}", cleanup_needed=True
            )

    def process_paper(self, paper_source: PaperSource) -> bool:
        """Process a single paper with error handling and cleanup."""
        self.logger.info(f"Processing paper from {paper_source.repo_url}")

        try:
            result = self.run_fetch_script(paper_source)

            if not result.success:
                self.logger.error(f"Failed to process paper: {result.error}")
                if result.cleanup_needed:
                    self.cleanup_paper_directory(paper_source)
                return False

            self.logger.info(f"Successfully processed {paper_source.repo_url}")
            return True

        except Exception as e:
            self.logger.error(f"Unexpected error processing paper: {e}")
            self.cleanup_paper_directory(paper_source)
            return False

    def fetch_papers(self) -> None:
        """Main method to fetch all papers."""
        if not self.force_update:
            env_check = self.check_environment()
            if not env_check.success:
                self.logger.error(f"Environment check failed: {env_check.error}")
                return

        files_check = self.verify_files()
        if not files_check.success:
            self.logger.error(f"File verification failed: {files_check.error}")
            return

        script_check = self.ensure_script_executable()
        if not script_check.success:
            self.logger.error(f"Script preparation failed: {script_check.error}")
            return

        paper_sources = self.load_paper_sources()
        if not paper_sources:
            self.logger.warning("No valid papers to process")
            return

        self.logger.info(f"Found {len(paper_sources)} papers to process")

        successful_papers = 0
        failed_papers = 0

        for paper_source in paper_sources:
            if self.process_paper(paper_source):
                successful_papers += 1
            else:
                failed_papers += 1

        self.logger.info(
            f"Processing complete. Successful: {successful_papers}, Failed: {failed_papers}"
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch papers for Quarto website")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force update regardless of commit hash",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        fetcher = PaperFetcher(force_update=args.force, debug=args.debug)
        fetcher.fetch_papers()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
