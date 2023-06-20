import boto3
import json
import os
import base64
import yaml

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)  
s3 = boto3.client('s3')
bucket_name = os.environ['BUCKET_NAME']

# For DynamoDB 
def get_item(table, partition_key, sort_key):
    key = {
        'partition_key': partition_key,
        'sort_key': sort_key
    }
    print(key)
    response = table.get_item(Key=key)
    item = response.get('Item')
    return item
    
def get_yaml_from_s3(bucket_name, object_key, load=True):
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    yaml_data = response['Body'].read().decode('utf-8')
    if load:
        yaml_data = yaml.safe_load(yaml_data)
    return yaml_data

def handler(event, context):
    http_method = event['httpMethod']
    print(http_method)
    
    if http_method == "GET":
        query_parameters = event['queryStringParameters']
        print(query_parameters)
        
        # List approach/ not working with query params
        # exp_names=query_parameters['experiment_names']
        # files = [get_yaml_from_s3(bucket_name, name, load=False) for name in exp_names]
        # all_yaml_data = '\n---\n'.join(files)
        
        exp_name=query_parameters['experiment_name']
        print(exp_name)
        file = get_yaml_from_s3(bucket_name, exp_name, load=False)
        # all_yaml_data = '\n---\n'.join(files)

        return {
            'statusCode': 200,
            'headers': { 'Content-Type': 'application/octet-stream; charset=utf-8'},
            'body': file,
        }
    else:
        data = base64.b64decode(event['body'])
        data = json.loads(data)

        # experiment = {
        #     'title': '',
        #     'version': '1.0.0',
        #     'description': '',
        #     'configuration': {},
        #     'method': [],
        #     'steady-state-hypothesis' : {
        #         'title': 'steady state probe(s)',
        #     }
        # }

        if http_method == "POST" or http_method == "PUT":
            for exp_name, exp_map in data.items():
                if http_method == "PUT":
                    experiment = get_yaml_from_s3(bucket_name, exp_name)
                else:
                    experiment = {}
        
                experiment['title'] = exp_name # change?
                experiment['description'] = exp_name

                term = exp_map.get('exp_term')
                target = exp_map.get('target')
                
                if term:
                    experiment['method'] = get_item(table, 'methods', term)['method']
                if target:
                    experiment['steady-state-hypothesis'] = get_item(table, 'steady_state', target)['steady_state']
                if term:
                    experiment['configuration'] = get_item(table, 'scenario_config', term)['scenario']
                if target:
                    # Layer target configs on top as they take priority
                    print(experiment)
                    target_config = get_item(table, 'target_config', target)['config']
                    experiment['configuration'].update(target_config)

                if http_method == "POST" and 'method' not in experiment.keys():
                    return {
                        'statusCode': 500,
                        'body': "Need at least a method/term",
                    } 

                yaml_data = yaml.dump(experiment, sort_keys=False)

                s3.put_object(Body=yaml_data, Bucket=bucket_name, Key=exp_name)

                return {
                    'statusCode': 200,
                    'headers': { 'Content-Type': 'application/octet-stream; charset=utf-8'},
                    'body': yaml_data.encode('utf-8'),
                }
        elif http_method == "DELETE":
            for exp_name in data['experiment_names']:
                s3.delete_object(Bucket=bucket_name, Key=exp_name)
            return {
                'statusCode': 200,
                'body': "Deleted experiment(s)"
            }