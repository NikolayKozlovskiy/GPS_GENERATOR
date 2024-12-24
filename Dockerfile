# https://medium.com/@albertazzir/blazing-fast-python-docker-builds-with-poetry-a78a66f5aed0
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

# heated debate about the usage of poetry.lock  
# https://stackoverflow.com/questions/61037557/should-i-commit-lock-file-changes-separately-what-should-i-write-for-the-commi
# recommendations https://python-poetry.org/docs/basic-usage/#:~:text=You%20should%20commit%20the%20poetry,of%20dependencies%20(more%20below).
COPY pyproject.toml poetry.lock README.md ./

# delete --with vis,docs if you don't need these optional groups dependencies 
RUN poetry install --with vis,docs --no-root && rm -rf $POETRY_CACHE_DIR

COPY configs ./configs
COPY gps_synth ./gps_synth
# comment out if you do not need to run notebooks in docker container
COPY notebooks ./notebooks

RUN poetry install

CMD ["tail", "-f", "/dev/null"]
