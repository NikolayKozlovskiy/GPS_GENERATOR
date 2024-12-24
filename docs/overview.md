# About GPS Synth 🗂️

This Python codebase generates **synthetic GPS data based on the properties of a network and users**. The code source allows for flexible specification of unique characteristics for a network (e.g., a place of interest) and user parameters (e.g., speed limit).

The basic foundation of the approach is as follows:

- Each use case is denoted as a **profile**. For each profile, network and user parameters should be specified
- Profiles **can share the identical network** (if network parameters are the same), but will always have **a different movement history for their users** (meaning that even if users' parameters are the same, the output trajectories will be different)
- A network is a **combination of anchor points/locations and roads/ways that connect locations to each other** (essentially, a graph with nodes and edges)
- All locations are derived from [OpenStreetMap's conceptual data model](https://wiki.openstreetmap.org/wiki/Main_Page) of the physical world using the osmnx library
- There are three main types of locations: **home, work and event** (bars, parks, museums, etc.). Event could be either one of the **regular** locations of a user or **random** location (amenity) in the area
- The entire movement history of a user can be described as **a consecutive process of stay and movement activities happen in some locations**
- The combination of these two types of activities and the type of locations in which they occur are **specified by the plot**. Each unique movement plot should automatically produce a new child class of the Parent Class User (e.g., `User_employed_walk` class in `./gps_synth/user/user_employed_walk.py`)
