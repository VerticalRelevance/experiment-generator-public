import boto3
import json
import os
import base64
from typing import get_args, Literal
from decimal import Decimal

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


    item = {
        'partition_key' : partition_key,
        'sort_key' : sort_key,
        'scenario': scenario, # what will be overlaid in experiment configuration
        'scenario_function_mappings': scenario_dict, # preserves function->arg mapping (needed for update)
        'required': no_defaults,
        'documentation': doc
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

def outer_inner_types(arg):

    outer = arg.__name__
    outer = eval(outer)
    inner_args = get_args(arg)
    if len(inner_args) == 1:
        inner = inner_args[0]
    elif len(inner_args)>1:
        inner = inner_args
    
    print(inner, outer)
    return outer, inner

def check_inner_types(iterable, outer, inner):
    print(iterable)
    if type(iterable)==outer:
        if isinstance(inner, tuple):
            nested_inner_args = get_args(inner[1])
            if not nested_inner_args:
                print('no nest')
                inner_check = [isinstance(key, inner[0]) and isinstance(val, inner[1]) for key, val in iterable.items()]
                print(inner_check)
            elif (isinstance(key, inner[0]) for key, val in iterable.items()): # if key type matches
                print('check nested')
                nest_out, nest_in = outer_inner_types(inner[1])
                print(nest_out, nest_in)
                inner_check = [check_inner_types(val, nest_out, nest_in) for val in iterable.values()]
                print(inner_check)
            else:
                return False
        else:
            inner_check = [isinstance(item, inner) for item in iterable]

        return all(inner_check)    
    else:
        return False 

def compare_arg_types(input_args, types):

    arg_types = {k: type(v).__name__ for k, v in input_args.items()}

    diff_values = {}

    for key, value in types.items():
        if arg_types.get(key) and arg_types[key] != value:
            print(value, arg_types.get(key))
            try:
                print("checking for nested types..")
                arg_type = eval(value.lower())
                outer_type, inner_type = outer_inner_types(arg_type)
                print(outer_type, inner_type)
                if outer_type == Literal and input_args[key] not in inner_type:
                    diff_values[key] = value                 
                elif not check_inner_types(input_args[key], outer_type, inner_type):
                    diff_values[key] = value
            except Exception as e:
                print("Error:", str(e))
                diff_values[key] = value
    return diff_values

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

                    # diff is none if no diffrence - update and prepare to send
                    scenario_config.update({func: parameters[func]})

                elif only_args:
                    
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