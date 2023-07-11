
from network.network import Network
from user.user import User
import yaml
import importlib

config = yaml.safe_load(open("config.yaml", "r"))

network_module_path = config['CLASS_INIT']['NETWORK_MODULE_PATH']
network_class_name = config['CLASS_INIT']['NETWORK_CLASS_NAME']
Network_module = importlib.import_module(network_module_path)
Network_class = getattr(Network_module, network_class_name)(config)

Network_class.run()

user_module_path = config['CLASS_INIT']['USER_MODULE_PATH']
user_class_name = config['CLASS_INIT']['USER_CLASS_NAME']
user_module = importlib.import_module(user_module_path)
User_walk = getattr(user_module, user_class_name)

# user = User_walk(config, 1, Network_class)
# user.get_meaningful_locations()
# user.generate_gps()


# Network_class.run()

# print(f'Before: {",".join("%s: %s" % item for item in vars(Network).items())}')
# Network.generate_graph()
# print(f'Before: {",".join("%s: %s" % item for item in vars(Network).items())}')


