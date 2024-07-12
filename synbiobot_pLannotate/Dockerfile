# Base Image
FROM continuumio/anaconda3


# Install rclone
RUN apt-get update
RUN apt-get install -y rclone

RUN conda update -n base -c defaults conda


RUN conda create -n plannotate python=3.9 && \
    conda config --env --add channels conda-forge && \
    conda config --env --add channels bioconda && \
    conda config --env --add channels defaults && \
    conda install -n plannotate -y \
    click curl numpy "biopython>=1.78" \
    "blast>=2.10.1" "diamond>=2.0.13" "pandas>=1.3.5" "ripgrep>=13.0.0" \
    "tabulate>=0.8.9" "trnascan-se>=2.0.7" "streamlit=1.8.1" "altair=4.2.*" "bokeh=2.4.1"

# Verify the environment
RUN conda run -n plannotate conda list

# Clone and install pLannotate
RUN git clone https://github.com/mmcguffi/pLannotate.git && \
    cd pLannotate && \
    conda run -n plannotate python setup.py install && \
    conda run -n plannotate plannotate setupdb && \
    cd ..

# Install Playwright within the "plannotate" environment
RUN conda run -n plannotate pip install playwright && \
    conda run -n plannotate playwright install && \
    conda run -n plannotate playwright install-deps


# Copy core 
COPY ./synbiobot_CORE /synbiobot_CORE

# Copy bot
COPY ./synbiobot_pLannotate /synbiobot_pLannotate

# Remove .env files
RUN rm /synbiobot_CORE/core.env && \
    rm /synbiobot_pLannotate/bot.env

# Set PATH
ENV PATH="/synbiobot_pLannotate:${PATH}"

# Set working directory
WORKDIR /synbiobot_pLannotate


# Upgrade pip and install dependencies from requirements.txt within the "plannotate" environment
RUN conda run -n plannotate pip install --upgrade pip && \
    conda run -n plannotate pip install -r requirements.txt

# Command to run the app within the "plannotate" environment
CMD ["conda", "run", "-n", "plannotate", "python", "bot.py"]
