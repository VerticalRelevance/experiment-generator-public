import requests
import argparse
import os
import shutil
import yaml
import configparser
import boto3

CONFIG_FILE = 'config.ini'
API_URL = None
API_PARAM = "/experiment_generator/api_url"

def api_call(method, route, data=None, params=None, files=None, print_response=True):
    url = f"{API_URL}/{route}"
    response = requests.request(method, url, json=data, params=params, files=files)
    if response.status_code >= 400:
        raise Exception(f"API call to /{route} failed: {response.text}.")
    if print_response:
        print(response)
        print(response.text)
    return response

def update_config_url(config, config_file, value):

    # Update the API URL in the config file
    config.set("API", "url", value)

    with open(config_file, 'w') as config_file:
        config.write(config_file)

def main():
    parser = argparse.ArgumentParser(description="CLI utility for Experiment Generator API")
    subparsers = parser.add_subparsers(dest='command')
    
    app = subparsers.add_parser("app")
    app_sp = app.add_subparsers(dest="app_subcommand")
    app_init = app_sp.add_parser("init", help="Gets documentation and starter templates")
    onboarding = app_sp.add_parser("onboarding", help="Onboard app")
    onboarding.add_argument("crud", choices=["create", "update", "get", "delete"], help="CRUD for onboarding app", default=None)
    onboarding.add_argument("item", default=None)
    
    package = subparsers.add_parser("package")
    package.add_argument("crud", choices=["upload", "delete"], help="upload or delete module packages")
    package.add_argument("item", default=None)

    scenario = subparsers.add_parser("scenario")
    scenario.add_argument("crud", choices=["create", "update", "get", "delete"], help="CRUD operations for building out method section")
    scenario.add_argument("item", default=None)

    generator = subparsers.add_parser("generator")
    generator.add_argument("crud", choices=["create", "update", "get", "delete"], help="CRUD operations for experiments")
    generator.add_argument("item")

    root_init = subparsers.add_parser("init")
    root_init_sp = root_init.add_subparsers(dest="init_subcommand")
    api_set = root_init_sp.add_parser("api-url", help="Sets api url")
    api_set.add_argument("url")

    args = parser.parse_args()

    if args.command =="init":
        if args.init_subcommand == "api-url":
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            update_config_url(config, CONFIG_FILE, args.url)

    if args.command =="app":
        if args.app_subcommand == "init":

            # Make directory and copy over starter files
            dir_name = "app_config_defaults"
            os.makedirs(dir_name, exist_ok=True)
            shutil.copy('sample_template.yaml', dir_name)

            # Get and store documentation
            docs = api_call('GET', 'config/getinputs', params={'type':'documentation'}, print_response=False)
            arg_pairs = api_call('GET', 'config/getinputs', params={'type':'arg pairs'}, print_response=False)
            
            filepath_docs = os.path.join(dir_name, "documentation")
            filepath_args = os.path.join(dir_name, "arg_pairs")
            
            with open(filepath_docs, 'wb') as file:
                file.write(docs.content)

            with open(filepath_args, 'wb') as file:
                file.write(arg_pairs.content)

            print(f"initialized at: {os.path.abspath(dir_name)}")

        if args.app_subcommand == "onboarding":
            if args.crud == "create" or args.crud == "update":
                with open(args.item, "rb") as file:
                    yaml_data = yaml.safe_load(file)
                    call = "POST" if args.crud == "create" else "PUT"
                    r = api_call(call, "config/target", data=yaml_data['Target Application Config'])
            elif args.crud == "get":
                r = api_call("get", "config/target", params={"term": args.item}, print_response=False)
                y_resp = yaml.dump(r.json())
                print(y_resp)
            elif args.crud == "delete":
                with open(args.item, "rb") as file:
                    yaml_data = yaml.safe_load(file)
                    r = api_call("delete", "config/target", data=yaml_data['Target Application Delete'])


    if args.command =="package":
        if args.crud == "upload":
            with open(args.item, "rb") as file:
                r = api_call("POST", "package", files={"file": file})

        elif args.crud == "delete":
            del_json = {"package": args.item}
            r = api_call("DELETE", "package", data=del_json)

    if args.command == "scenario":

        if args.crud == "create" or args.crud == "update":
            with open(args.item, "rb") as file:
                yaml_data = yaml.safe_load(file)
                call = "POST" if args.crud == "create" else "PUT"
                
                # for multiple scenarios, iteration happens here. other calls can iterate in lambda. will standarize later
                for method in yaml_data['Scenario Method']:
                    r = api_call(call, "config/method", data=method)

                for config in yaml_data['Scenario Configurations']:
                    r = api_call(call, "config/scenario", data=config)

        elif args.crud == "get":
            rm = api_call("get", "config/method", params={"term": args.item}, print_response=False)
            rs = api_call("get", "config/scenario", params={"name": args.item}, print_response=False)
            y_resp = {
                "Method": rm.json(),
                "Config": rs.json()
            }
            y_resp = yaml.dump(y_resp)
            print(y_resp)

        elif args.crud == "delete":
            with open(args.item, "rb") as file:
                yaml_data = yaml.safe_load(file)
                if 'Scenario Method Delete' in yaml_data:
                    for item in yaml_data['Scenario Method Delete']:
                        r = api_call("delete", "config/method", data=item, print_response=False)
                        if r.ok:
                            print(f"{item} deleted")
                if 'Scenario Config Delete' in yaml_data:
                    for item in yaml_data['Scenario Config Delete']:
                        r = api_call("delete", "config/scenario", data={"term": item}, print_response=False)
                        if r.ok:
                            print(f"{item} deleted")

    if args.command == "generator":
        if isinstance(args.item, str):
            split_title = args.item.split('-', 1)
        if args.crud == "create" or args.crud == "update":
            data = {
                args.item: {
                    "target application": split_title[0],
                    "experiment scenario": split_title[1]
                }
            }
            call = "POST" if args.crud == "create" else "PUT"
            r = api_call(call, "generate", data=data)
        
        elif args.crud == "get":
            r = api_call("get", "generate", params={"experiment name": args.item})
        
        elif args.crud == "delete":
            if split_title:
                r = api_call("delete", "generate", data={"Experiment Names": [args.item]})
            else:
                with open(args.item, "rb") as file:
                    yaml_data = yaml.safe_load(file)
                    deletes = {"Experiment Names": yaml_data['Experiment Names Delete']}
                    r = api_call("delete", "generate", data=deletes)

if __name__ == "__main__":
    
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    
    if config.has_option("API", "URL"):
        API_URL = config.get("API", "URL")
    else:
        # Retrieve and update config.ini with url

        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(Name=API_PARAM, WithDecryption=True)
        API_URL = response['Parameter']['Value']

        update_config_url(config, CONFIG_FILE, API_URL)


    if API_URL:
        main()
    else:
        print("API URL not set. Please set manually via init api-url or check if the proper ssm parameter is set")