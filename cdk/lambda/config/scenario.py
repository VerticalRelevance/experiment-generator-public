import boto3
import json
import os
import base64
from typing import get_args, Literal, Any, Dict, List, Tuple, Union, _GenericAlias
from decimal import Decimal
from chaoslib.types import * #for ease of eval
from shared import *

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def create_scenario(table, partition_key, sort_key, scenario_dict, all_defaults, all_types):
    scenario = {}
    doc = {}
    no_defaults = [key for key, value in all_defaults.items() if value == "NoDefault"]
    print(all_types)
    for func, args in scenario_dict.items():
        for arg, value in args.items():
            scenario[arg] = value
            if arg in doc:
                doc[arg]['Function Name'].append(func)
            else:
                doc[arg] = {
                    'Required': arg in no_defaults,
                    'Type': all_types[arg],
                    'Default': all_defaults.get(arg),
                    'Function Name': [func]
                }


    send = {
        'scenario': scenario, # what will be overlaid in experiment configuration
        'scenario_function_mappings': scenario_dict, # preserves function->arg mapping (needed for update)
        'required': no_defaults,
        'documentation': doc
    }

    response = create_item(table, partition_key, sort_key, send)
    return response

def handler(event, context):
    http_method = event['httpMethod']
    
    # Extract values
    if http_method != "GET":
        data = base64.b64decode(event['body'])
        mappings = json.loads(data)
        term = mappings['name']
        
    else:
        query_parameters = event['queryStringParameters']
        print(query_parameters)
        term=query_parameters['name']

    if http_method == 'POST' or http_method == 'PUT':
        print(mappings)
        parameters = mappings['scenario']
        
        # If PUT/update, get existing params and combine with current  so logic continues as if POST
        # Switch order to prioritize input arguments
        if http_method == 'PUT':
            existing_params = get_item(table, 'scenario_config', term)['scenario_function_mappings']
            existing_params.update(parameters)
            parameters=existing_params
        
        scenario_config = {}

        # Get arguments from method
        method = get_item(table, 'methods', term)['method']

        # get in format function_name : argument keys
        arguments = {item['name']: item['provider']['arguments'].keys() for item in method}
        print(arguments)
        # no_defaults = []
        all_defaults = {}
        all_types = {}
        for func, args in arguments.items():
            signature = get_item(table, 'packages', func)
            defaults, types = get_defaults_and_types(signature['args'])
            all_defaults.update(defaults)
            all_types.update(types)
            # no_def = [key for key, value in defaults.items() if value == "NoDefault"]
            # no_defaults.extend(no_def)
            if func in parameters:

                # Check if required args and input args are alike 
                only_args, only_params = compare_lists(args, parameters[func].keys())
                print("compare types for ", func)
                
                # If args are the same, validate types
                diff = compare_arg_types(parameters[func], types)
                if diff:
                    return {
                        'statusCode': 500,
                        'body': f"The following arguments do not have the correct type: {diff}"
                    }
                elif not only_args and not only_params:
                    print("arg types pass")
                    # diff is none if no diffrence - update and prepare to send
                    scenario_config.update({func: parameters[func]})

                elif only_args:
                    print("checking defaults")
                    # only_args -> means input/parameter args are less than required args. So we check for default
                    has_defaults = {arg:defaults.get(arg) for arg in only_args}
                    none_values = [key for key, value in has_defaults.items() if value == "NoDefault"]

                    # update if default args + input args satisfy total argument requirements
                    if not none_values:
                        arg_update = {func: parameters[func]}
                        arg_update[func].update(has_defaults)
                        scenario_config.update(arg_update)
                        
                    else:
                        return {
                            'statusCode': 500,
                            'body': f"The function {func} requires the following arguments: {none_values}"
                        }
                elif only_params:
                    print('recieved extra params')
                    print(only_params)
                    extra_types = {arg:type(arg).__name__  for arg in only_params}
                    all_types.update(extra_types)
                    print(all_types)
                    scenario_config.update({func: parameters[func]})
                    
            else:
                print(func)
                print(parameters)
                return {
                    'statusCode': 500,
                    'body': f"Missing function {func}"
                }
        
        print(scenario_config)
        
        resp = create_scenario(table, 'scenario_config', term, scenario_config, all_defaults, all_types)
        return handle_dynamodb_response(resp)
    
    elif http_method == 'GET':
        resp = get_item(table=table, partition_key="scenario_config", sort_key=term)
        scen = resp['scenario']
        for arg, val in scen.items():
            if isinstance(val, Decimal):
                _real_type_ = eval(resp['documentation'][arg]['Type'])
                scen[arg] = _real_type_(val)
        return {
            'statusCode': 200,
            'body': json.dumps(scen)
        } 
    elif http_method == 'DELETE':
        resp = delete_item(table=table, partition_key="scenario_config", sort_key=term)
        return handle_dynamodb_response(resp)