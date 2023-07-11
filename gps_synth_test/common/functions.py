import importlib
import os

def class_getter(module_path: str, class_name: str) -> __build_class__: 
    module = importlib.import_module(module_path)
    class_result = getattr(module, class_name)

    return class_result

def write_data(data, output_path, geo = False): 
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if geo == True:
        data.to_file(output_path, driver = "GPKG")
    data.to_csv(output_path, sep = ',', index=False)

    print(f"Data written to: {output_path}")

