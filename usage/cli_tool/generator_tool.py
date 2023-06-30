import requests
import argparse
import os
import shutil
import yaml

API_URL = "https://ahefn3akse.execute-api.us-east-1.amazonaws.com/prod/"

def api_call(method, route, data=None, params=None, files=None):
    url = f"{API_URL}/{route}"
    response = requests.request(method, url, json=data, params=params, files=files)
    if response.status_code >= 400:
        raise Exception(f"API call to /{route} failed: {response.text}.")
    return response

def main():
    parser = argparse.ArgumentParser(description="CLI utility for Experiment Generator API")
    subparsers = parser.add_subparsers(dest='command')
    
    app = subparsers.add_parser("app")
    app.add_argument("crud", choices=["create", "get", "update", "delete"], help="CRUD operation")
    app.add_argument("--file", default=None)
    app_sp = app.add_subparsers(dest="app_subcommand")
    init = app_sp.add_parser("init", help="Gets documentaion and starter templates")
    
    package = subparsers.add_parser("package")
    package.add_argument("crud", choices=["upload", "delete"], help="CRUD operation")
    package.add_argument("path", default=None)

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

    if args.command =="app" and args.crud == "create" or args.crud == "update":
        with open(args.file, "rb") as file:
            yaml_data = yaml.safe_load(file)
            call = "POST" if args.crud == "create" else "PUT"
            r = api_call(call, "config/target", data=yaml_data['Target Application Config'])
            print(r)
            print(r.text)

    if args.command =="package" and args.crud == "upload":
        if os.path.isfile(args.path):
            with open(args.path, "rb") as file:
                api_call("POST", "package", files={"file": file})

if __name__ == "__main__":
    main()