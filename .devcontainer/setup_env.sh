#!/bin/bash

# This script sets up the Python and R environments for the project.

python_version=${python_version:-3.10}
setup_uv=${setup_uv:-true}
r_version=${r_version:-4.4.1}
setup_renv=${setup_renv:-true}

while [ $# -gt 0 ]; do

   if [[ $1 == *"--"* ]]; then
        param="${1/--/}"
        declare $param="$2"
   fi

  shift
done

if [ f ".python-version" ]; then
    python_version=$(cat .python-version)
fi

# Exit immediately if a command exits with a non-zero status.
set -e

# Treat unset variables as an error when substituting.
set -u

# Pipe failure will result in script exit
set -o pipefail

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to handle errors
handle_error() {
    log "Error occurred in script at line: ${1}. Exit code: ${2}"
    exit 1
}

# Set up error handling
trap 'handle_error ${LINENO} $?' ERR

log "Starting environment setup..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}


# Python setup
log "Setting up Python environment..."
export UV_HOME="/opt/python_env"

setup_python_env() {
    # Python setup
    echo "Setting up Python environment..."

    if [ -f "pyproject.toml" ]; then
        echo "uv project detected."
        if command_exists uv; then
            log "Using uv for environment management."
            uv sync
            uv add ipykernel jupyter
            uv run python -m ipykernel install --user --name=project_kernel
        fi
    elif [ -f ".venv/pyvenv.cfg" ]; then
        echo "Existing venv detected. Assuming uv was used."
        source .venv/bin/activate
        if [ -f "requirements.txt" ]; then
            uv pip install -r requirements.txt
        fi
        uv pip install ipykernel jupyter
        python -m ipykernel install --user --name=project_kernel
    elif [ -f "requirements.txt" ]; then
        echo "requirements.txt found. Creating new environment with uv."
        uv venv
        source .venv/bin/activate
        uv pip install -r requirements.txt
        uv pip install ipykernel jupyter
        python -m ipykernel install --user --name=project_kernel
    else
        echo "No Python environment configuration found. Creating a basic environment."
        uv python install $python_version
        uv python pin $python_version
        uv init --app --no-readme --no-workspace --python $python_version
        uv add ipykernel jupyter
        uv run python -m ipykernel install --user --name=project_kernel
        rm hello.py
    fi
}

if [ "$setup_uv" = true ]; then
    if ! setup_python_env; then
        log "Python environment setup failed."
        exit 1
    fi
fi

log "Python environment setup complete."

if [ "$setup_renv" = true ]; then
    # R setup
    log "Setting up R environment..."
    export R_LIBS_USER="/opt/r_env"

    setup_r_env() {
        if [ -f "renv.lock" ]; then
            log "renv.lock found. Restoring R environment."
            if ! R --quiet -e "renv::restore()"; then
                log "Error: Failed to restore R environment with renv."
                return 1
            fi
        else
            log "No renv.lock found. Initializing new renv project..."
            R --quiet -e "renv::init()"
            R --quiet -e "renv::install(c('pak'))"
            log "Install other R packages."
            R --quiet -e "renv::install(c('yaml', 'languageserver', 'knitr', 'rmarkdown'))"
            R --quiet -e "renv::snapshot()"
        fi

        return 0
    }

    if ! setup_r_env; then
        log "R environment setup failed."
        exit 1
    fi

    log "R environment setup complete."
fi

log "Environment setup completed successfully!"