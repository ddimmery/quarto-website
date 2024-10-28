#!/bin/bash

# Check if the QUARTO_PROJECT_RENDER_ALL environment variable is set
if [ -z "$QUARTO_PROJECT_RENDER_ALL" ]; then
    echo "QUARTO_PROJECT_RENDER_ALL is not set. Exiting."
    exit 1
fi

# Store the original working directory
ORIGINAL_DIR="$(pwd)"
needs_update=true

# Define directories using absolute paths
PAPER_DIR="${ORIGINAL_DIR}/research/papers/embedded_paper"
LAST_COMMIT_FILE="$PAPER_DIR/last_commit.txt"

# Create directories if they don't exist
mkdir -p "$PAPER_DIR"

# Clone the entire repository
REPO_URL="https://github.com/MitchellAcoustics/JASAEL-HowToAnalyseQuantiativeSoundscapeData.git"
TEMP_DIR="$(mktemp -d)"

# Fetch the latest commit hash from the remote repository
LATEST_COMMIT=$(git rev-parse HEAD)

# Check if we have a last commit hash and need to check for updates
if [ -f "$LAST_COMMIT_FILE" ] && [ "$needs_update" = "false" ]; then
    REPO_URL="https://github.com/MitchellAcoustics/JASAEL-HowToAnalyseQuantiativeSoundscapeData.git"
    LATEST_COMMIT=$(git ls-remote "$REPO_URL" HEAD | cut -f1)
    LAST_COMMIT=$(cat "$LAST_COMMIT_FILE")
    
    if [ "$LAST_COMMIT" != "$LATEST_COMMIT" ]; then
        echo "Remote repository has updates."
        needs_update=true
    else
        echo "Remote repository is up-to-date."
    fi
fi

if [ "$needs_update" = "false" ]; then
    echo "No updates found. Exiting."
    exit 0
fi

git clone "$REPO_URL" "$TEMP_DIR"
cd "$TEMP_DIR"

# Parse _quarto.yml to determine the base name, output files, and output directory
QUARTO_YML="_quarto.yml"
BASE_NAME=""
OUTPUT_FILES=()
OUTPUT_DIR=""

if [ -f "$QUARTO_YML" ]; then
    if command -v yq >/dev/null 2>&1; then
        # Get base name from manuscript.article if it exists
        BASE_NAME=$(yq ".manuscript.article" "$QUARTO_YML" | sed 's/\.qmd$//')
        
        # Get output directory
        OUTPUT_DIR=$(yq ".project.output-dir" "$QUARTO_YML")
        
        # Get output files from different formats
        html_output=$(yq ".format.html.output-file" "$QUARTO_YML")
        pdf_output=$(yq ".format.elsevier-pdf.output-file" "$QUARTO_YML")
        
        # Add non-null output files to array
        if [ "$html_output" != "null" ]; then
            OUTPUT_FILES+=("$html_output")
        fi
        if [ "$pdf_output" != "null" ]; then
            OUTPUT_FILES+=("$pdf_output")
        fi
    else
        echo "yq is not installed. Please install yq for proper YAML parsing."
        exit 1
    fi
fi

echo "BASE_NAME from _quarto.yml: $BASE_NAME"
echo "OUTPUT_DIR from _quarto.yml: $OUTPUT_DIR"
echo "OUTPUT_FILES from _quarto.yml: ${OUTPUT_FILES[@]}"

# Fallback to finding a .qmd or .ipynb file if _quarto.yml does not define the base name
if [ -z "$BASE_NAME" ] || [ "$BASE_NAME" = "null" ]; then
    for file in *.qmd *.ipynb; do
        if [ -f "$file" ]; then
            echo "Found file: $file"
            BASE_NAME="${file%.*}"
            break
        fi
    done
fi

echo "BASE_NAME after fallback: $BASE_NAME"

# Check if a base name was found
if [ -z "$BASE_NAME" ] || [ "$BASE_NAME" = "null" ]; then
    echo "No .qmd or .ipynb file found in the root directory. Exiting."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Copy the paper files if they don't already exist
[ ! -f "$PAPER_DIR/${BASE_NAME}.quarto_ipynb" ] && cp "${BASE_NAME}.quarto_ipynb" "$PAPER_DIR/${BASE_NAME}.quarto_ipynb"
[ ! -f "$PAPER_DIR/${BASE_NAME}.ipynb" ] && cp "${BASE_NAME}.ipynb" "$PAPER_DIR/${BASE_NAME}.ipynb"
[ ! -f "$PAPER_DIR/${BASE_NAME}.qmd" ] && cp "${BASE_NAME}.qmd" "$PAPER_DIR/${BASE_NAME}.qmd"
[ ! -d "$PAPER_DIR/figures" ] && cp -r "${OUTPUT_DIR}/figures" "$PAPER_DIR/figures"
[ ! -d "$PAPER_DIR/_tex" ] && cp -r "${OUTPUT_DIR}/_tex" "$PAPER_DIR/_tex"
[ ! -d "$PAPER_DIR/${BASE_NAME}_files" ] && cp -r "${OUTPUT_DIR}/${BASE_NAME}_files" "$PAPER_DIR/${BASE_NAME}_files"
[ ! -f "$PAPER_DIR/references.bib" ] && cp references.bib "$PAPER_DIR/references.bib"

# Create freeze directory with all parent directories
FREEZE_DIR="${ORIGINAL_DIR}/_freeze/research/papers/embedded_paper/${BASE_NAME}"
mkdir -p "$FREEZE_DIR"

# Copy the _freeze subdirectories
FREEZE_SOURCE_DIR="_freeze/${BASE_NAME}"

echo "Creating freeze directory at: $FREEZE_DIR"
echo "Copying from source: $FREEZE_SOURCE_DIR"

if [ -d "$FREEZE_SOURCE_DIR" ]; then
    for subdir in "$FREEZE_SOURCE_DIR"/*; do
        if [ -d "$subdir" ]; then
            echo "Copying subdirectory: $subdir"
            cp -r "$subdir" "$FREEZE_DIR/"
        fi
    done
else
    echo "Source freeze directory not found: $FREEZE_SOURCE_DIR"
fi

# Save the latest commit hash to the file
echo "$LATEST_COMMIT" > "$LAST_COMMIT_FILE"

# Clean up
rm -rf "$TEMP_DIR"

echo "Files have been successfully copied."