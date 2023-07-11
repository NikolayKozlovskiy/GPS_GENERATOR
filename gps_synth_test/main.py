import yaml
import sys
from gps_synth_test.common.functions import class_getter

def main(config_file_path): 

  config = yaml.safe_load(open(str(config_file_path), "r"))

  GPS_GENERATOR = class_getter(config['INIT']['GPS_GENERATOR_PATH'], config['INIT']['GPS_GENERATOR_CLASS'])

  GPS_GENERATOR = GPS_GENERATOR(config)

  GPS_GENERATOR.run()

if __name__ == '__main__': 
  main(sys.argv[1])

