FROM python:3.10-bullseye

WORKDIR /
COPY . GPS_GENERATOR

WORKDIR /GPS_GENERATOR

RUN apt-get update && \
    apt-get install -y \
    gdal-bin \
    libgdal-dev \
    curl

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.in-project true --local
RUN poetry install





