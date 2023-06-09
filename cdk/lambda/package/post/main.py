import os
import ast
import boto3
import zipfile
import base64
import shutil

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
    module_path = module_path.replace(folder_path+"/", '', 1)  # Remove leading dir
    
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
    all_args = node.args.args
    args = [arg.arg for arg in all_args]
    defaults = [None] * (len(args) - len(node.args.defaults)) + node.args.defaults

    # Extract argument types and default values
    arg_types = []
    default_values = []
    for arg, default in zip(all_args, defaults):
        if arg.annotation:
            arg_types.append(ast.unparse(arg.annotation).strip())
        else:
            arg_types.append('')
        if default:
            default_values.append(ast.literal_eval(ast.unparse(default).strip()))
        else:
            default_values.append(None)

    signature = {
        'function_name': function_name,
        'package': module_path.split("/")[0],
        'import_path': module_path.replace('/','.'),
        'args': {arg: {'type': type_, 'default': default_} for arg, type_, default_ in zip(args, arg_types, default_values)},
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
    
    # Note, package/module/folder are used interchangably
    unzip_target = '/tmp/module'
    os.mkdir(unzip_target)

    # Extract the contents of the zip file
    with zipfile.ZipFile(temp_zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(unzip_target)
        
    table_name = os.environ['TABLE_NAME']
    bucket = os.environ['BUCKET_NAME']
    
    try:
        # Extract function signatures
        signatures = extract_function_signatures(unzip_target)
        print(signatures)

        # Send signatures to DynamoDB
        send_to_dynamodb(signatures, table_name)

        response = {
            'statusCode': 200,
            'body': 'Success'
        }
    except Exception as e:
        print(e)
        response = {
            'statusCode': 500,
            'body': f"Error: {e}"
        }
    
    shutil.rmtree(unzip_target)
    
    return response
