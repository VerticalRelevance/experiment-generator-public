from typing import get_args, Literal, Any, Dict, List, Tuple, Union, _GenericAlias

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

def compare_lists(list1, list2):
    # common_elements = set(list1) & set(list2)
    only_in_list1 = set(list1) - set(list2)
    only_in_list2 = set(list2) - set(list1)
    
    return list(only_in_list1), list(only_in_list2)

def get_defaults_and_types(data):
    defaults = {}
    types = {}
    print(data)
    for key, value in data.items():
        print(key, value)
        defaults[key] = value["default"]
        types[key] = value["type"]

    return defaults, types

def outer_inner_types(arg):

    outer = arg.__name__
    outer = eval(outer)
    inner_args = get_args(arg)
    print(inner_args)
    if len(inner_args) == 1:
        inner = inner_args[0]
    elif len(inner_args)>1:
        inner = inner_args
        print("len inner > 1")
    
    print(outer, inner)
    return outer, inner

def isinstance_with_any(obj, cls):
    # isinstance but works with any
    if cls == Any:
        return isinstance(obj, object)
    else:
        return isinstance(obj, cls)

def check_inner_types(iterable, outer, inner):
    print(iterable)
    if isinstance(iterable, outer):
        print('pass outer')
        if isinstance(inner, Tuple) and outer == Dict:
            print('checking dict')
            nested_inner_args = get_args(inner[1])
            if not nested_inner_args:
                print('no nest')
                inner_check = [isinstance_with_any(key, inner[0]) and isinstance_with_any(val, inner[1]) for key, val in iterable.items()]
                print(inner_check)
            elif (isinstance_with_any(key, inner[0]) for key, val in iterable.items()): # if key type matches
                print('check nested')
                nest_out, nest_in = outer_inner_types(inner[1])
                inner_check = [check_inner_types(val, nest_out, nest_in) for val in iterable.values()]
                print(inner_check)
            else:
                return False
        if isinstance(inner, Tuple) and (outer == Tuple or outer == List):
            print('checking tuple/list')
            nested_inner_args = get_args(inner[1])
            if not nested_inner_args:
                print('no nest')
                inner_check = [isinstance_with_any(val, inner[0]) for val in iterable]
                print(inner_check)
            elif (isinstance_with_any(val, inner[0]) for val in iterable): # if key type matches
                print('check nested')
                nest_out, nest_in = outer_inner_types(inner[1])
                inner_check = [check_inner_types(val, nest_out, nest_in) for val in iterable]
                print(inner_check)
            else:
                return False
        elif isinstance(inner, _GenericAlias):
            # for nested param types in param types
            out2, in2 = outer_inner_types(inner)
            if outer == List or outer == Tuple:
                values = iterable
            elif outer==Dict:
                values = iterable.values()
            inner_check = [check_inner_types(val, out2, in2) for val in values]
        else:
            inner_check = [isinstance_with_any(item, inner) for item in iterable]

        return all(inner_check)
    elif outer==Union:
        print('check union')
        for typ in inner:
            if isinstance(typ, _GenericAlias):
                # for nested param types in param types
                out2, in2 = outer_inner_types(typ)
                if check_inner_types(iterable, out2, in2):
                    return True
            else:
                if isinstance_with_any(iterable, typ):
                    return True
        return False
    else:
        return False 

def compare_arg_types(input_args, types):

    arg_types = {k: type(v).__name__ for k, v in input_args.items()}
    print("input args:", input_args)

    diff_values = {}

    for key, value in types.items():
        if value and key in arg_types and arg_types[key] != value:
            print(value, arg_types.get(key))
            try:
                print("checking for nested or literal types..")
                arg_type = eval(value)
                outer_type, inner_type = outer_inner_types(arg_type)
                print(outer_type, inner_type)
                if outer_type == Literal and input_args[key] not in inner_type:
                    diff_values[key] = value                 
                elif not check_inner_types(input_args[key], outer_type, inner_type):
                    diff_values[key] = value
            except Exception as e:
                print("Error:", str(e))
                diff_values[key] = value
    return diff_values

def build_method_item(func, table, additionals=None):

    signature = get_item(table, 'packages', func)
    item = {
        'name': func,
        'type': signature['import_path'].split('.')[-1][:-1], # whether in actions or probes file.
        'provider': {
            'type': 'python',
            'module': signature['import_path'],
            'func': signature['function_name'],
            'arguments': {arg: f"${{{arg}}}" for arg in signature['args'].keys()},
        }
    }
    
    if additionals:
        item.update(additionals)
        
    return item, signature