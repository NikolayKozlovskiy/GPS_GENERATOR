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
    PYTHONPATH=/GPS_GENERATOR

COPY pyproject.toml README.md ./

RUN poetry install --with vis

COPY configs ./configs
COPY gps_synth ./gps_synth

EXPOSE 8888

CMD ["tail", "-f", "/dev/null"]
