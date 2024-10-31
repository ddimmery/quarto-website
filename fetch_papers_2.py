#!/usr/bin/env python3

import tempfile
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Set, Optional
import argparse
import yaml
from loguru import logger
import sys


# Configure loguru
def setup_logging(console_level: str = "SUCCESS"):
    """Configure loguru logger with enhanced stage visualization and basic rotation."""
    # Remove default handler
    logger.remove()

    # Initialize formatters
    console_formatter = ConsoleFormatter()
    file_formatter = FileFormatter()

    # Configure logger with context
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": console_formatter.format,
                "level": console_level,
                "colorize": True,
            },
            {
                "sink": "paper_fetch.log",
                "format": file_formatter.format,
                "level": "DEBUG",
                "rotation": "1 MB",
                "enqueue": True,
            },
        ]
    )
    global console_level_setting
    console_level_setting = console_level

class ConsoleFormatter:
    """Formatter for console output with dynamic padding for aligned stages."""
    def __init__(self):
        self.fmt = (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "{extra[padding]}<level>{message}</level>\n"
            "{exception}"
        )

    def format(self, record):
        if "padding" not in record["extra"]:
            record["extra"]["padding"] = ""
        return self.fmt


class FileFormatter:
    """Formatter for file output with dynamic metadata padding for alignment."""
    def __init__(self):
        self.padding = 0
        self.fmt = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line}{extra[padding]} | "
            "{message}\n"
            "{exception}"
        )

    def format(self, record):
        # Calculate required padding based on metadata length
        metadata_length = len(f"{record['name']}:{record['function']}:{record['line']}")
        self.padding = max(self.padding, metadata_length)
        record["extra"]["padding"] = " " * (self.padding - metadata_length)
        return self.fmt


