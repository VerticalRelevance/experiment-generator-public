import boto3
import json
import os
import base64

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def create_item(table, partition_key, sort_key, scenario):
    item = {
        'partition_key' : partition_key,
        'sort_key' : sort_key,
        'scenario': scenario
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
            diff_values[key] = value
    return diff_values

def handler(event, context):
    
    # Extract values
    data = base64.b64decode(event['body'])
    mappings = json.loads(data)
    term = mappings['term']
    parameters = mappings['scenario']
    
    scenario_config = {}

    # Get arguments from method
    method = get_item(table, 'methods', term)['method']
    arguments = {item['name']: item['provider']['arguments'].keys() for item in method}
    print(arguments)

    for func, args in arguments.items():
        signature = get_item(table, 'packages', func)
        defaults, types = get_defaults_and_types(signature['args'])
        if func in parameters:
            only_args, only_params = compare_lists(args, parameters[func].keys())
            if not only_args and not only_params:
                diff = compare_arg_types(parameters[func], types)
                if not diff:
                    scenario_config.update(parameters[func])
                else:
                    return {
                        'statusCode': 500,
                        'body': f"The following function types do not match: {diff}"
                    }
            elif only_args:
                has_defaults = {arg:defaults.get(arg) for arg in only_args}
                none_values = [key for key, value in has_defaults.items() if value is None]
                if not none_values:
                    scenario_config.update(parameters[func])
                    scenario_config.update(has_defaults)
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
    resp = create_item(table, 'scenario_config', term, scenario_config)
    return handle_dynamodb_response(resp)


            




    
