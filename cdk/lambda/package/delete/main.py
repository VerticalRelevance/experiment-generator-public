import boto3
import json
import base64
import os

def delete_records(partition_key_value, attribute_value, table):

    response = table.scan(
        FilterExpression='partition_key = :partition_key_value and pacakge_name = :attribute_value',
        ExpressionAttributeValues={
            ':partition_key_value': partition_key_value,
            ':attribute_value': attribute_value
        }
    )

    with table.batch_writer() as batch:
        for item in response['Items']:
            batch.delete_item(
                Key={
                    'partition_key': item['partition_key'],
                    'sort_key': item['sort_key']
                }
            )

    print("Records deleted successfully.")

def handler(event, context):
    try:
        # Extracting the module value from the input
        data = base64.b64decode(event['body'])
        package = json.loads(data)['package']

        # Deleting DynamoDB records
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ['TABLE_NAME']
        table = dynamodb.Table(table_name)  

        delete_records('packages', package, table)

        return {
            'statusCode': 200,
            'body': f'All items with the partition key {package} have been deleted.'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Processing failed. Error: {str(e)}'
        }