def stage(name: str):
    """Decorator to mark and log processing stages."""

    def decorator(func):
        @logger.catch
        def wrapper(*args, **kwargs):
            # Create stage header
            stage_header = f" STAGE: {name} "
            padding = "═" * (40 - len(stage_header) // 2)

            # Log stage start
            with logger.contextualize(padding=""):
                logger.info(f"{padding}{stage_header}{padding}")

            # Execute function with indented logging
            with logger.contextualize(padding=""):
                result = func(*args, **kwargs)

            # Log stage completion
            with logger.contextualize(padding=""):
                logger.info(f"{'═' * (len(stage_header) + 2 * len(padding))}\n")

            return result

        return wrapper

    return decorator


def substage(name: str):
    """Decorator to mark and log processing substages."""

    def decorator(func):
        @logger.catch
        def wrapper(*args, **kwargs):
            # Log substage header with consistent indentation
            with logger.contextualize(padding=""):
                logger.info(f"▶ {name}")

            # Execute function with additional indentation
            if console_level_setting == "SUCCESS":
                result = func(*args, **kwargs)
            else:
                with logger.contextualize(padding="  "):
                    result = func(*args, **kwargs)

            return result

        return wrapper

    return decorator


@dataclass
class Paper:
    """Paper source configuration."""

    repo_url: str
    target_folder: str
    branch: Optional[str] = None
    commit: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Optional["Paper"]:
        return (
            cls(**data)
            if all(k in data for k in ("repo_url", "target_folder"))
            else None
        )


class QuartoProject:
    """Analyzes and processes Quarto projects."""

    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.config = self._load_config()
        self.project_type = self._determine_project_type()
        self.main_doc = self._find_main_doc()
        logger.debug(
            "Initialized QuartoProject: type={}, main_doc={}",
            self.project_type,
            self.main_doc,
        )

    @substage("Loading Quarto configuration")
    def _load_config(self) -> dict:
        config_path = self.repo_dir / "_quarto.yml"
        if config_path.exists():
            config = yaml.safe_load(config_path.read_text())
            logger.debug("Loaded config:\n{}", yaml.dump(config, indent=2))
            return config
        logger.warning("No _quarto.yml found, using empty config")
        return {}

    def _determine_project_type(self) -> str:
        """Determine if this is a manuscript or default project."""
        project_type = "manuscript" if "manuscript" in self.config else "default"
        logger.debug(f"Determined project type: {project_type}")
        return project_type

    @substage("Analyzing project structure")
    def get_files(self) -> Dict[str, Set[Path]]:
        """Get required project files based on project type."""
        standard_files = {
            Path("_quarto.yml"),
            self.main_doc,
            *self._get_bibliography_files(),
            *self._get_notebooks(),
            *self._get_support_directories(),
        }

        freeze_files = self._get_freeze_directories()

        # Log files in a structured way
        logger.info("📁 Collected files:")
        logger.info("└── 📄 Standard files:")
        for f in sorted(standard_files):
            logger.info("    └── {}", f)
        logger.info("└── 🧊 Freeze files:")
        for f in sorted(freeze_files):
            logger.info("    └── {}", f)

        return {"standard": standard_files, "freeze": freeze_files}

    @logger.catch(message="Error finding main document")
    def _find_main_doc(self) -> Path:
        """Find main document based on project type."""
        logger.debug("Searching for main document")

        # Check manuscript configuration
        if self.project_type == "manuscript":
            if article := self.config.get("manuscript", {}).get("article"):
                logger.success(f"Found main document in manuscript config: {article}")
                return Path(article)

        # Check common names
        for name in ["index.qmd", "paper.qmd", "manuscript.qmd"]:
            if (self.repo_dir / name).exists():
                logger.success(f"Found main document with common name: {name}")
                return Path(name)

        # Take first .qmd or .ipynb file
        for ext in ["qmd", "ipynb"]:
            if files := list(self.repo_dir.glob(f"*.{ext}")):
                main_doc = files[0].relative_to(self.repo_dir)
                logger.success(
                    f"Using first found {ext} file as main document: {main_doc}"
                )
                return main_doc

        raise FileNotFoundError("No main document found")

    def _get_bibliography_files(self) -> Set[Path]:
        """Get bibliography files from both config and filesystem."""
        logger.debug("Collecting bibliography files")
        bib_files = set()

        # Check config
        if bib_path := self.config.get("bibliography"):
            logger.info(f"Found bibliography in config: {bib_path}")
            bib_files.add(Path(bib_path))

        # Find all .bib files
        filesystem_bibs = self._find_files("*.bib")
        if filesystem_bibs:
            logger.info("Found bibliography files in filesystem:")
            for bib in filesystem_bibs:
                logger.info(f"  └── {bib}")
            bib_files.update(filesystem_bibs)

        if len(bib_files) == 0:
            logger.warning("✖ No bibliography files found.")

        return bib_files

    def _get_notebooks(self) -> Set[Path]:
        """Get notebooks based on project type."""
        logger.debug("Collecting notebooks for {} project", self.project_type)
        notebooks = set()

        if self.project_type == "manuscript":
            # Get notebooks from manuscript config
            config_notebooks = self.config.get("manuscript", {}).get("notebooks", [])
            if config_notebooks:
                logger.info("Found notebooks in manuscript config:")
                for nb in config_notebooks:
                    logger.info("  └── {}", nb)
                notebooks.update(Path(nb) for nb in config_notebooks)

            # Look for embedded notebooks in main document
            main_doc_path = self.repo_dir / self.main_doc
            if main_doc_path.exists():
                content = main_doc_path.read_text()
                embedded_notebooks = {
                    line.split("notebooks/")[1].split("#")[0].strip()
                    for line in content.splitlines()
                    if "embed notebooks/" in line
                }

                if embedded_notebooks:
                    logger.info("Found embedded notebooks:")
                    for nb in sorted(embedded_notebooks):
                        logger.info("  └── notebooks/{}", nb)
                        notebooks.add(Path("notebooks") / nb)
        else:
            # For default projects, include all notebooks
            found_notebooks = self._find_files("**/*.ipynb")
            if found_notebooks:
                logger.info("Found notebooks in filesystem:")
                for nb in sorted(found_notebooks):
                    logger.info("  └── {}", nb)
                notebooks.update(found_notebooks)

        return notebooks

    def _get_support_directories(self) -> Set[Path]:
        """Get support directories based on project type."""
        logger.debug("Collecting support directories")
        # Common directories for both types
        dirs = {"figures", "_tex"}

        # Add notebooks directory for manuscript projects
        if self.project_type == "manuscript":
            dirs.add("notebooks")

        found_dirs = {Path(d) for d in dirs if (self.repo_dir / d).exists()}
        if found_dirs:
            logger.info("Found support directories:")
            for d in sorted(found_dirs):
                logger.info(f"  └── {d}")
        return found_dirs

    def _get_freeze_directories(self) -> Set[Path]:
        """Get freeze directories based on project type."""
        logger.debug(f"Collecting freeze directories for {self.project_type} project")
        freeze_dirs = set()
        freeze_base = self.repo_dir / "_freeze"

        if self.project_type == "default":
            # For default projects, check main document's freeze directory
            freeze_path = freeze_base / self.main_doc.stem
            if freeze_path.exists():
                freeze_dir = Path("_freeze") / self.main_doc.stem
                logger.success(f"Found default project freeze directory: {freeze_dir}")
                freeze_dirs.add(freeze_dir)
        else:
            # For manuscript projects, check all potential freeze directories
            if freeze_base.exists():
                found_dirs = [
                    Path("_freeze") / p.relative_to(freeze_base)
                    for p in freeze_base.glob("**/*")
                    if p.is_dir()
                    and not any(part.startswith("_") for part in p.parts[1:])
                ]
                if found_dirs:
                    logger.info("Found manuscript freeze directories:")
                    for d in sorted(found_dirs):
                        logger.info(f"  └── {d}")
                    freeze_dirs.update(found_dirs)

        return freeze_dirs

    def _find_files(self, pattern: str) -> Set[Path]:
        """Find files matching pattern."""
        return {f.relative_to(self.repo_dir) for f in self.repo_dir.glob(pattern)}


class PaperManager:
    """Manages paper fetching and processing."""

    def __init__(self, force_update: bool = False):
        self.force_update = force_update

    @stage("Paper Processing")
    def process(self, paper: Paper) -> bool:
        """Process a single paper."""
        logger.success("📑 Processing paper: {}", paper.target_folder)
        logger.debug("Repository URL: {}", paper.repo_url)
        logger.debug("Branch: {}", paper.branch)
        logger.debug("Commit: {}", paper.commit)

        paper_dir = Path("research/papers") / paper.target_folder
        commit_file = paper_dir / "last_commit.txt"

        try:
            # Get latest commit
            ref = (
                paper.commit or f"refs/heads/{paper.branch}" if paper.branch else "HEAD"
            )
            latest_commit = self._get_commit(paper.repo_url, ref)

            if self._check_if_updated(commit_file, latest_commit):
                return True

            # Process paper
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                self._clone_repo(paper, temp_path)
                self._copy_files(temp_path, paper_dir, paper.target_folder)
                self._save_commit(commit_file, latest_commit)

            logger.success("✨ Successfully processed paper {}", paper.target_folder)
            return True

        except Exception as e:
            logger.exception("❌ Failed to process {}: {}", paper.repo_url, e)
            self._cleanup(paper_dir)
            return False

    @substage("Checking repository status")
    def _check_if_updated(self, commit_file: Path, latest_commit: str) -> bool:
        """Check if paper needs updating."""
        if not self.force_update and commit_file.exists():
            current_commit = commit_file.read_text().strip()
            if current_commit == latest_commit:
                logger.success("✓ Paper is up to date (commit: {})", current_commit)
                return True
            logger.info(
                "⟳ Update needed: current={}, latest={}", current_commit, latest_commit
            )
        return False

    @logger.catch
    def _get_commit(self, repo_url: str, ref: str) -> str:
        """Get commit hash."""
        result = subprocess.run(
            ["git", "ls-remote", repo_url, ref],
            capture_output=True,
            text=True,
            check=True,
        )
        if not result.stdout:
            raise ValueError(f"No commit found for ref: {ref}")
        return result.stdout.split()[0]

    @substage("Saving commit information")
    def _save_commit(self, commit_file: Path, commit_hash: str) -> None:
        """Save the current commit hash to the commit file."""
        logger.info("💾 Saving commit hash: {}", commit_hash)
        commit_file.parent.mkdir(parents=True, exist_ok=True)
        commit_file.write_text(commit_hash)
        logger.debug("Commit hash saved to: {}", commit_file)

    @substage("Cloning repository")
    def _clone_repo(self, paper: Paper, path: Path) -> None:
        """Clone repository."""
        logger.info("📥 Cloning: {}", paper.repo_url)
        cmd = ["git", "clone", "--quiet", "--depth", "1"]
        if paper.branch:
            cmd.extend(["--branch", paper.branch])
        cmd.extend([paper.repo_url, str(path)])

        subprocess.run(cmd, check=True, capture_output=True)

        if paper.commit:
            logger.info(f"Checking out specific commit: {paper.commit}")
            subprocess.run(
                ["git", "checkout", "-q", paper.commit],
                check=True,
                capture_output=True,
                cwd=path,
            )

    @substage("Copying files")
    def _copy_files(self, source: Path, target: Path, folder: str) -> None:
        """Copy files to target directory."""
        logger.info("📋 Starting file copy")

        # Create QuartoProject instance once
        project = QuartoProject(source)
        files = project.get_files()

        # Copy standard files
        logger.info("Copying standard files:")
        target.mkdir(parents=True, exist_ok=True)
        for item in files["standard"]:
            src = source / item
            dst = target / item
            if src.exists():
                if src.is_file():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    logger.info("  └── Copied file: {}", item)
                else:
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    logger.info("  └── Copied directory: {}", item)
            else:
                logger.warning("Source file not found: {}", src)

        # Copy freeze files to special location
        if files["freeze"]:
            logger.info("Copying freeze files:")
            for freeze_dir in files["freeze"]:
                src = source / freeze_dir
                dst = Path("_freeze/research/papers") / folder / freeze_dir.name
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    logger.info(
                        "  └── Copied freeze directory: {} to {}", freeze_dir, dst
                    )
                else:
                    logger.warning("Source freeze directory not found: {}", src)

    def _cleanup(self, path: Path) -> None:
        """Clean up on failure."""
        logger.warning(f"Cleaning up failed paper directory: {path}")
        for p in [path, Path("_freeze/research/papers") / path.name]:
            if p.exists():
                shutil.rmtree(p)
                logger.debug(f"Removed directory: {p}")


def main():
    parser = argparse.ArgumentParser(description="Fetch Quarto papers")
    parser.add_argument("--force", "-f", action="store_true", help="Force update")
    parser.add_argument(
        "--config", type=Path, default=Path("research/_paper_sources.yml")
    )
    parser.add_argument(
        "--log-level",
        default="SUCCESS",
        help="Logging level",
        choices=["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR"],
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    # Determine log level without logging
    log_level = "DEBUG" if args.debug else args.log_level

    # Setup logging with loguru
    setup_logging(console_level=log_level)

    # Log startup with higher level and no extra padding
    with logger.contextualize(padding=""):
        logger.info(f"{'═' * 80}")
        logger.success("🚀 QUARTO PAPER FETCHER")
        logger.info(f"{'═' * 80}")

    try:
        config = yaml.safe_load(args.config.read_text())
        papers = [p for p in map(Paper.from_dict, config.get("papers", [])) if p]

        if not papers:
            logger.warning("No valid papers found")
            return 1

        manager = PaperManager(force_update=args.force)
        results = []

        # Process each paper
        for paper in papers:
            results.append(manager.process(paper))

        # Log summary with no extra padding
        success_count = sum(results)
        total_count = len(results)

        with logger.contextualize(padding=""):
            if success_count == total_count:
                logger.info(f"{'═' * 80}")
                logger.success(
                    f"✅ All papers processed successfully ({success_count}/{total_count})"
                )
                logger.info(f"{'═' * 80}")
            else:
                logger.warning(f"{'═' * 80}")
                logger.warning(
                    f"⚠️  Processed {success_count}/{total_count} papers successfully"
                )
                failed_papers = [
                    p.target_folder for p, r in zip(papers, results) if not r
                ]
                logger.warning(f"❌ Failed papers: {', '.join(failed_papers)}")
                logger.warning(f"{'═' * 80}")

        return 0 if all(results) else 1

    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
