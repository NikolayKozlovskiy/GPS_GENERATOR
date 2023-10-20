FROM python:3.10-bullseye

WORKDIR /GPS_GENERATOR

RUN apt-get update && \
    apt-get install -y \
    gdal-bin \
    libgdal-dev \
    curl

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYTHONPATH=/GPS_GENERATOR

COPY pyproject.toml poetry.lock README.md ./

RUN poetry install --with vis --no-root && rm -rf $POETRY_CACHE_DIR

COPY config ./config
COPY gps_synth_test ./gps_synth_test
COPY Makefile ./

EXPOSE 8888

CMD ["tail", "-f", "/dev/null"]
