import yaml
import requests
import argparse
import os

API_URL = "https://ahefn3akse.execute-api.us-east-1.amazonaws.com/prod/"

import requests

def api_call(method, route, data=None, params=None, files=None):
    url = f"{API_URL}/{route}"
    response = requests.request(method, url, json=data, params=params, files=files)
    
    if response.status_code >= 400:
        raise Exception(f"API call to /{route} failed: {response.text}.")
    
    print(f"/{route} call response: \n{response.text}")


def main():
    parser = argparse.ArgumentParser(description="Automates Experiment Generator API Calls")
    parser.add_argument('yamlInput', type=str, help='Path to the YAML input file')

    args = parser.parse_args()

    yaml_file = args.yamlInput
    with open(yaml_file, 'r') as file:
        config_data = yaml.safe_load(file)
    
    if 'Package' in config_data:
        for path in config_data['Package']:
            if os.path.isfile(path):
                with open(path, "rb") as file:
                    api_call("POST", "package", files={"file": file})

            else:
                print("Invalid file path provided.")

    if 'Scenario Method' in config_data:
        for config in config_data['Scenario Method']:
            api_call("POST", "config/method", data=config)

    if 'Scenario Configurations' in config_data:
        for config in config_data['Scenario Configurations']:
            api_call("POST", "config/scenario", data=config)

    if 'Target Application Config' in config_data:
        api_call("POST", "config/target", data=config_data['Target Application Config'])

    if 'Generate' in config_data:
        for config in config_data['Generate']:
            api_call("POST", "generate", data=config)

if __name__ == "__main__":
    main()

