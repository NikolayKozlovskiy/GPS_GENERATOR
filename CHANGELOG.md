# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased]

### Added

- CHANGELOG.md

## [v0.2.0-beta](https://github.com/NikolayKozlovskiy/GPS_GENERATOR/releases/tag/v0.2.0-beta) - 2025-01-04

### Added

- pre-commit hooks for Pylint, Black formatter, isort
- Automated docs generation with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- GitHub Actions for docs generation and Docker Image build

### Changed

- Refactoring of User and GPS_Generator modules - apart from formatting and linting adjustments, this refectoring holds **a MAJOR change which leads to incompatible API**. Previously Network was an attribute of User class, now instead User methods accept Network attributes as an explicit argument
- Bump geopandas from 0.14.0 to 0.14.4


## [v0.1.0-beta](https://github.com/NikolayKozlovskiy/GPS_GENERATOR/releases/tag/v0.1.0-beta) - 2024-01-01

### Added

- Initial implementation of gps_synth package with Network, User, GPS_Generator modules
- Dev env with Docker and Poetry
- [Visualisation notebook](notebooks/vis_notebook.ipynb) for results' evaluation
- Apache License