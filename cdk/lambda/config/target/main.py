import boto3
import json
import os
import base64

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
        'type': signature['import_path'].split('.')[-2][:-1], # whether in actions or probes file. What do we do if its in shared?
        'provider': {
            'type': 'python',
            'module': signature['import_path'],
            'func': func,
            'arguments': {arg: f"${{{arg}}}" for arg in signature['args'].keys()},
        }
    }
    return item

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
    print(http_method)
    
    if http_method == "GET":
        query_parameters = event['queryStringParameters']
        print(query_parameters)
        data=query_parameters['term']
        resp_tc = get_item(table=table, partition_key="target_config", sort_key=data)
        resp_ss = get_item(table=table, partition_key="steady_state", sort_key=data)

        return_data = {
            'target_config': resp_tc,
            'steady_state:': resp_ss
        }
        return {
            'statusCode': 200,
            'body': json.dumps(return_data)
        } 
    else:
        data = base64.b64decode(event['body'])
        data = json.loads(data)
        responses = []

        if 'target_config' in data:
            if http_method == "POST" or http_method=="PUT":
                for target, config in data['target_config'].items():
                    if http_method == "POST":
                        resp = create_item(table, 'target_config', target, {"config": config})
                        responses.append(handle_dynamodb_response(resp))
                    elif http_method=="PUT":
                        existing_config = get_item(table, 'target_config', target)['config']
                        print(existing_config)
                        existing_config.update(config)
                        print(existing_config)
                        resp = create_item(table, 'target_config', target, {"config": existing_config})
                        responses.append(handle_dynamodb_response(resp))
            elif http_method == "DELETE":
                for tc in data['target_config']:
            
                    resp = delete_item(table, 'target_config', tc)
                    responses.append(handle_dynamodb_response(resp))
                
        if 'steady_state' in data:
            print("ss process")
            if http_method == 'POST' or http_method=="PUT":
                for target, steady_state in data['steady_state'].items():
                    # Since order matters, for steady state post and put will act identically
                    probes = [build_method_item(func, table) for func in steady_state]
                    non_probes = [probe['name'] for probe in probes if probe['type'] != 'probe']
                    
                    if non_probes:
                        return {
                            'statusCode': 500,
                            'body': f"The following functions are not probes: {non_probes}"
                        }
                    else:
                        resp = create_item(table=table, partition_key="steady_state", sort_key=target, send={"steady_state": probes})
    
                    
                    responses.append(handle_dynamodb_response(resp))
                
            elif http_method == "DELETE":
                for ss in data['steady_state']:
            
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