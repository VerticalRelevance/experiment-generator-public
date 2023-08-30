import boto3
import json
import os
import base64
from typing import get_args, Literal, Any, Dict, List, Tuple, Union, _GenericAlias
from chaoslib.types import * #for ease of eval
from shared import *

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

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