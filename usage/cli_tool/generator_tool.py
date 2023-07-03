import requests
import argparse
import os
import shutil
import yaml

API_URL = os.getenv("API_URL")

def api_call(method, route, data=None, params=None, files=None, print_response=True):
    url = f"{API_URL}/{route}"
    response = requests.request(method, url, json=data, params=params, files=files)
    if response.status_code >= 400:
        raise Exception(f"API call to /{route} failed: {response.text}.")
    if print_response:
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

    args = parser.parse_args()

    if args.command =="app":
        if args.app_subcommand == "init":

            # Make directory and copy over starter files
            dir_name = "app_config_defaults"
            os.makedirs(dir_name, exist_ok=True)
            shutil.copy('sample_template.yaml', dir_name)

            # Get and store documentation
            docs = api_call('GET', 'config/getinputs', params={'type':'documentation'})
            filepath = os.path.join(dir_name, "documentation")
            with open(filepath, 'wb') as file:
                file.write(docs.content)
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
            r = api_call("POST", "package", data=del_json)

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
            rs = api_call("get", "config/scenario", params={"term": args.item}, print_response=False)
            y_resp = {
                "Method": rm.json(),
                "Config": rs.json()
            }
            y_resp = yaml.dump(y_resp)
            print(y_resp)

        elif args.crud == "delete":
            with open(args.item, "rb") as file:
                yaml_data = yaml.safe_load(file)
                r = api_call("delete", "config/method", data=yaml_data['Scenario Method Delete'])
                r = api_call("delete", "config/scenario", data=yaml_data['Scenario Config Delete'])

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
    main()