import boto3
import json
import os
import base64
import yaml 

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def parse_dynamodb_value(value):
    for data_type in ['S', 'N', 'BOOL', 'M', 'L', 'NULL']:
        if data_type in value:
            return value[data_type]
    return None

def get_all_scenario_configs(table_name, partition_key):
    # Create a DynamoDB client
    dynamodb = boto3.client('dynamodb')
    
    # Create a Paginator for the scan operation
    paginator = dynamodb.get_paginator('scan')
    
    # Specify the table name and the partition key
    scan_params = {
        'TableName': table_name,
        'FilterExpression': '#pk = :pk',
        'ExpressionAttributeNames': {'#pk': 'partition_key'},
        'ExpressionAttributeValues': {':pk': {'S': partition_key}}
    }
    all_scenarios = {}
    # Iterate through the pages of results
    for page in paginator.paginate(**scan_params):

        items = page['Items']
        
        for item in items:
            
            json_item = {key: parse_dynamodb_value(value) for key, value in item.items()}
            print(json_item)
            scenario_items = {key: parse_dynamodb_value(value) for key, value in json_item['scenario'].items()}
            print(scenario_items)
            all_scenarios.update(scenario_items)
    
    return all_scenarios

def handler(event, context):
    
    partition_key = 'scenario_config'

    all_scenario_configs = get_all_scenario_configs(table_name, partition_key)

    yaml_data = yaml.dump(all_scenario_configs, sort_keys=False)

    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/octet-stream; charset=utf-8'},
        'body': yaml_data.encode('utf-8'),
    }
