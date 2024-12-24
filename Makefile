PWD := $(shell pwd)
CONFIG ?= configs/config_example.yaml
OUTPUT_DIR ?= output_files

build_docker_image: 
	@echo "Building docker image gps_generator"
	@docker build . -t gps_generator -f Dockerfile

create_docker_container: 
	@echo "Based on built image creating container gps_generator and with binded directories"
	@echo "The ouput directory path: $(OUTPUT_DIR)"
	@docker run -p 8888:8888 --name gps_generator \
	--mount type=bind,src=$(PWD)/configs,dst=/GPS_GENERATOR/configs \
	--mount type=bind,src=$(PWD)/$(OUTPUT_DIR),dst=/GPS_GENERATOR/output_files \
	-t gps_generator 

run_main_script:
	@echo "Running main script in docker container"
	@docker exec gps_generator poetry run python gps_synth/main.py $(CONFIG)

run_jupyter_lab: 
	@docker exec gps_generator poetry run jupyter lab --allow-root --ip='*' --NotebookApp.token='' \
	--NotebookApp.password='' --notebook-dir /GPS_GENERATOR


remove_docker_container:
	@echo "Removing container, run create_docker_container command if you need it again"
	@docker rm gps_generator --force