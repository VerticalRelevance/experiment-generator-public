import boto3
import json
import os
import base64
from typing import get_args, Literal, Any, Union
import types
from types_cl import *


dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def create_item(table, partition_key, sort_key, send):
    item = {
        'partition_key' : partition_key,
        'sort_key' : sort_key
    }
    item.update(send)
    print(item)
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

def build_method_item(func, table):

    signature = get_item(table, 'packages', func)
    item = {
        'name': func,
        'type': signature['import_path'].split('.')[-1][:-1], # whether in actions or probes file.
        'provider': {
            'type': 'python',
            'module': signature['import_path'],
            'func': signature['function_name'],
            'arguments': {arg: f"${{{arg}}}" for arg in signature['args'].keys()},
        }
    }
    return item, signature

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
    print(data)
    for key, value in data.items():
        print(key, value)
        defaults[key] = value["default"]
        types[key] = value["type"]

    return defaults, types

def outer_inner_types(arg):

    outer = arg.__name__
    outer = eval(outer)
    inner_args = get_args(arg)
    print(inner_args)
    if len(inner_args) == 1:
        inner = inner_args[0]
    elif len(inner_args)>1:
        inner = inner_args
        print("len inner > 1")
    
    print(outer, inner)
    return outer, inner

def isinstance_with_any(obj, cls):
    # isinstance but works with any
    if cls == Any:
        return isinstance(obj, object)
    else:
        return isinstance(obj, cls)

def check_inner_types(iterable, outer, inner):
    print(iterable)
    if type(iterable)==outer:
        if isinstance(inner, tuple) and outer == dict:
            print('checking dict')
            nested_inner_args = get_args(inner[1])
            if not nested_inner_args:
                print('no nest')
                inner_check = [isinstance_with_any(key, inner[0]) and isinstance_with_any(val, inner[1]) for key, val in iterable.items()]
                print(inner_check)
            elif (isinstance_with_any(key, inner[0]) for key, val in iterable.items()): # if key type matches
                print('check nested')
                nest_out, nest_in = outer_inner_types(inner[1])
                inner_check = [check_inner_types(val, nest_out, nest_in) for val in iterable.values()]
                print(inner_check)
            else:
                return False
        if isinstance(inner, tuple) and (outer == tuple or outer == list):
            print('checking tuple/list')
            nested_inner_args = get_args(inner[1])
            if not nested_inner_args:
                print('no nest')
                inner_check = [isinstance_with_any(val, inner[0]) for val in iterable]
                print(inner_check)
            elif (isinstance_with_any(val, inner[0]) for val in iterable): # if key type matches
                print('check nested')
                nest_out, nest_in = outer_inner_types(inner[1])
                inner_check = [check_inner_types(val, nest_out, nest_in) for val in iterable]
                print(inner_check)
            else:
                return False
        elif isinstance(inner, types.GenericAlias):
            # for nested param types in param types
            out2, in2 = outer_inner_types(inner)
            if outer == list or tuple:
                values = iterable
            elif outer == dict:
                values = iterable.values()
            inner_check = [check_inner_types(val, out2, in2) for val in values]
        else:
            inner_check = [isinstance_with_any(item, inner) for item in iterable]

        return all(inner_check)
    elif outer==Union:
        print('check union')
        for typ in inner:
            if isinstance(typ, types.GenericAlias):
                # for nested param types in param types
                out2, in2 = outer_inner_types(typ)
                if check_inner_types(iterable, out2, in2):
                    return True
            else:
                if isinstance_with_any(iterable, typ):
                    return True
        return False
    else:
        return False 

