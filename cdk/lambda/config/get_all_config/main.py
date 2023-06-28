import boto3
import json
import os
import base64
import yaml 
from boto3.dynamodb.types import TypeDeserializer
import decimal

deserializer = TypeDeserializer()
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def get_all_scenario_configs(table_name, partition_key):
    
    # Create a Paginator for the scan operation
    dynamodb = boto3.client('dynamodb')
    paginator = dynamodb.get_paginator('scan')
    
    scan_params = {
        'TableName': table_name,
        'FilterExpression': '#pk = :pk',
        'ExpressionAttributeNames': {'#pk': 'partition_key'},
        'ExpressionAttributeValues': {':pk': {'S': partition_key}}
    }
    all_scenarios = {}
    required = []
    docs = {}
    # Iterate through the pages of results
    for page in paginator.paginate(**scan_params):

        items = page['Items']
        
        for item in items:
            
            deserialized_item = {key: deserializer.deserialize(value) for key, value in item.items()}
            
            print(deserialized_item)
            
            all_scenarios.update(deserialized_item['scenario'])
            required.extend(deserialized_item['required'])
            docs.update({deserialized_item['sort_key']: deserialized_item['documentation']})
    
    return all_scenarios, required, docs
    
def search_keys(dictionary, target_key):
    for key, value in dictionary.items():
        if key == target_key:
            return value
        if isinstance(value, dict):
            result = search_keys(value, target_key)
            if result is not None:
                return result
    return None


def handler(event, context):
    
    partition_key = 'scenario_config'

    all_scenario_configs, required, docs = get_all_scenario_configs(table_name, partition_key)
    
    query_parameters = event['queryStringParameters']
    print(query_parameters)
    req_type=query_parameters['type']
        
    # Convert decimals to proper types
    for arg, val in all_scenario_configs.items():
        if type(val) == decimal.Decimal:
            doc = search_keys(docs, arg)
            print(doc)
            eval_type = eval(doc['Type'])
            all_scenario_configs[arg] = eval_type(val)
            for scenario, doc in docs.items():
                if arg in doc:
                    docs[scenario][arg]['Default'] = eval_type(val)
    
    if req_type == 'arg pairs':
        if required:
            required_config = {req_arg: all_scenario_configs[req_arg] for req_arg in required}
            optional_config = {key: all_scenario_configs[key] for key in all_scenario_configs if key not in required}
            send = {'Required': required_config,
                    'Optional': optional_config}
        else:
            send = {'Optional': optional_config}
    
    elif req_type== 'documentation':
        send = docs

    yaml_data = yaml.dump(send, sort_keys=False)

    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/octet-stream; charset=utf-8'},
        'body': yaml_data.encode('utf-8'),
    }
