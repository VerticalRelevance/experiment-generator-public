import boto3
import json
import os
import base64
import yaml
import decimal

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
        
        exp_name=query_parameters['experiment scenario']
        print(exp_name)
        file = get_yaml_from_s3(bucket_name, exp_name, load=False)

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

                term = exp_map.get('experiment scenario')
                target = exp_map.get('target application')
                
                if term:
                    experiment['method'] = get_item(table, 'methods', term)['method']
                    sc = get_item(table, 'scenario_config', term)
                    experiment['configuration'] = sc['scenario']

                if target:

                    try:
                        experiment['steady-state-hypothesis'] = {
                            'title': f"{target} steady state",
                            'probes': get_item(table, 'steady_state', target)['steady_state']
                        }
                        
                    except Exception as e:
                        print(f"An exception occurred: {e}")

                    # Layer target configs on top as they take priority
                    print(experiment)
                    target_app = get_item(table, 'target_config', target)
                    experiment['configuration'].update(target_app['config'])

                if http_method == "POST" and 'method' not in experiment.keys():
                    return {
                        'statusCode': 500,
                        'body': "Need at least a method/term",
                    }
                    
                print(experiment)
                
                # DyanmoDB does not diffrentiate between diffrent numeric types and returns all numerics as python decimals 
                # Look up the correct type and convert
                for k, v in experiment['configuration'].items():
                    if type(v) == decimal.Decimal:
                        print(sc["scenario_function_mappings"])
                        arg_type = None
                        
                        for func, args in sc["scenario_function_mappings"].items():
                            if k in args.keys():
                                sig = get_item(table, "packages", func)
                                arg_type = sig['args'][k]['type']
                                break
                            
                        if not arg_type:
                            types = target_app['types']
                            arg_type = types[k]
                            
                        # eval and enforce correct type
                        print(arg_type)
                        _arg_type_ = eval(arg_type)
                        experiment['configuration'][k] = _arg_type_(v)
                        
                for item in experiment['method']:
                    if 'pauses' in item:
                        for k, v in item['pauses'].items():
                            item['pauses'][k] = int(v)

                yaml_data = yaml.dump(experiment, sort_keys=False)

                s3.put_object(Body=yaml_data, Bucket=bucket_name, Key=exp_name) # prefix

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