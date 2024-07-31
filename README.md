# My Personal Website

[![Quarto Publish](https://github.com/MitchellAcoustics/quarto-website/actions/workflows/publish.yml/badge.svg)](https://github.com/MitchellAcoustics/quarto-website/actions/workflows/publish.yml)

## Environment management

This project uses `renv` for R environment management. To install the required packages, run the following command:

```r
renv::restore()
```

This project uses `venv` for python environment management. To install the required packages, run the following command:

```bash
source .venv/bin/activate
pip install -r requirements.txt # or ideally, uv pip install -r requirements.txt
```