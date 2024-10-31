#!/usr/bin/env python3

import sys
import logging
import tempfile
import subprocess
import shutil
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
import yaml
from datetime import datetime


@dataclass
class PaperSource:
    """Configuration for a paper source."""

    repo_url: str
    target_folder: str
    branch: Optional[str] = None
    commit: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Optional["PaperSource"]:
        """Create a PaperSource from a dictionary, returning None if invalid."""
        if not all(k in data for k in ("repo_url", "target_folder")):
            return None
        try:
            return cls(
                repo_url=data["repo_url"],
                target_folder=data["target_folder"],
                branch=data.get("branch"),
                commit=data.get("commit"),
            )
        except (KeyError, TypeError):
            return None


@dataclass
class PaperContext:
    """Stores context information for paper processing."""

    temp_dir: Path
    paper_dir: Path
    last_commit_file: Path
    latest_commit: str
    repo_url: str
    target_folder: str
    branch: Optional[str] = None
    commit: Optional[str] = None


@dataclass
class QuartoProject:
    """Represents the structure of a Quarto project based on its configuration."""

    project_type: str
    main_document: Path
    notebooks: List[Path]
    bibliography: Set[Path]
    output_dir: Path
    additional_files: Set[Path]


class QuartoAnalyzer:
    """Analyzes Quarto project configuration to determine required files."""

    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.quarto_config = self._load_quarto_config()
        self.main_document = self._find_main_document()
        self.project_type = self.quarto_config.get("project", {}).get("type", "default")

    def _load_quarto_config(self) -> Dict:
        """Load and parse _quarto.yml configuration."""
        config_path = self.repo_dir / "_quarto.yml"
        if not config_path.exists():
            raise FileNotFoundError("No _quarto.yml found in repository")

        with open(config_path) as f:
            return yaml.safe_load(f)

    def _find_main_document(self) -> Path:
        """Find the main document based on project configuration or file search."""
        # First try _quarto.yml configuration
        if "manuscript" in self.quarto_config:
            article = self.quarto_config["manuscript"].get("article")
            if article:
                return Path(article)

        # Then try project root for common main document names
        for name in ["index.qmd", "paper.qmd", "manuscript.qmd"]:
            if (self.repo_dir / name).exists():
                return Path(name)

        # Finally, search for any .qmd or .ipynb files
        for ext in ["qmd", "ipynb"]:
            files = list(self.repo_dir.glob(f"*.{ext}"))
            if files:
                return files[0].relative_to(self.repo_dir)

        raise FileNotFoundError("Could not find main document")

    def _get_notebooks(self) -> List[Path]:
        """Get list of notebook files referenced in the project."""
        notebooks = []

        # Check manuscript notebooks configuration
        if "manuscript" in self.quarto_config:
            manuscript_notebooks = self.quarto_config["manuscript"].get("notebooks", [])
            notebooks.extend(Path(nb) for nb in manuscript_notebooks)

        # Look for embedded notebook references in main document
        main_doc_path = self.repo_dir / self.main_document
        if main_doc_path.exists():
            with open(main_doc_path) as f:
                content = f.read()
                # Look for notebook embed patterns
                for line in content.split("\n"):
                    if "embed notebooks/" in line:
                        nb_path = line.split("notebooks/")[1].split("#")[0].strip()
                        notebooks.append(Path("notebooks") / nb_path)

        return notebooks

    def _get_bibliography(self) -> Set[Path]:
        """
        Get bibliography files from both config and filesystem.
        Returns a set of bibliography file paths.
        """
        bib_files = set()

        # Check quarto.yml configuration
        if "bibliography" in self.quarto_config:
            bib_files.add(Path(self.quarto_config["bibliography"]))

        # Search for any .bib files in the root directory
        for bib_file in self.repo_dir.glob("*.bib"):
            bib_files.add(bib_file.relative_to(self.repo_dir))

        return bib_files

    def _get_output_dir(self) -> Path:
        """Get output directory configuration."""
        if "project" in self.quarto_config:
            return Path(self.quarto_config["project"].get("output-dir", "paper"))
        return Path("_site")

    def _find_freeze_directories(self) -> Set[Path]:
        """Find freeze directories that need to be copied."""
        freeze_dirs = set()
        base_name = self.main_document.stem

        # Check for freeze directory
        freeze_source = self.repo_dir / "_freeze" / base_name
        if freeze_source.exists():
            # We don't add the full path to required_files because it needs special handling
            # during copying to maintain the correct target structure
            freeze_dirs.add(Path("_freeze") / base_name)

        return freeze_dirs

    def _find_additional_files(self) -> Set[Path]:
        """Find additional required files based on project structure."""
        additional = set()

        # Always include figures directory if it exists
        figures_dir = self.repo_dir / "figures"
        if figures_dir.exists():
            additional.add(Path("figures"))

        # Add support directories
        for support_dir in ["_tex"]:
            if (self.repo_dir / support_dir).exists():
                additional.add(Path(support_dir))

        return additional

    def analyze_project(self) -> QuartoProject:
        """Analyze the Quarto project and return its structure."""
        return QuartoProject(
            project_type=self.project_type,
            main_document=self.main_document,
            notebooks=self._get_notebooks(),
            bibliography=self._get_bibliography(),
            output_dir=self._get_output_dir(),
            additional_files=self._find_additional_files(),
        )

    def get_required_files(self) -> Dict[str, Set[Path]]:
        """
        Get sets of files required for the project.
        Returns a dictionary with 'standard' and 'freeze' keys for different handling.
        """
        standard_files = {
            Path("_quarto.yml"),
            self.main_document,
            *self._get_notebooks(),
            *self._find_additional_files(),
            *self._get_bibliography(),  # Now returns a set of all found .bib files
        }

        return {"standard": standard_files, "freeze": self._find_freeze_directories()}


