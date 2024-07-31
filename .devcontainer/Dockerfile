FROM registry.gitlab.com/quarto-forge/docker/quarto_all

USER root

RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    apt-transport-https \
    build-essential \
    curl \
    libssl-dev \
    libgit2-dev \
    gfortran \
    libatlas-base-dev \
    libbz2-dev \
    libcairo2 \
    r-cran-curl \
    libicu-dev \
    liblzma-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpcre3-dev \
    libtcl8.6 \
    libtk8.6 \
    libx11-6 \
    libxt6 \
    locales \
    tzdata \
    zlib1g-dev \
    cmake \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    libxml2-dev \
    pandoc \
    zlib1g-dev \
    git
    # libcurl4-openssl-dev \
    # libcurl4-gnutls-dev \


USER $MAMBA_USER

COPY --chown=$MAMBA_USER:$MAMBA_USER requirements.txt /tmp/requirements.txt
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install -r /tmp/requirements.txt


# RUN R -e "renv::restore()"