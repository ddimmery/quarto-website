"""Report papers.yaml entries added since the last commit.

Run after `quarto render research.qmd` re-executes the Semantic Scholar sync
(see `make papers`). New entries land with `visible: false`, so they need a
manual opt-in before they appear on the Research page.
"""

import subprocess
import sys

import yaml

YAML_FILE = "papers.yaml"

GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


def committed_entries():
    """Load papers.yaml as of HEAD; empty dict if unavailable."""
    try:
        blob = subprocess.run(
            ["git", "show", f"HEAD:{YAML_FILE}"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    return yaml.safe_load(blob) or {}


def main():
    with open(YAML_FILE) as f:
        current = yaml.safe_load(f) or {}

    old = committed_entries()
    added = {k: v for k, v in current.items() if k not in old}

    if not added:
        print(f"  {DIM}No new papers ({len(current)} entries){RESET}")
        return 0

    print(f"  {GREEN}{len(added)} new paper(s){RESET} "
          f"{DIM}({len(old)} -> {len(current)} entries){RESET}\n")

    for key, data in added.items():
        year = data.get("year") or "n.d."
        print(f"  {GREEN}{year}{RESET}  {data.get('title', 'Untitled')}")
        if data.get("venue"):
            print(f"        {DIM}{data['venue']}{RESET}")
        for field in ("published_url", "preprint", "pdf_url"):
            if data.get(field):
                print(f"        {DIM}{field}: {data[field]}{RESET}")
        state = "visible" if data.get("visible") else "hidden"
        print(f"        {DIM}key: {key}  ({state}){RESET}\n")

    hidden = [k for k, v in added.items() if not v.get("visible")]
    if hidden:
        print(f"  {YELLOW}Set `visible: true` in {YAML_FILE} to publish, "
              f"then re-run `make papers`.{RESET}")
        print(f"  {DIM}Semantic Scholar also returns false positives - "
              f"leave those hidden.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
