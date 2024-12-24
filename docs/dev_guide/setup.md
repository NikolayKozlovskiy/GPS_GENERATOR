# Setup Guide 👷

Both approaches leveraging [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer), a tool that offers an intelligent and intuitive approach to handle Python dependencies. Important note: Poetry doesn't include Python internally, hence it uses Python somewhere externally e.g. from Docker Image, local machine, etc.

## Docker + Poetry + Makefile :simple-docker:

Code is executed within a docker container, however, the outcome can also be directed to your host. The commands are wrapped up in Makefile for convenience\*

1. Navigate to a directory you want to run the codebase and store results
2. Clone the repo: `git clone https://github.com/NikolayKozlovskiy/GPS_GENERATOR.git`
3. Move the repo directory e.g. `cd GPS_GENERATOR`
4. Build a docker image called gps_generator: `make build_docker_image`
5. In `Makefile` correctly specify relative paths for your source directories which then will be used in [bind mounts](https://docs.docker.com/storage/bind-mounts/): `OUTPUT_DIR` and `CONFIG` (or use default ones)
6. Based on the image create a docker container named the same, which will constatntly run till it is removed: `make create_docker_container`
7. Open a new terminal (a docker container is runing in the first one) and run the `main.py` script: `make run_main_script`
6. When you no longer need a container, remove it: `make remove_docker_container`<br />

Prerequirements:

1. Installed [Docker](https://www.docker.com/get-started/)

\*If `make` is not available just open Makefile in text editor and run corresponding shell commands in terminal manually

## Conda + Poetry :fontawesome-solid-laptop:

The fundamental approach remains unchanged, except that in this scenario, Conda is employed to establish an environment with a specified Python version and now you run scripts not in a container but some machine. Despite this, Poetry retains its responsibility for managing dependencies. What approach to use is a difficulty of having alternatives

1. Navigate to a directory you want to run the codebase and store results
2. Clone the repo: `git clone https://github.com/NikolayKozlovskiy/GPS_GENERATOR.git`
3. Move to GPS_GENERATOR directory: `cd GPS_GENERATOR`
4. Create python environment with [conda](https://docs.conda.io/en/latest/), conda is used for downloading python; 3.9 <= python version <= 3.12 because of dependecies' specifics: `conda create --name [your_env_name] python=3.10 -y`
5. Activate python environment: `conda activate [your_env_name]`
6. Install poetry, version - up to you to choose: `pip install poetry==1.6.0`
7. Install other dependencies listed in pyproject.toml, `poetry install --with vis,docs`, **_--with vis,docs_** option specifies that along with core dependencies optional groups called _vis_ and _docs_ should be installed. **_vis_** group includes libraries that you may need to analyse and visualise the output results, **_docs_** group is useful for generating and managing project documentation, just run `poetry install` if you don't need these additional groups
8. Run the codebase: `python gps_synth/main.py configs/[your_config].yaml`\*<br />

Prerequirements:

1. Installed conda, the easiest way is to download [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/)
2. Installed [gdal](https://gdal.org/) locally

\*You may need to directly specify the python path to GPS_GENERATOR: `export PYTHONPATH=/path/to/GPS_GENERATOR folder` for MacOs, for other operating systems ask [ChatGPT](https://chat.openai.com/) :green_heart: