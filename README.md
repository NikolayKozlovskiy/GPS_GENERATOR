# GPS_GENERATOR

## Overview

This Python package generates **synthetic GPS data based on the properties of a network and users**. The package allows for flexible specification of unique characteristics for a network (e.g., a place of interest) and user parameters (e.g., speed limit).

The basic foundation of the approach is as follows:

- Each use case is denoted as a **profile**. For each profile, network and user parameters should be specified
- Profiles **can share the identical network** (if network parameters are the same), but will always have **a different movement history for their users** (meaning that even if users' parameters are the same, the output trajectories will be different)
- A network is a **combination of anchor points/locations and roads/ways that connect locations to each other** (essentially, a graph with nodes and edges)
- All locations are derived from [OpenStreetMap's conceptual data model](https://wiki.openstreetmap.org/wiki/Main_Page) of the physical world using the osmnx library
- There are three main types of locations: **home, work and event** (bars, parks, museums, etc.). Event could be either one of the **regular** locations of a user or **random** location (amenity) in the area
- The entire movement history of a user can be described as **a consecutive process of stay and movement activities happen in some locations**
- The combination of these two types of activities and the type of locations in which they occur are **specified by the plot**. Each unique movement plot should automatically produce a new child class of the Parent Class User (e.g., in this script, it is the User_walk class)

## Deployment

### Conda + Poetry

1. Navigate to a directory you want to run the package and store results
2. Clone the repo: `git clone https://github.com/NikolayKozlovskiy/GPS_GENERATOR.git`
3. Move to GPS_GENERATOR directory: `cd GPS_GENERATOR`
4. Create python environment with [conda](https://docs.conda.io/en/latest/), conda is used for downloading python; 3.9 <= python version <= 3.12 because of dependecies' specifics: `conda create --name [your_env_name] python=3.10 -y`
5. Activate python environment: `conda activate [your_env_name]`
6. Install [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer), version - up to you to choose: `pip install poetry==1.6.0`
7. Install other dependencies listed in pyproject.toml, `poetry install --with vis`, **_--with vis_** option specifies that along with core dependencies an optional group called _vis_ should be installed. _Vis_ group includes libraries that you may need to analyse and visualise the output results, run `poetry install` if you don't need these modules
8. Run the codebase: `python gps_synth/main.py configs/config_example.yaml`
