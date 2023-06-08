import os
import ast
import boto3
import zipfile
import base64

def extract_function_signatures(folder_path):
    signatures = []
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.py') and not file_name.startswith('__'):
                file_path = os.path.join(root, file_name)
                signatures.extend(process_file(file_path, folder_path))

    return signatures


def process_file(file_path, folder_path):
    with open(file_path, 'r') as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            print(f"Syntax error in file: {file_path}")

    module_path = file_path.replace("\\", "/")
    module_path = module_path.replace(folder_path+"/", '', 1)  # Remove leading directory
    
    return extract_function_signatures_from_tree(tree, module_path)

def extract_function_signatures_from_tree(tree, module_path):
    signatures = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            signature = get_function_signature(node, module_path)
            signatures.append(signature)
    return signatures


def get_function_signature(node, module_path):
    function_name = node.name
    args = [arg.arg for arg in node.args.args]
    defaults = [None] * (len(args) - len(node.args.defaults)) + node.args.defaults

    # Extract argument types
    arg_types = []
    for arg in node.args.args:
        if arg.annotation:
            arg_types.append(ast.unparse(arg.annotation).strip())
        else:
            arg_types.append('')

    signature = {
        'function_name': function_name,
        'module': os.path.split(module_path)[0],
        'full_path': module_path,
        'args': {arg: type_ for arg, type_ in zip(args, arg_types)},
    }
    return signature

def send_to_dynamodb(signatures, table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    with table.batch_writer() as batch:
        for signature in signatures:
            item = signature
            batch.put_item(Item=item)

def upload_directory_to_s3(local_directory, bucket_name, s3_directory):
    s3 = boto3.client('s3')
    
    for root, dirs, files in os.walk(local_directory):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_directory)
            s3_path = os.path.join(s3_directory, relative_path).replace("\\", "/")
            s3.upload_file(local_path, bucket_name, s3_path)
            print(f"Uploaded {local_path} to S3 path: {s3_path}")

def handler(event, context):

    data = base64.b64decode(event['body'])
    # Create a temporary file path to save the zip file
    temp_zip_file_path = f'/tmp/temp_zip'
    with open(temp_zip_file_path, 'wb') as temp_zip_file:
        temp_zip_file.write(data)
    
    unzip_target = '/tmp/module'
    os.mkdir(unzip_target)

    # Extract the contents of the zip file to a folder with the same name as the zip file
    with zipfile.ZipFile(temp_zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(unzip_target)
        
    table_name = os.environ['TABLE_NAME']
    bucket = os.environ['BUCKET_NAME']
    
    try:
        # Extract function signatures
        signatures = extract_function_signatures(unzip_target)
        # Send signatures to DynamoDB and upload module to s3
        send_to_dynamodb(signatures, table_name)
        upload_directory_to_s3(unzip_target, bucket, 'modules')

        response = {
            'statusCode': 200,
            'body': 'Success'
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': "An error occurred during processing."
        }
    
    return response