def compare_arg_types(input_args, types):

    arg_types = {k: type(v).__name__ for k, v in input_args.items()}
    print("input args:", input_args)

    diff_values = {}

    for key, value in types.items():
        if value and key in arg_types and arg_types[key] != value:
            print(value, arg_types.get(key))
            try:
                print("checking for nested or literal types..")
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
    print(http_method)
    
    if http_method == "GET":
        query_parameters = event['queryStringParameters']
        print(query_parameters)
        data=query_parameters['term']
        resp_tc = get_item(table=table, partition_key="target_config", sort_key=data)
        resp_ss = get_item(table=table, partition_key="steady_state", sort_key=data)

        return_data = {
            'Config': resp_tc['config'],
            'Steady State': resp_ss['steady_state']
        }
        return {
            'statusCode': 200,
            'body': json.dumps(return_data)
        } 
    else:
        data = base64.b64decode(event['body'])
        data = json.loads(data)
        responses = []
        print(data)

        if 'Parameters' in data:
            if http_method == "POST" or http_method=="PUT":
                for target, config in data['Parameters'].items():
                    types = {arg: type(value).__name__ for arg, value in config.items()}
                    if http_method == "POST":
                        resp = create_item(table, 'target_config', target, {"config": config, "types": types})
                        responses.append(handle_dynamodb_response(resp))
                    elif http_method=="PUT":
                        existing = get_item(table, 'target_config', target)
                        existing['config'].update(config)
                        existing['types'].update(types)
                        resp = create_item(table, 'target_config', target, {"config": existing['config'], "types": existing['types']})
                        responses.append(handle_dynamodb_response(resp))
            elif http_method == "DELETE":
                for tc in data['Parameters']:
            
                    resp = delete_item(table, 'target_config', tc)
                    responses.append(handle_dynamodb_response(resp))
                
        if 'Steady state' in data:
            print("ss process")
            if http_method == 'POST' or http_method=="PUT":
                for target, steady_state in data['Steady state'].items():
                    # Since order matters, for steady state post and put will act identically
                    method_items = [build_method_item(func, table) for func in steady_state]

                    # since method items returns method item and sig pair, split it
                    probes = [item[0] for item in method_items]
                    signatures = [item[1] for item in method_items]

                    print(probes)
                    print(signatures)

                    non_probes = [probe['name'] for probe in probes if probe['type'] != 'probe']
                    print(non_probes)
                    if non_probes:
                        return {
                            'statusCode': 500,
                            'body': f"The following functions are not probes: {non_probes}"
                        }
                    elif 'Parameters' in data:
                        input_args = data['Parameters'][target]
                        all_args = {}
                        defaults, types = {}, {}
                        for probe, sig in zip(probes, signatures):
                            all_args.update(probe['provider']['arguments'])
                            def_, type_ = get_defaults_and_types(sig['args'])
                            defaults.update(def_)
                            types.update(type_)

                        diff = compare_arg_types(input_args, types)
                        only_all_args, only_in_args = compare_lists(all_args.keys(), input_args.keys())

                        if diff:
                            return {
                                'statusCode': 500,
                                'body': f"The following arguments do not have the correct type: {diff}"
                            }


                        elif not only_all_args and not only_in_args:

                             # diff is none if no diffrence - update and prepare to send
                            resp = create_item(table=table, partition_key="steady_state", sort_key=target, send={"steady_state": probes})
                                
                        elif only_all_args:

                            # only_args -> means input/parameter args are less than required args. So we check for default
                            has_defaults = {arg:defaults.get(arg) for arg in only_all_args}
                            none_values = [key for key, value in has_defaults.items() if value == "NoDefault"]

                            # update if default args + input args satisfy total argument requirements
                            if not none_values:
                                
                                # Update target config with default arg vals
                                existing_config = get_item(table, 'target_config', target)['config']
                                existing_config.update(has_defaults)
                                resp = create_item(table, 'target_config', target, {"config": existing_config})
                                responses.append(handle_dynamodb_response(resp))
                                
                                # create steady state
                                resp = create_item(table=table, partition_key="steady_state", sort_key=target, send={"steady_state": probes})
                                responses.append(handle_dynamodb_response(resp))
                                
                            else:
                                return {
                                    'statusCode': 500,
                                    'body': f"The function steady state probes require the following arguments: {none_values}"
                                }
                        
                    else:
                        return {
                            'statusCode': 500,
                            'body': "Please include accopanying function arguments for steady state functions"
                        }    
                    
                    responses.append(handle_dynamodb_response(resp))
                
            elif http_method == "DELETE":
                for ss in data['Steady state']:
            
                    resp = delete_item(table, 'steady_state', ss)
                    responses.append(handle_dynamodb_response(resp))
                    
        
        # Check status codes and send return appropriately 
        print(responses)
        status_codes = [resp["statusCode"] for resp in responses]

        if all(code == 200 for code in status_codes):
            return {
                'statusCode': 200,
                'body': "All action(s) successful"
            }         
        else:
            return {
                'statusCode': 500,
                'body': f"Errors: {responses}"
            } 