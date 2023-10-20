PWD := $(shell pwd)
OUTPUT_DIR ?= output
CONFIG ?= config/config.yaml

build_docker_image: 
	@echo "Building docker image gps_generator_synth"
	@docker build . -t gps_generator_synth -f Dockerfile

# create_docker_container: 
# 	@echo "Based on built image creating container gps_generator_synth"
# 	@echo $(OUTPUT_DIR)
# 	@docker run --name gps_generator_synth --rm \
# 	--mount type=bind,src=$(PWD)/config,dst=/configs \
# 	--mount type=bind,src=$(OUTPUT_DIR),dst=/output \
# 	-t gps_generator_nikolay \
# 	poetry run python gps_synth_test/main.py $(CONFIG)

create_docker_container_with_shell: 
	@echo "Based on built image creating container gps_generator_synth"
	@echo $(OUTPUT_DIR)
	@docker run --name gps_generator_synth --rm \
	--mount type=bind,src=$(PWD)/config,dst=/GPS_GENERATOR/config \
	--mount type=bind,src=$(OUTPUT_DIR),dst=/GPS_GENERATOR/output_files \
	-ti gps_generator_synth /bin/bash

run_main_file:
	@echo "Running main.py"
	@poetry run python gps_synth_test/main.py config/config.yaml

stop_docker_container:
	@docker stop gps_generator_synth
