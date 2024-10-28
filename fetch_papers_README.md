# Quarto Paper Fetcher

A tool for automatically fetching and incorporating pre-rendered Quarto papers from external Git repositories into a main Quarto website project.

## Functionality Overview

### Core Purpose

- Fetches Quarto papers from Git repositories
- Maintains proper directory structure for Quarto websites
- Updates content only when changes are detected
- Handles multiple papers independently
- Keeps track of paper versions using Git commit hashes

### Directory Structure

```
your-quarto-project/
├── research/papers/{PAPER_TARGET_FOLDER}/
│   ├── paper files (.qmd, .ipynb)
│   ├── figures/
│   ├── _tex/
│   └── references.bib
└── _freeze/research/papers/{PAPER_TARGET_FOLDER}/
    └── paper freeze files
```

## Configuration

### Paper Sources (`_paper_sources.yml`)

```yaml
papers:
  - repo_url: "https://github.com/user/paper-repo.git"
    target_folder: "paper_name"
    branch: "main"  # optional
    commit: "abc123"  # optional
```

### Environment Variables

- `QUARTO_PROJECT_RENDER_ALL`: Required for non-force updates
- `PAPER_DEBUG`: Set to "true" for detailed logging

## Usage

### Basic Usage

```bash
# Normal update
python fetch_papers.py

# Force update regardless of commit hash
python fetch_papers.py --force

# Enable debug logging
python fetch_papers.py --debug
```

### Integration with Quarto

Add to `_quarto.yml`:

```yaml
project:
  pre-render: "python fetch_papers.py"
```

## Maintenance Notes

### Dependencies

- Python 3.x
- Git
- yq (for YAML parsing)
- Quarto

### Key Files

1. `fetch_papers.py`: Python controller script

  - Manages multiple papers
  - Handles logging and error reporting
  - Coordinates paper fetching process

2. `fetch_paper_template.sh`: Bash script for paper fetching

  - Handles Git operations
  - Manages file copying
  - Maintains directory structure

3. `_paper_sources.yml`: Configuration file

  - Defines paper sources
  - Configures target locations

### Common Issues and Solutions

1. **Paper Not Updating**

  - Check if `QUARTO_PROJECT_RENDER_ALL` is set
  - Use `--force` flag to bypass commit check
  - Verify Git repository access

2. **Missing Files**

  - Ensure paper repository has required files
  - Check file permissions
  - Enable debug logging for detailed information

3. **Failed Papers**

  - Individual paper failures don't affect others
  - Check logs for specific error messages
  - Failed papers are cleaned up automatically

### Adding New Papers

1. Add entry to `_paper_sources.yml`:

  ```yaml
  papers:
    - repo_url: "https://github.com/user/new-paper.git"
      target_folder: "new_paper_name"
  ```

2. Ensure paper repository has:

  - Quarto source file (.qmd or .ipynb)
  - Required assets (figures, references)
  - Pre-rendered content

### Updating the Tool

When modifying the code:

1. Maintain current file copy behavior
2. Keep error handling and cleanup logic
3. Test with both valid and invalid papers
4. Verify directory structure remains correct
5. Check logging output is meaningful

### Testing

```bash
# Test single paper
python fetch_papers.py --debug

# Test force update
python fetch_papers.py --force

# Test multiple papers
# Add test papers to _paper_sources.yml and run
python fetch_papers.py
```

## Error Logs

Located at: `paper_fetch_YYYYMMDD.log`

- Contains detailed error messages
- Includes script outputs
- Shows paper processing status

Remember to check logs when troubleshooting issues or making modifications.
