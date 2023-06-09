import boto3
import json
import base64
import os

def handler(event, context):
    try:
        # Extracting the module value from the input
        data = base64.b64decode(event['body'])
        module = json.loads(data)['module']

        partition_key = 'package'
        sort_key = 'function_name'

        # Deleting DynamoDB records
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ['TABLE_NAME']
        table = dynamodb.Table(table_name)  

        # Scan for items with the specified partition key
        response = table.scan(
            FilterExpression=f'{partition_key} = :key_value',
            ExpressionAttributeValues={
                ':key_value': module
            }
        )

        # Delete each item found in the scan result
        with table.batch_writer() as batch:
            for item in response['Items']:
                batch.delete_item(
                    Key={
                        partition_key: item[partition_key],
                        sort_key: item[sort_key]
                    }
                )

        return {
            'statusCode': 200,
            'body': f'All items with the partition key {module} have been deleted.'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Processing failed. Error: {str(e)}'
        }
