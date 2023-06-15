import boto3
import json
import os
import base64
from typing import get_args

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def create_scenario(table, partition_key, sort_key, scenario_dict):
    scenario = {}
    for func, args in scenario_dict.items():
        for arg, value in args.items():
            scenario[arg] = value
    item = {
        'partition_key' : partition_key,
        'sort_key' : sort_key,
        'scenario': scenario, # what will be overlaid in experiment configuration
        'scenario_function_mappings': scenario_dict # preserves function->arg mapping (needed for update)
    }

    response = table.put_item(Item=item)
    return response


def get_item(table, partition_key, sort_key):
    key = {
        'partition_key': partition_key,
        'sort_key': sort_key
    }
    print(key)
    response = table.get_item(Key=key)
    item = response.get('Item')
    return item

def delete_item(table, partition_key, sort_key):
    key = {
        'partition_key': partition_key,
        'sort_key': sort_key
    }

    response = table.delete_item(Key=key)

    return response

def handle_dynamodb_response(response):
    print(response)
    try:
        if response['ResponseMetadata']['HTTPStatusCode'] >= 200 and response['ResponseMetadata']['HTTPStatusCode'] < 300:
            return {
                'statusCode': 200,
                'body': 'Action successful!'
            }
        else:
            print(response)
            return {
                'statusCode': 500,
                'body': f"Error: {response}"
            }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': f"An exception occurred: {str(e)}"
        }
    
def compare_lists(l1, l2):
    if sorted(l1) == sorted(l2):
        return "identical"
    else:
        return False
    
def compare_lists(list1, list2):
    # common_elements = set(list1) & set(list2)
    only_in_list1 = set(list1) - set(list2)
    only_in_list2 = set(list2) - set(list1)
    
    return list(only_in_list1), list(only_in_list2)

def get_defaults_and_types(data):
    defaults = {}
    types = {}

    for key, value in data.items():
        defaults[key] = value["default"]
        types[key] = value["type"]

    return defaults, types

def compare_arg_types(input_args, types):

    arg_types = {k: type(v).__name__ for k, v in input_args.items()}

    diff_values = {}

    for key, value in types.items():
        if value and arg_types[key] != value:
            try:
                arg_type = eval(value.lower())
                outer_type, inner_type = outer_inner_types(arg_type)
                if not check_inner_type(input_args[key], outer_type, inner_type):
                    diff_values[key] = value
            except Exception as e:
                print("Error:", str(e))
                diff_values[key] = value
    return diff_values

def outer_inner_types(arg):

    outer = arg.__name__
    outer = eval(outer)
    inner_args = get_args(arg)
    inner = inner_args[0]

    return outer, inner

def check_inner_type(iterable, outer, inner):
    print(outer, inner)
    inner_check = [isinstance(item, inner) for item in iterable]
    print(inner_check)
    if all(inner_check):
        print("pass")
        print(iterable)
        print(type(iterable))
        if type(iterable)==outer:
            print("pass")
            return True
    else:
        return False 

def handler(event, context):
    http_method = event['httpMethod']
    
    # Extract values
    if http_method != "GET":
        data = base64.b64decode(event['body'])
        mappings = json.loads(data)
        term = mappings['term']
        
    else:
        query_parameters = event['queryStringParameters']
        print(query_parameters)
        term=query_parameters['term']

    if http_method == 'POST' or http_method == 'PUT':
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

        for func, args in arguments.items():
            signature = get_item(table, 'packages', func)
            defaults, types = get_defaults_and_types(signature['args'])
            if func in parameters:

                # Check if required args and input args are alike 
                only_args, only_params = compare_lists(args, parameters[func].keys())
                if not only_args and not only_params:

                    # If args are the same, validate types
                    diff = compare_arg_types(parameters[func], types)
                    if not diff:

                        # diff is none if no diffrence - update and prepare to send
                        scenario_config.update({func: parameters[func]})
                    else:
                        return {
                            'statusCode': 500,
                            'body': f"The following arguments do not have the correct type: {diff}"
                        }
                elif only_args:

                    # only_args -> means input/parameter args are less than required args. So we check for default
                    has_defaults = {arg:defaults.get(arg) for arg in only_args}
                    none_values = [key for key, value in has_defaults.items() if value is None]

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
                    
            else:
                return {
                    'statusCode': 500,
                    'body': f"Missing function {func}"
                }
        
        print(scenario_config)
        
        resp = create_scenario(table, 'scenario_config', term, scenario_config)
        return handle_dynamodb_response(resp)
    
    elif http_method == 'GET':
        resp = get_item(table=table, partition_key="scenario_config", sort_key=term)
        return {
            'statusCode': 200,
            'body': json.dumps(resp)
        } 
    elif http_method == 'DELETE':
        resp = delete_item(table=table, partition_key="scenario_config", sort_key=term)
        return handle_dynamodb_response(resp)