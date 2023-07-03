import requests
import argparse
import os
import shutil
import yaml

API_URL = os.getenv("API_URL")

def api_call(method, route, data=None, params=None, files=None):
    url = f"{API_URL}/{route}"
    response = requests.request(method, url, json=data, params=params, files=files)
    if response.status_code >= 400:
        raise Exception(f"API call to /{route} failed: {response.text}.")
    print(response)
    print(response.text)
    return response

def main():
    parser = argparse.ArgumentParser(description="CLI utility for Experiment Generator API")
    subparsers = parser.add_subparsers(dest='command')
    
    app = subparsers.add_parser("app")
    app_sp = app.add_subparsers(dest="app_subcommand")
    init = app_sp.add_parser("init", help="Gets documentation and starter templates")
    onboarding = app_sp.add_parser("onboarding", help="Onboard app")
    onboarding.add_argument("crud", choices=["create", "update", "get", "delete"], help="CRUD for onboarding app")
    onboarding.add_argument("item", default=None)
    
    package = subparsers.add_parser("package")
    package.add_argument("crud", choices=["upload", "delete"], help="upload or delete module packages")
    package.add_argument("item", default=None)

    scenario = subparsers.add_parser("scenario")
    scenario.add_argument("crud", choices=["create", "update", "get", "delete"], help="CRUD operations for building out method section")
    scenario.add_argument("item", default=None)

    generator = subparsers.add_parser("generator")
    generator.add_argument("crud", choices=["create", "update", "get", "delete"], help="CRUD operations for experiments")
    generator.add_argument("title")

    args = parser.parse_args()

    if args.command =="app" and args.app_subcommand == "init":

        # Make directory and copy over starter files
        dir_name = "ap_config_defaults"
        os.makedirs(dir_name, exist_ok=True)
        shutil.copy('sample_template.yaml', dir_name)

        # Get and store documentation
        docs = api_call('GET', 'getinputs', params={'type':'documentation'})
        filepath = os.path.join(dir_name, "documentation")
        with open(filepath, 'wb') as file:
            file.write(docs.content)
        print(f"initialized at: {os.path.abspath(dir_name)}")

    if args.command == "app" and (args.crud == "create" or args.crud == "update"):
        with open(args.item, "rb") as file:
            yaml_data = yaml.safe_load(file)
            call = "POST" if args.crud == "create" else "PUT"
            r = api_call(call, "config/target", data=yaml_data['Target Application Config'])


    if args.command =="package" and args.crud == "upload":
        with open(args.item, "rb") as file:
            r = api_call("POST", "package", files={"file": file})

    if args.command =="package" and args.crud == "delete":
        del_json = {"package": args.item}
        r = api_call("POST", "package", data=del_json)

    if args.command == "scenario" and (args.crud == "create" or args.crud == "update"):
        with open(args.item, "rb") as file:
            yaml_data = yaml.safe_load(file)
            call = "POST" if args.crud == "create" else "PUT"
            
            # scenario needs to iterate here. other calls can iterate in lambda. will standarize later
            for method in yaml_data['Scenario Method']:
                r = api_call(call, "config/method", data=method)

            for config in yaml_data['Scenario Configurations']:
                r = api_call(call, "config/scenario", data=config)

    if args.command == "generator" and (args.crud == "create" or args.crud == "update"):
        split_title = args.title.split('-', 1)
        call = "POST" if args.crud == "create" else "PUT"
        data = {
            args.title: {
                "target application": split_title[0],
                "experiment scenario": split_title[1]
            }
        }
        r = api_call(call, "generate", data=data)


if __name__ == "__main__":
    main()