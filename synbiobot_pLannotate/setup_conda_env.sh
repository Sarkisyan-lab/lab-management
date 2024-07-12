#!/bin/bash

# Source the conda.sh script to initialize conda (user-independent)
source /home/$(whoami)/anaconda3/etc/profile.d/conda.sh  # Dynamically fetch the current user's home directory

# Create a new Conda environment named "plannotate"
conda create -n plannotate python=3.9

# Activate the "plannotate" environment
conda activate plannotate

# Add channels
conda config --env --add channels conda-forge
conda config --env --add channels bioconda
conda config --env --add channels defaults

# Install dependencies
conda install -n plannotate click curl numpy "biopython>=1.78" "blast>=2.10.1" "diamond>=2.0.13" "pandas>=1.3.5" "ripgrep>=13.0.0" "tabulate>=0.8.9" "trnascan-se>=2.0.7" "streamlit=1.8.1" "altair=4.2.*" "bokeh=2.4.1"

# Verify the environment
conda list -n plannotate

conda activate plannotate

git clone https://github.com/mmcguffi/pLannotate.git

cd pLannotate

python setup.py install

plannotate setupdb

cd ..

pip install playwright
playwright install

conda install jupyter notebook
conda install nb_conda_kernels
