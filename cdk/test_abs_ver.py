import os
import ast
import yaml


def extract_function_signatures(folder_path, output_file):
    signatures = []
    root_folder_name = os.path.basename(folder_path)
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.py') and not file_name.startswith('__'):
                file_path = os.path.join(root, file_name)
                signatures.extend(process_file(file_path))

    write_signatures_to_yaml(signatures, root_folder_name, output_file)


def process_file(file_path):
    with open(file_path, 'r') as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            print(f"Syntax error in file: {file_path}")
            return []

    return extract_function_signatures_from_tree(tree)


def extract_function_signatures_from_tree(tree):
    signatures = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            signature = get_function_signature(node)
            signatures.append(signature)
    return signatures


def get_function_signature(node):
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
        'name': function_name,
        'args': {arg: type_ for arg, type_ in zip(args, arg_types)},
    }
    return signature


def write_signatures_to_yaml(signatures, root_folder_name, output_file):
    data = {
        'module': root_folder_name,
        'signatures': signatures,
    }

    with open(output_file, 'w') as file:
        yaml.dump(data, file, sort_keys=False)

# Example usage
folder_path = r'tmp/testing/file.py'
# extract_function_signatures(folder_path, 'sample.yaml')
# import zipfile
# temp_zip_file_path = 'testing.zip'
# with zipfile.ZipFile(temp_zip_file_path, 'r') as zip_ref:
#     zip_ref.extractall('tmp')
#     name = zip_ref.namelist()
#     print(name)
