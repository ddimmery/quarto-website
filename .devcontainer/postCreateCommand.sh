#!/bin/bash

# Set default values for configuration flags
setup_py_venv=${1:-true}
setup_r_renv=${2:-true}
install_py_defaults=${3:-false}
install_r_defaults=${4:-false}
install_tinytex=${5:-false}


# Print configuration
echo "====== Post Create Command ======"
echo "setup_py_venv: $setup_py_venv"
echo "setup_r_renv: $setup_r_renv"
echo "install_py_defaults: $install_py_defaults"
echo "install_r_defaults: $install_r_defaults"
echo "install_tinytex: $install_tinytex"
echo "================================="
echo ""

# Python virtual environment setup
if [ "$setup_py_venv" = true ]; then
    echo "Setting up Python virtual environment..."
    
    if [ ! -d venv ] && [ ! -d .venv ]; then
        echo "Creating virtual environment..."
        uv venv .venv
        . .venv/bin/activate
    elif [ -d venv ]; then
        echo "Activating virtual environment at venv..."
        . venv/bin/activate
    elif [ -d .venv ]; then
        echo "Activating virtual environment at .venv..."
        . .venv/bin/activate
    fi

    if [ -f requirements.lock ]; then
        echo "Installing dependencies from requirements.lock..."
        uv pip install -r requirements.lock
    elif [ -f requirements.txt ]; then
        echo "Installing dependencies from requirements.txt..."
        uv pip install -r requirements.txt
    elif [ "$install_py_defaults" = true ]; then
        echo "Installing default dependencies..."
        uv pip install pandas numpy matplotlib seaborn scikit-learn ipykernel
        echo "Creating requirements.txt..."
        uv pip freeze > requirements.txt
    fi
fi

# R renv setup
if [ "$setup_r_renv" = true ]; then
    echo "Setting up R renv..."
    
    if [ ! -f .Rprofile ]; then
        echo "Creating .Rprofile..."
        echo "options(renv.config.pak.enabled = TRUE)" > .Rprofile
    fi

    if [ ! -f renv.lock ]; then
        echo "renv.lock not found. Initializing renv..."
        Rscript -e 'renv::init(); renv::activate(); options(renv.config.pak.enabled = TRUE)'
        if [ "$install_r_defaults" = true ]; then
            Rscript -e "renv::install(c('rmarkdown', 'tidyverse', 'languageserver')); renv::snapshot()"
        fi
    else
        echo "renv.lock found. Restoring dependencies..."
        Rscript -e 'renv::activate(); options(renv.config.pak.enabled = TRUE); renv::restore()'
    fi
fi

# Setup R language server
setup_r_language_server() {
    echo "Setting up R language server..."
    Rscript -e '
        if (!require(languageserver)) {
            install.packages("languageserver", repos="https://cloud.r-project.org")
        }
        if (!file.exists("~/.Rprofile")) {
            file.create("~/.Rprofile")
        }
        cat("options(languageserver.server_capabilities = list(definitionProvider = TRUE))\n", 
            file = "~/.Rprofile", 
            append = TRUE)
    '
    echo "R language server setup complete."
}

# setup_r_language_server # Probably best just to have vscode do this if you want it.
# if uncommenting, remember to add the input variable at the top and in the devcontainer.json
# TinyTeX installation (no longer necessary, installing texlive via r-apt is much faster)
if [ "$install_tinytex" = true ]; then
    echo "Installing TinyTeX..."
    Rscript -e "install.packages('tinytex', repos='https://cran.rstudio.com/'); tinytex::install_tinytex(add_path=TRUE)"

    echo "Adding TinyTeX to PATH..."
    echo 'export PATH=$PATH:/root/.TinyTeX/bin/aarch64-linux' >> /root/.bashrc
    export PATH=$PATH:/root/.TinyTeX/bin/aarch64-linux
    source /root/.bashrc
    
    # Uncomment the following lines if you need to install additional LaTeX packages
    tlmgr update --self --all
    tlmgr install fancyhdr fontawesome pgf lastpage synctex texcount latexindent titlesec nth gensymb xelatex-dev caption sidenotes \
        marginnote changepage # really helps with quarto render to pre-install the required packages rather than autoinstall
fi