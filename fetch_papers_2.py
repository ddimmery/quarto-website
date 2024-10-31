#!/usr/bin/env python3

import tempfile
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Set, Optional, List
import yaml
from loguru import logger
import sys
from datetime import datetime

# Configure loguru
def setup_logging(debug: bool = False):
    """Configure loguru logger with file and console outputs."""
    # Remove default handler
    logger.remove()
    
    # Add colored stderr handler
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Set debug level for console if requested
    logger_level = "DEBUG" if debug else "INFO"
    logger.add(sys.stderr, format=log_format, level=logger_level, colorize=True)
    
    # Add file handler with more detailed format
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    log_file = f"paper_fetch_{datetime.now():%Y%m%d_%H%M%S}.log"
    logger.add(log_file, format=file_format, level="DEBUG", rotation="100 MB")

@dataclass
class Paper:
    """Paper source configuration."""
    repo_url: str
    target_folder: str
    branch: Optional[str] = None
    commit: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Optional["Paper"]:
        return cls(**data) if all(k in data for k in ("repo_url", "target_folder")) else None

class QuartoProject:
    """Analyzes and processes Quarto projects."""
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.config = self._load_config()
        self.project_type = self._determine_project_type()
        self.main_doc = self._find_main_doc()
        logger.debug(f"Initialized QuartoProject: type={self.project_type}, main_doc={self.main_doc}")
        
    def _load_config(self) -> dict:
        config_path = self.repo_dir / "_quarto.yml"
        if config_path.exists():
            config = yaml.safe_load(config_path.read_text())
            logger.debug(f"Loaded Quarto config:\n{yaml.dump(config, indent=2)}")
            return config
        logger.warning("No _quarto.yml found, using empty config")
        return {}

    def _determine_project_type(self) -> str:
        """Determine if this is a manuscript or default project."""
        project_type = "manuscript" if "manuscript" in self.config else "default"
        logger.debug(f"Determined project type: {project_type}")
        return project_type

    def get_files(self) -> Dict[str, Set[Path]]:
        """Get required project files based on project type."""
        logger.debug("Starting file collection process")
        
        standard_files = {
            Path("_quarto.yml"),
            self.main_doc,
            *self._get_bibliography_files(),
            *self._get_notebooks(),
            *self._get_support_directories()
        }
        
        freeze_files = self._get_freeze_directories()
        
        # Log files in a structured way
        logger.debug("Collected files:")
        logger.debug("Standard files:")
        for f in sorted(standard_files):
            logger.debug(f"  └── {f}")
        logger.debug("Freeze files:")
        for f in sorted(freeze_files):
            logger.debug(f"  └── {f}")
        
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
                logger.success(f"Using first found {ext} file as main document: {main_doc}")
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
        
        return bib_files

    def _get_notebooks(self) -> Set[Path]:
        """Get notebooks based on project type."""
        logger.debug(f"Collecting notebooks for {self.project_type} project")
        notebooks = set()
        
        if self.project_type == "manuscript":
            # Get notebooks from manuscript config
            config_notebooks = self.config.get("manuscript", {}).get("notebooks", [])
            if config_notebooks:
                logger.info("Found notebooks in manuscript config:")
                for nb in config_notebooks:
                    logger.info(f"  └── {nb}")
                notebooks.update(Path(nb) for nb in config_notebooks)
            
            # Look for embedded notebooks in main document
            main_doc_path = self.repo_dir / self.main_doc
            if main_doc_path.exists():
                content = main_doc_path.read_text()
                embedded_notebooks = []
                for line in content.split("\n"):
                    if "embed notebooks/" in line:
                        nb_path = line.split("notebooks/")[1].split("#")[0].strip()
                        embedded_notebooks.append(nb_path)
                        notebooks.add(Path("notebooks") / nb_path)
                if embedded_notebooks:
                    logger.info("Found embedded notebooks:")
                    for nb in embedded_notebooks:
                        logger.info(f"  └── notebooks/{nb}")
        else:
            # For default projects, include all notebooks
            found_notebooks = self._find_files("**/*.ipynb")
            if found_notebooks:
                logger.info("Found notebooks in filesystem:")
                for nb in found_notebooks:
                    logger.info(f"  └── {nb}")
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
                    if p.is_dir() and not any(part.startswith("_") for part in p.parts[1:])
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

    @logger.catch
    def process(self, paper: Paper) -> bool:
        """Process a single paper."""
        logger.info(f"Processing paper: {paper.target_folder}")
        logger.debug(f"Repository URL: {paper.repo_url}")
        logger.debug(f"Branch: {paper.branch}")
        logger.debug(f"Commit: {paper.commit}")
        
        paper_dir = Path("research/papers") / paper.target_folder
        commit_file = paper_dir / "last_commit.txt"

        try:
            # Get latest commit
            ref = paper.commit or f"refs/heads/{paper.branch}" if paper.branch else "HEAD"
            logger.debug(f"Getting latest commit for ref: {ref}")
            latest_commit = self._get_commit(paper.repo_url, ref)
            logger.debug(f"Latest commit: {latest_commit}")

            # Check if update needed
            if not self.force_update and commit_file.exists():
                current_commit = commit_file.read_text().strip()
                if current_commit == latest_commit:
                    logger.success(f"Paper {paper.target_folder} is up to date (commit: {current_commit})")
                    return True
                logger.info(f"Update needed: current={current_commit}, latest={latest_commit}")

            # Process paper
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                logger.debug(f"Created temporary directory: {temp_path}")
                
                self._clone_repo(paper, temp_path)
                self._copy_files(temp_path, paper_dir, paper.target_folder)
                
                commit_file.parent.mkdir(parents=True, exist_ok=True)
                commit_file.write_text(latest_commit)
                logger.debug(f"Updated commit file: {commit_file}")

            logger.success(f"Successfully processed paper {paper.target_folder}")
            return True

        except Exception as e:
            logger.exception(f"Failed to process {paper.repo_url}: {e}")
            self._cleanup(paper_dir)
            return False

    @logger.catch
    def _get_commit(self, repo_url: str, ref: str) -> str:
        """Get commit hash."""
        result = subprocess.run(
            ["git", "ls-remote", repo_url, ref],
            capture_output=True, text=True, check=True
        )
        if not result.stdout:
            raise ValueError(f"No commit found for ref: {ref}")
        return result.stdout.split()[0]

    @logger.catch
    def _clone_repo(self, paper: Paper, path: Path) -> None:
        """Clone repository."""
        logger.info(f"Cloning repository: {paper.repo_url}")
        cmd = ["git", "clone", "--quiet", "--depth", "1"]
        if paper.branch:
            cmd.extend(["--branch", paper.branch])
        cmd.extend([paper.repo_url, str(path)])
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        if paper.commit:
            logger.info(f"Checking out specific commit: {paper.commit}")
            subprocess.run(
                ["git", "checkout", "-q", paper.commit],
                check=True, capture_output=True, cwd=path
            )

    @logger.catch
    def _copy_files(self, source: Path, target: Path, folder: str) -> None:
        """Copy files to target directory."""
        logger.info(f"Starting file copy from {source} to {target}")
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
                    logger.info(f"  └── Copied file: {item}")
                else:
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    logger.info(f"  └── Copied directory: {item}")
            else:
                logger.warning(f"Source file not found: {src}")

        # Copy freeze files to special location
        logger.info("Copying freeze files:")
        for freeze_dir in files["freeze"]:
            src = source / freeze_dir
            dst = Path("_freeze/research/papers") / folder / freeze_dir.name
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst, dirs_exist_ok=True)
                logger.info(f"  └── Copied freeze directory: {freeze_dir} to {dst}")
            else:
                logger.warning(f"Source freeze directory not found: {src}")

    def _cleanup(self, path: Path) -> None:
        """Clean up on failure."""
        logger.warning(f"Cleaning up failed paper directory: {path}")
        for p in [path, Path("_freeze/research/papers") / path.name]:
            if p.exists():
                shutil.rmtree(p)
                logger.debug(f"Removed directory: {p}")

