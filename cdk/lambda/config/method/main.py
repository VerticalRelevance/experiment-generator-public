import boto3
import json
import os
import base64

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def create_item(table, partition_key, sort_key, method):
    item = {
        'partition_key' : partition_key,
        'sort_key' : sort_key,
        'method': method
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

def build_method_item(func, table):

    signature = get_item(table, 'packages', func)
    item = {
        'name': func,
        'type': signature['import_path'].split('.')[-2], # whether in actions or probes file. What do we do if its in shared?
        'provider': {
            'type': 'python',
            'module': signature['import_path'],
            'func': func,
            'arguments': {arg: f"${{{arg}}}" for arg in signature['args'].keys()},
        }
    }
    return item

def handle_dynamodb_response(response):
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
    
    # Extract values
    data = base64.b64decode(event['body'])
    mappings = json.loads(data)
    method = []

    # Cycle through term-function mappings and handle method crud
    for term, functions in mappings.items():
        method = [build_method_item(func, table) for func in functions]
            
        http_method = event['httpMethod']
        
        if http_method == 'POST':
            resp = create_item(table=table, partition_key="methods", sort_key=term, method=method)
            return handle_dynamodb_response(resp)
        elif http_method == 'GET':
            resp = get_item(table=table, partition_key="methods", sort_key=term)
            return handle_dynamodb_response(resp)
        elif http_method == 'DELETE':
            resp = delete_item(table=table, partition_key="methods", sort_key=term)
            return handle_dynamodb_response(resp)

    
