import boto3
import json
import os
import base64

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def create_item(table, partition_key, sort_key, config):
    item = {
        'partition_key' : partition_key,
        'sort_key' : sort_key,
        'config': config
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

def handler(event, context):
    http_method = event['httpMethod']
    
    if http_method == "GET":
        query_parameters = event['queryStringParameters']
        print(query_parameters)
        data=query_parameters['term']
        resp = get_item(table=table, partition_key="target_config", sort_key=data)
        return {
            'statusCode': 200,
            'body': json.dumps(resp)
        } 
    else:
        data = base64.b64decode(event['body'])
        data = json.loads(data)
    
        for target, config in data:
            if http_method == "POST":
                resp = create_item(table, 'target_config', target, config)
                return handle_dynamodb_response(resp)
            elif http_method=="PUT":
                existing_config = get_item(table, 'target_config', target)['config']
                existing_config.update[config]
                resp = create_item(table, 'target_config', target, config)
                return handle_dynamodb_response(resp)
            elif http_method == "DELETE":
                resp = delete_item(table, 'target_config', target)
                return handle_dynamodb_response(resp)