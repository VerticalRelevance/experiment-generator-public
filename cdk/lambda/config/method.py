import boto3
import json
import os
import base64
from shared import *

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  

def handler(event, context):
    
    # Extract values
    http_method = event['httpMethod']
    if http_method != "GET":
        data = base64.b64decode(event['body'])
    else:
        query_parameters = event['queryStringParameters']
        print(query_parameters)
        data=query_parameters['term']

    if http_method == 'POST':
        mappings = json.loads(data)
        for term, functions in mappings.items():
            method = []
            for func in functions:
                additionals = {}
                if isinstance(func, dict):
                    print(func)
                    for func_name, val in func.items():
                        if 'pauses' in val:
                            if 'before' in val['pauses']:
                                if type(val['pauses']['before']) == int:
                                    additionals.update({'pauses': val['pauses']})
                            if 'after' in val['pauses']:
                                if type(val['pauses']['after']) == int:
                                    additionals.update({'pauses': val['pauses']})
                        if 'background' in val:
                            if type(val['background']) == bool:
                                additionals.update({'background': val['background']})
                    item = build_method_item(func_name, table, additionals)[0]
                    method.append(item)
                else:
                    item = build_method_item(func, table)[0]
                    method.append(item)

            resp = create_item(table=table, partition_key="methods", sort_key=term, send={'method': method})

            return handle_dynamodb_response(resp)
        
    # For get and delete, we need only the 'term', so we take the data variable as the term
    elif http_method == 'GET':
        resp = get_item(table=table, partition_key="methods", sort_key=data)
        
        # cant json dump decimals, make int
        for item in resp['method']:
            if 'pauses' in item:
                for k, v in item['pauses'].items():
                    item['pauses'][k] = int(v)
        return {
            'statusCode': 200,
            'body': json.dumps(resp['method'])
        } 
    elif http_method == 'DELETE':
        data = json.loads(data)
        print(data)
        resp = delete_item(table=table, partition_key="methods", sort_key=data)
        return handle_dynamodb_response(resp)