# Contribution 💊

## Contribution guidelines

1. Fork the repo
2. Open an issue 
3. Create a branch to this issue that originates from the **main** branch
4. Once issue is resolved, create a PR to the created issue
5. Cross fingers and give yourself deserve praise - the repository administrator(s) will review the PR and hopefully merge it to the main 🤞


## Issues to work on
I am arrogant enough to think that this project might be interesting for someone. Below is a list of issues which can make the results more humanlike, diverse, and efficient.

1. Make movements more realistic:
    - The path between the location and its nearest node can intersect buildings or water bodies (lakes). A user goes through them, it is not realistic.
    - GPS-like errors in the data (e.g., sudden termination of ‘acquiring’ data, or some points that do not make sense).

2. Create more profiles and new User classes:
    - New places.
    - New OSM tags for anchor points.
    - New modes of transport and their combination.
    - New movement plots.

3. In terms of growing number of profiles, possible rethinking of orchestration approach.
4. Code optimization (e.g., in `get_meaningful_locations()`).
5. Testing, benchmarking, trying new config params.
6. More detailed and thorough approach for results' evaluation
7. Just to play around: setting up and running code on Cloud using e.g. Terraform