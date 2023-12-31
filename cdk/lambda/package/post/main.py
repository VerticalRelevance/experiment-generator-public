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
            if file_name == 'actions.py' or file_name== 'probes.py':
            # if file_name != 'shared.py' and file_name.endswith('.py') and not file_name.startswith('__'): 
                file_path = os.path.join(root, file_name)
                signatures.extend(process_file(file_path, folder_path))

    return signatures


def process_file(file_path, folder_path):
    # Get ast tree
    with open(file_path, 'r') as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            print(f"Syntax error in file: {file_path}")

    # Replace \ with / and remove leading dir
    module_path = file_path.replace("\\", "/")
    module_path = module_path.replace(folder_path+"/", '', 1)  
    
    return extract_function_signatures_from_tree(tree, module_path)

def extract_function_signatures_from_tree(tree, module_path):
    signatures = []
    for node in tree.body:
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
            default_values.append("NoDefault")

    import_path = module_path.replace('/','.')
    import_path = import_path.replace('.py','')

    signature = {
        'partition_key': 'packages',
        'sort_key': f"{import_path}.{function_name}",
        'package_name': module_path.split("/")[0],
        'import_path': import_path,
        'function_name': function_name,
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
