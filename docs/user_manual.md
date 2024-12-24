# User Manual 🦮

## Brief navigation

To enable pre-commit hooks run the `pre-commit install` command to set up the git hooks integration with `.pre-commit-config.yaml` file.

It is hihly recommended to use Docker environment. If you need to experiment with the code, print out the specific output you can do this in JupyterLab, execute `make run_jupyter_lab` and go to `http://127.0.0.1:8888/lab` (the port should not be occupied both in docker and local machine). If you want to run some other 'more custom' commands use [docker exec](https://docs.docker.com/engine/reference/commandline/exec/) option, make sure your container is running.


## Output structure

There are three main outputs of the repository, all in parquet format and partitioned: 

1. GPS data with following columns: `user_id,timestamp,lon,lat,profile_name`; 
2. Network data with following columns: `element_type,osmid,name,centre_x,centre_y,loc_type,network_name` 
3. Metadata with the following columns: `user_id,home_id,work_id,regular_loc_array,profile_name, network_name`

Example of the output structure:

```
/output_root
├── gps_data
│   │
│   ├── profile_name=profile_name_1
│   │   ├── part-{i}[hex].parquet
│   │   └── part-{i}[hex].parquet
│   │
│   └── profile_name=profile_name_2
│       ├── part-{i}[hex].parquet
│       └── part-{i}[hex].parquet
│
├── metadata
│   │
│   ├── profile_name=profile_name_1
│   │   ├── part-{i}[hex].parquet
│   │   └── part-{i}[hex].parquet
│   │
│   └── profile_name=profile_name_2
│       ├── part-{i}[hex].parquet
│       └── part-{i}[hex].parquet
│
└── network_data
    │
    └── network_name=network_name_1
        ├── part-{i}[hex].parquet
        └── part-{i}[hex].parquet
```

P.S. In `notebooks/vis_notebook.ipynb` there are some approaches implemented to visualise and analyse results.