# Previous code remains the same until the main() function...

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch Quarto papers")
    parser.add_argument("--force", "-f", action="store_true", help="Force update")
    parser.add_argument("--config", type=Path, default=Path("research/_paper_sources.yml"))
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Setup logging with loguru
    setup_logging(debug=args.debug)

    # Log startup information
    logger.info("Starting paper fetcher")
    logger.debug("Arguments: {}", args)

    # Load and process papers
    try:
        config = yaml.safe_load(args.config.read_text())
        logger.debug("Loaded config:\n{}", yaml.dump(config, indent=2))
        
        papers = [p for p in map(Paper.from_dict, config.get("papers", [])) if p]
        logger.info("Found {} valid papers in config", len(papers))
        
        if not papers:
            logger.warning("No valid papers found")
            return 1

        manager = PaperManager(force_update=args.force)
        
        # Process papers and collect results
        results = []
        for paper in papers:
            logger.info("=" * 80)
            logger.info("Processing paper: {}", paper.target_folder)
            results.append(manager.process(paper))
        
        # Log summary
        success_count = sum(results)
        total_count = len(results)
        if success_count == total_count:
            logger.success("All papers processed successfully ({}/{})", success_count, total_count)
        else:
            logger.warning("Processed {}/{} papers successfully", success_count, total_count)
            failed_papers = [p.target_folder for p, r in zip(papers, results) if not r]
            logger.warning("Failed papers: {}", ", ".join(failed_papers))
        
        return 0 if all(results) else 1

    except Exception as e:
        logger.exception("Unexpected error: {}", e)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())