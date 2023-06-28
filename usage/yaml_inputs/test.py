# import yaml

# def load_yaml(file_path):
#     with open(file_path, 'r') as file:
#         try:
#             data = yaml.safe_load(file)
#             return data
#         except yaml.YAMLError as e:
#             print(f"Error while loading YAML file: {e}")

# # Specify the path to your YAML file
# yaml_file_path = r'C:\Users\ShahRahman\Desktop\Experiment Generator\usage\yaml_inputs\_hold.yaml'

# # Load the YAML file and convert it into a dictionary
# yaml_data = load_yaml(yaml_file_path)

# funcs = []
# # Print the dictionary
# for i in yaml_data['method']:
#     key = i['provider']['module']+'.'+i['provider']['func']
#     key = key.replace('resiliency','experimentvr')
#     funcs.append(key)

# data = {
#     "Scenario Method": {
#         "Processor SSM Overflow" : funcs
#     }
# }

# import yaml

# yaml_data = yaml.dump(data, sort_keys=False)

# print(yaml_data)

API_URL = "https://ahefn3akse.execute-api.us-east-1.amazonaws.com/prod/"

import requests

def api_call(method, route, data=None, params=None, files=None):
    url = f"{API_URL}/{route}"
    response = requests.request(method, url, json=data, params=params, files=files)
    
    if response.status_code >= 400:
        raise Exception(f"API call to /{route} failed: {response.text}.")
    
    print(f"/{route} call response: \n{response.text}")

api_call('GET', 'getinputs', params={'type':'documentation'})