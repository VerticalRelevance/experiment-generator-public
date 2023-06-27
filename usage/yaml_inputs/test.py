import yaml

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as e:
            print(f"Error while loading YAML file: {e}")

# Specify the path to your YAML file
yaml_file_path = r'C:\Users\ShahRahman\Desktop\Experiment Generator\usage\yaml_inputs\_hold.yaml'

# Load the YAML file and convert it into a dictionary
yaml_data = load_yaml(yaml_file_path)

funcs = []
# Print the dictionary
for i in yaml_data['method']:
    key = i['provider']['module']+'.'+i['provider']['func']
    key = key.replace('resiliency','experimentvr')
    funcs.append(key)

data = {
    "Scenario Method": {
        "Processor SSM Overflow" : funcs
    }
}

import yaml

yaml_data = yaml.dump(data, sort_keys=False)

print(yaml_data)