class PaperProcessor:
    """Handles the fetching and processing of individual papers."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.logger = logging.getLogger(__name__)

    def validate_environment(self, repo_url: str, target_folder: str) -> None:
        """Validate required environment and commands."""
        if not repo_url or not target_folder:
            raise ValueError("Missing required parameters: repo_url and target_folder")

        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise EnvironmentError("Git is not installed or not accessible")

    def get_repo_info(self, context: PaperContext) -> str:
        """Get the latest commit hash for the specified reference."""
        ref = (
            context.commit or f"refs/heads/{context.branch}"
            if context.branch
            else "HEAD"
        )

        try:
            result = subprocess.run(
                ["git", "ls-remote", context.repo_url, ref],
                check=True,
                capture_output=True,
                text=True,
            )
            commit_hash = result.stdout.split()[0]
            if not commit_hash:
                raise ValueError(f"No commit hash found for ref: {ref}")
            return commit_hash

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to fetch commit hash: {e.stderr}")

    def prepare_repository(self, context: PaperContext) -> None:
        """Clone and prepare the repository."""
        clone_opts = ["--quiet", "--depth", "1"]
        if context.branch:
            clone_opts.extend(["--branch", context.branch])

        try:
            subprocess.run(
                ["git", "clone"]
                + clone_opts
                + [context.repo_url, str(context.temp_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

            if context.commit:
                subprocess.run(
                    ["git", "checkout", "-q", context.commit],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=context.temp_dir,
                )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to prepare repository: {e.stderr}")

    def copy_files(self, context: PaperContext) -> None:
        """Copy required files to target directory based on Quarto project structure."""
        source_dir = context.temp_dir
        paper_dir = context.paper_dir

        try:
            # Analyze Quarto project and get required files
            analyzer = QuartoAnalyzer(source_dir)
            required_files = analyzer.get_required_files()

            # Create paper directory
            paper_dir.mkdir(parents=True, exist_ok=True)

            # Copy standard files and directories
            for item in required_files["standard"]:
                source = source_dir / item
                target = paper_dir / item

                if not source.exists():
                    self.logger.warning(f"Required file/directory not found: {item}")
                    continue

                if source.is_file():
                    # Ensure parent directories exist
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                else:
                    # Copy directory recursively
                    shutil.copytree(source, target, dirs_exist_ok=True)

            # Handle freeze directories separately
            for freeze_dir in required_files["freeze"]:
                source = source_dir / freeze_dir
                # Note the special handling of the target path to match the bash script
                target = (
                    Path("_freeze/research/papers")
                    / context.target_folder
                    / freeze_dir.name
                )

                if source.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(source, target, dirs_exist_ok=True)

            self.logger.info(
                f"Copied {len(required_files['standard'])} standard files/directories "
                f"and {len(required_files['freeze'])} freeze directories"
            )

        except Exception as e:
            raise RuntimeError(f"Failed to copy files: {e}")

    def process(
        self,
        repo_url: str,
        target_folder: str,
        force_update: bool = False,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
    ) -> bool:
        """Process a single paper."""
        try:
            self.validate_environment(repo_url, target_folder)

            with tempfile.TemporaryDirectory() as temp_dir:
                context = PaperContext(
                    temp_dir=Path(temp_dir),
                    paper_dir=Path("research/papers") / target_folder,
                    last_commit_file=Path("research/papers")
                    / target_folder
                    / "last_commit.txt",
                    latest_commit="",  # Will be set after getting repo info
                    repo_url=repo_url,
                    target_folder=target_folder,
                    branch=branch,
                    commit=commit,
                )

                # Get repository information
                context.latest_commit = self.get_repo_info(context)

                # Check if update is needed
                if not force_update and context.last_commit_file.exists():
                    if (
                        context.last_commit_file.read_text().strip()
                        == context.latest_commit
                    ):
                        self.logger.info("Paper is up-to-date")
                        return True

                # Prepare repository
                self.prepare_repository(context)

                # Copy files using new method
                self.copy_files(context)

                # Save commit hash
                context.last_commit_file.parent.mkdir(parents=True, exist_ok=True)
                context.last_commit_file.write_text(context.latest_commit)

                self.logger.info("Paper successfully processed")
                return True

        except Exception as e:
            self.logger.error(f"Failed to process paper: {e}")
            self._cleanup_on_failure(target_folder)
            return False

    def _cleanup_on_failure(self, target_folder: str) -> None:
        """Clean up directories on failure."""
        try:
            for path in [
                Path("research/papers") / target_folder,
                Path("_freeze/research/papers") / target_folder,
            ]:
                if path.exists():
                    shutil.rmtree(path)
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


class PaperFetcher:
    """Orchestrates the fetching of multiple papers."""

    def __init__(self, force_update: bool = False, debug: bool = False):
        self.force_update = force_update
        self.debug = debug
        self.setup_logging()
        self.processor = PaperProcessor(debug=debug)
        self.script_dir = Path(__file__).parent

    def setup_logging(self) -> None:
        """Set up logging configuration."""
        level = logging.DEBUG if self.debug else logging.INFO
        handlers = [
            logging.StreamHandler(),
            logging.FileHandler(f"paper_fetch_{datetime.now():%Y%m%d}.log"),
        ]
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=handlers,
        )
        self.logger = logging.getLogger(__name__)

    def load_papers(self) -> List[PaperSource]:
        """Load paper configurations from YAML file."""
        config_path = self.script_dir / "research/_paper_sources.yml"
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            sources = []
            for paper in config.get("papers", []):
                if source := PaperSource.from_dict(paper):
                    sources.append(source)
                else:
                    self.logger.warning(f"Invalid paper configuration: {paper}")
            return sources

        except Exception as e:
            self.logger.error(f"Failed to load paper sources: {e}")
            return []

    def process_paper(self, paper: PaperSource) -> bool:
        """Process a single paper."""
        self.logger.info(f"Processing {paper.repo_url}")
        return self.processor.process(
            repo_url=paper.repo_url,
            target_folder=paper.target_folder,
            force_update=self.force_update,
            branch=paper.branch,
            commit=paper.commit,
        )

    def fetch_papers(self) -> bool:
        """Fetch all configured papers."""
        papers = self.load_papers()
        if not papers:
            self.logger.warning("No valid papers to process")
            return False

        successful = 0
        failed = 0

        for paper in papers:
            if self.process_paper(paper):
                successful += 1
            else:
                failed += 1

        self.logger.info(
            f"Processing complete. Successful: {successful}, Failed: {failed}"
        )
        return failed == 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch and update Quarto papers from Git repositories"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force update all papers regardless of their current state",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to paper sources configuration file (default: research/_paper_sources.yml)",
        default=Path("research/_paper_sources.yml"),
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()

    try:
        fetcher = PaperFetcher(force_update=args.force, debug=args.debug)
        success = fetcher.fetch_papers()
        return 0 if success else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
