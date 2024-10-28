#!/bin/bash

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# Initialize global variables
DEBUG=${PAPER_DEBUG:-false}
TEMP_DIR=""
ORIGINAL_DIR=""
PAPER_DIR=""
LAST_COMMIT_FILE=""
LATEST_COMMIT=""

# Function to log messages with timestamps
log() {
    local level="$1"
    local message="$2"
    local debug_info="${3:-}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[${timestamp}] [${level}] ${message}"
    
    if [ "$DEBUG" = "true" ] && [ -n "$debug_info" ]; then
        echo "DEBUG DETAILS:"
        echo "$debug_info"
        echo "---------------"
    fi
}

# Function to log errors and exit
error_exit() {
    local message="$1"
    local debug_info="${2:-}"
    
    if [ "$DEBUG" = "true" ]; then
        debug_info+="\nEnvironment:\n"
        debug_info+="PAPER_REPO_URL=$PAPER_REPO_URL\n"
        debug_info+="PAPER_TARGET_FOLDER=$PAPER_TARGET_FOLDER\n"
        debug_info+="Current Directory: $(pwd)\n"
        debug_info+="Temp Directory: ${TEMP_DIR:-not set}\n"
    fi
    
    log "ERROR" "$message" "$debug_info"
    exit 1
}

# Function to clean up temporary directories
cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        log "DEBUG" "Removing temporary directory" "Directory: $TEMP_DIR"
        rm -rf "$TEMP_DIR"
    fi
}

# Set trap for cleanup on script exit
trap cleanup EXIT

# Validate environment and requirements
validate_environment() {
    local required_vars=("PAPER_REPO_URL" "PAPER_TARGET_FOLDER")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        error_exit "Missing required environment variables: ${missing_vars[*]}"
    fi

    # Check for required commands
    for cmd in git yq; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            error_exit "Required command not found: $cmd"
        fi
    done
}

# Get repository information and latest commit
get_repo_info() {
    local ref="HEAD"
    [ -n "${PAPER_COMMIT:-}" ] && ref="${PAPER_COMMIT}"
    [ -n "${PAPER_BRANCH:-}" ] && ref="refs/heads/${PAPER_BRANCH}"

    log "INFO" "Fetching repository info" "Using ref: $ref"
    
    LATEST_COMMIT=$(git ls-remote "$PAPER_REPO_URL" "$ref" | cut -f1) || \
        error_exit "Failed to fetch latest commit"

    if [ -z "$LATEST_COMMIT" ]; then
        error_exit "No commit hash found for specified reference"
    fi
}

# Check if paper needs updating
check_update_needed() {
    [ "${PAPER_FORCE_UPDATE:-false}" = "true" ] && return 0
    
    if [ -f "$LAST_COMMIT_FILE" ]; then
        local last_commit
        last_commit=$(cat "$LAST_COMMIT_FILE")
        
        if [ "$last_commit" = "$LATEST_COMMIT" ]; then
            log "INFO" "Repository is up-to-date"
            return 1
        fi
    fi
    
    return 0
}

# Clone the repository
clone_repository() {
    local clone_opts=("--quiet" "--depth" "1")
    [ -n "${PAPER_BRANCH:-}" ] && clone_opts+=("--branch" "${PAPER_BRANCH}")
    
    log "INFO" "Cloning repository..."
    
    if ! git clone "${clone_opts[@]}" "$PAPER_REPO_URL" "$TEMP_DIR"; then
        error_exit "Failed to clone repository"
    fi

    if [ -n "${PAPER_COMMIT:-}" ]; then
        cd "$TEMP_DIR" || error_exit "Failed to change directory"
        if ! git checkout -q "$PAPER_COMMIT"; then
            error_exit "Failed to checkout specified commit"
        fi
    fi
}

# Find the base name for paper files
find_base_name() {
    local dir="$1"
    local base=""
    
    # Try _quarto.yml first
    if [ -f "$dir/_quarto.yml" ]; then
        base=$(yq ".manuscript.article" "$dir/_quarto.yml" | sed 's/\.qmd$//')
        [ "$base" != "null" ] && [ -n "$base" ] && echo "$base" && return 0
    fi
    
    # Fallback to finding files
    for ext in "qmd" "ipynb"; do
        local files=("$dir"/*."$ext")
        if [ -f "${files[0]}" ]; then
            basename "${files[0]}" ".$ext"
            return 0
        fi
    done
    
    return 1
}

# Copy paper files to target directory
copy_paper_files() {
    local source_dir="$1"
    local base_name="$2"
    
    mkdir -p "$PAPER_DIR"
    
    # Copy main files
    for ext in "quarto_ipynb" "ipynb" "qmd"; do
        [ -f "$source_dir/${base_name}.${ext}" ] && \
            cp "$source_dir/${base_name}.${ext}" "$PAPER_DIR/"
    done

    # Copy supporting files and directories
    [ -f "$source_dir/references.bib" ] && cp "$source_dir/references.bib" "$PAPER_DIR/"
    [ -d "$source_dir/figures" ] && cp -r "$source_dir/figures" "$PAPER_DIR/"
    [ -d "$source_dir/_tex" ] && cp -r "$source_dir/_tex" "$PAPER_DIR/"
    [ -d "$source_dir/${base_name}_files" ] && \
        cp -r "$source_dir/${base_name}_files" "$PAPER_DIR/"
    
    # Copy freeze directory if it exists
    local freeze_source="$source_dir/_freeze/${base_name}"
    local freeze_target="$ORIGINAL_DIR/_freeze/research/papers/${PAPER_TARGET_FOLDER}/${base_name}"
    
    if [ -d "$freeze_source" ]; then
        mkdir -p "$freeze_target"
        cp -r "$freeze_source"/* "$freeze_target/"
    fi
}

# Main execution starts here
main() {
    log "INFO" "Starting paper fetch process..."
    
    validate_environment
    
    ORIGINAL_DIR="$(pwd)"
    PAPER_DIR="${ORIGINAL_DIR}/research/papers/${PAPER_TARGET_FOLDER}"
    LAST_COMMIT_FILE="$PAPER_DIR/last_commit.txt"
    TEMP_DIR="$(mktemp -d)" || error_exit "Failed to create temporary directory"

    get_repo_info

    if ! check_update_needed; then
        exit 0
    fi

    clone_repository
    
    cd "$TEMP_DIR" || error_exit "Failed to change to temporary directory"
    
    local base_name
    base_name=$(find_base_name "$TEMP_DIR") || \
        error_exit "Could not find paper source file"

    copy_paper_files "$TEMP_DIR" "$base_name"
    
    echo "$LATEST_COMMIT" > "$LAST_COMMIT_FILE"

    log "INFO" "Paper successfully processed"
}

# Run main function
main "$@"