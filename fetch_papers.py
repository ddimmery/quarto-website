
# %%
import fsspec
from pathlib import Path
import os

# Only run this script if the QUARTO_PROJECT_RENDER_ALL environment variable is set 
# if not os.getenv("QUARTO_PROJECT_RENDER_ALL"):
#     exit()

#TODO: Wrap in a function
#TODO: Check if the file already exists before downloading
#TODO: Check if the file is the same as the one on the server before downloading (use commit hash?)

### JASA-EL How to Analyse Quantitative Soundscape Data
paper_dir = Path.cwd().joinpath("research/papers/embedded_paper/")
paper_dir.mkdir(exist_ok=True, parents=True)

fs = fsspec.filesystem("github", org="MitchellAcoustics", repo="JASAEL-HowToAnalyseQuantiativeSoundscapeData", ref="main")

# Download the paper files
# fs.get("paper.qmd", paper_dir.joinpath("index.qmd").as_posix())
fs.get("paper.quarto_ipynb", paper_dir.joinpath("index.quarto_ipynb").as_posix())
fs.get("paper.quarto_ipynb", paper_dir.joinpath("index.ipynb").as_posix())
fs.get("figures/Figure1.jpg", paper_dir.joinpath("figures/Figure1.jpg").as_posix())
fs.get("references.bib", paper_dir.joinpath("references.bib").as_posix())

# Download the _freeze files
destination = Path.cwd().joinpath("_freeze/research/papers/embedded_paper/")
destination.mkdir(exist_ok=True, parents=True)

# Should work with this but it doesn't for some reason. See: https://github.com/fsspec/filesystem_spec/issues/1741 
# fs.get(fs.ls("paper/paper_files"), destination.as_posix(), recursive=True)

for pth in fs.find("_freeze/paper", withdirs=True):
    subdir_path = Path(pth).relative_to("_freeze/paper")
    if fs.isdir(pth):
        destination.joinpath(subdir_path).mkdir(exist_ok=True, parents=True)

    elif fs.isfile(pth):
        fs.get(pth, destination.joinpath(subdir_path).as_posix())
    else:
        continue
