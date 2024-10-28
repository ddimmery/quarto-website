#!/bin/bash

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# Initialize global variables
DEBUG=${PAPER_DEBUG:-false}
TEMP_DIR=""
PAPER_DIR=""
LAST_COMMIT_FILE=""
LATEST_COMMIT=""

# Define arrays with proper declarations
declare -a PAPER_EXTENSIONS=("quarto_ipynb" "ipynb" "qmd")
declare -a SUPPORT_DIRS=("figures" "_tex")

# Simplified logging with error context
log() {
    local level=$1
    local message=$2
    local context=${3:-}
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message"
    if [ -n "$context" ]; then
        echo "  Context: $context"
    fi
}

# Enhanced error handling
error_exit() {
    local message=$1
    local context=""
    
    # Build error context
    context="Current directory: $(pwd)"
    context+="\nPaper URL: $PAPER_REPO_URL"
    context+="\nTarget folder: $PAPER_TARGET_FOLDER"
    context+="\nTemp directory: ${TEMP_DIR:-not set}"
    context+="\nPaper directory: ${PAPER_DIR:-not set}"
    
    # Include git status if in repo
    if [ -d "$TEMP_DIR" ] && [ -d "$TEMP_DIR/.git" ]; then
        context+="\nGit status: $(cd "$TEMP_DIR" && git status 2>&1)"
    fi
    
    # Log the error with context
    log "ERROR" "$message" "$context"
    
    # Exit with error status
    exit 1
}

# Enhanced validation
validate_environment() {
    log "INFO" "Validating environment..."
    
    # Check required environment variables
    local required_vars=("PAPER_REPO_URL" "PAPER_TARGET_FOLDER")
    local missing=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing+=("$var")
        fi
    done
    if [ ${#missing[@]} -ne 0 ]; then
        error_exit "Missing required variables: ${missing[*]}"
    fi

    # Check required commands with specific feedback
    for cmd in git yq; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            error_exit "Required command not found: $cmd" "Please install $cmd before continuing"
        fi
    done
    
    log "INFO" "Environment validation successful"
}

# Enhanced repository info retrieval
get_repo_info() {
    local ref="HEAD"
    [ -n "${PAPER_COMMIT:-}" ] && ref="${PAPER_COMMIT}"
    [ -n "${PAPER_BRANCH:-}" ] && ref="refs/heads/${PAPER_BRANCH}"

    log "INFO" "Fetching repository info" "Using ref: $ref"
    
    # Try to get commit hash with better error handling
    LATEST_COMMIT=$(git ls-remote "$PAPER_REPO_URL" "$ref" 2>&1) || {
        error_exit "Failed to fetch commit hash" "Command output: $LATEST_COMMIT"
    }
    
    LATEST_COMMIT=$(echo "$LATEST_COMMIT" | cut -f1)
    
    if [ -z "$LATEST_COMMIT" ]; then
        error_exit "No commit hash found" "Ref: $ref, URL: $PAPER_REPO_URL"
    fi
    
    log "INFO" "Found commit hash: $LATEST_COMMIT"
}

# Enhanced repository preparation
prepare_repository() {
    log "INFO" "Preparing repository..."
    
    local clone_opts=("--quiet" "--depth" "1")
    [ -n "${PAPER_BRANCH:-}" ] && clone_opts+=("--branch" "${PAPER_BRANCH}")
    
    # Clone with better error capture
    local clone_output
    clone_output=$(git clone "${clone_opts[@]}" "$PAPER_REPO_URL" "$TEMP_DIR" 2>&1) || {
        error_exit "Failed to clone repository" "Command output: $clone_output"
    }

    if [ -n "${PAPER_COMMIT:-}" ]; then
        cd "$TEMP_DIR" || error_exit "Failed to change to temp directory" "Dir: $TEMP_DIR"
        local checkout_output
        checkout_output=$(git checkout -q "$PAPER_COMMIT" 2>&1) || {
            error_exit "Failed to checkout commit" "Command output: $checkout_output"
        }
    fi
    
    log "INFO" "Repository prepared successfully"
}

# Find the source file base name
find_base_name() {
    local dir=$1
    local base=""
    
    # Try _quarto.yml first
    if [ -f "$dir/_quarto.yml" ]; then
        base=$(yq ".manuscript.article" "$dir/_quarto.yml" | sed 's/\.qmd$//')
        [ "$base" != "null" ] && [ -n "$base" ] && echo "$base" && return 0
    fi
    
    # Fallback to finding files
    for ext in "qmd" "ipynb"; do
        for file in "$dir"/*."$ext"; do
            [ -f "$file" ] && basename "$file" ".$ext" && return 0
        done
    done
    
    return 1
}

# Copy files to target directories
copy_files() {
    local source_dir=$1
    local base_name=$2
    
    mkdir -p "$PAPER_DIR"
    
    # Copy main paper files
    for ext in "${PAPER_EXTENSIONS[@]}"; do
        [ -f "$source_dir/${base_name}.${ext}" ] && \
            cp "$source_dir/${base_name}.${ext}" "$PAPER_DIR/"
    done

    # Copy support files
    [ -f "$source_dir/references.bib" ] && cp "$source_dir/references.bib" "$PAPER_DIR/"
    
    # Copy support directories
    for dir in "${SUPPORT_DIRS[@]}"; do
        [ -d "$source_dir/$dir" ] && cp -r "$source_dir/$dir" "$PAPER_DIR/"
    done
    
    # Copy base-name specific directory
    [ -d "$source_dir/${base_name}_files" ] && \
        cp -r "$source_dir/${base_name}_files" "$PAPER_DIR/"
        
    # Handle freeze directory
    local freeze_source="$source_dir/_freeze/${base_name}"
    local freeze_target="_freeze/research/papers/${PAPER_TARGET_FOLDER}/${base_name}"
    
    if [ -d "$freeze_source" ]; then
        mkdir -p "$freeze_target"
        cp -r "$freeze_source"/* "$freeze_target/"
    fi
}

# Enhance main function with better error context
main() {
    log "INFO" "Starting paper fetch..."
    
    validate_environment
    
    PAPER_DIR="research/papers/${PAPER_TARGET_FOLDER}"
    LAST_COMMIT_FILE="$PAPER_DIR/last_commit.txt"
    
    # Create temp directory with error handling
    TEMP_DIR=$(mktemp -d) || error_exit "Failed to create temp directory"
    [ -d "$TEMP_DIR" ] || error_exit "Temp directory does not exist" "Dir: $TEMP_DIR"

    get_repo_info
    
    # Skip if up-to-date unless force update
    if [ "${PAPER_FORCE_UPDATE:-false}" != "true" ] && \
       [ -f "$LAST_COMMIT_FILE" ] && \
       [ "$(cat "$LAST_COMMIT_FILE")" = "$LATEST_COMMIT" ]; then
        log "INFO" "Paper is up-to-date"
        exit 0
    fi

    prepare_repository
    
    local base_name
    base_name=$(find_base_name "$TEMP_DIR") || {
        error_exit "Could not find paper source file" "Contents: $(ls -la "$TEMP_DIR")"
    }

    copy_files "$TEMP_DIR" "$base_name" || {
        error_exit "Failed to copy files" "Base name: $base_name"
    }
    
    echo "$LATEST_COMMIT" > "$LAST_COMMIT_FILE" || {
        error_exit "Failed to save commit hash" "File: $LAST_COMMIT_FILE"
    }
    
    log "INFO" "Paper successfully processed"
}

# Trap all errors for better debugging
trap 'error_exit "Script failed" "Line: $LINENO, Command: $BASH_COMMAND"' ERR

# Run main with error handling
main "$@"