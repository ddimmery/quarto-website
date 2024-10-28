from urllib.request import urlretrieve
import fsspec
from pathlib import Path

#TODO: Wrap in a function
#TODO: Check if the file already exists before downloading

### JASA-EL How to Analyse Quantitative Soundscape Data
urlretrieve(
    'https://raw.githubusercontent.com/MitchellAcoustics/JASAEL-HowToAnalyseQuantiativeSoundscapeData/refs/heads/main/paper.quarto_ipynb',
    'research/papers/embedded-paper/index.ipynb'
)

urlretrieve(
    'https://github.com/MitchellAcoustics/JASAEL-HowToAnalyseQuantiativeSoundscapeData/raw/main/figures/Figure1.jpg',
    'research/papers/embedded-paper/figures/Figure1.jpg'
)

urlretrieve(
    'https://raw.githubusercontent.com/MitchellAcoustics/JASAEL-HowToAnalyseQuantiativeSoundscapeData/refs/heads/main/references.bib',
    'research/papers/embedded-paper/references.bib'
)

destination = Path.cwd().joinpath("research/papers/embedded-paper/index_files")
destination.mkdir(exist_ok=True, parents=True)
fs = fsspec.filesystem("github", org="MitchellAcoustics", repo="JASAEL-HowToAnalyseQuantiativeSoundscapeData", ref="main")
fs.get(fs.ls("paper/paper_files"), destination.as_posix(), recursive=True)

###