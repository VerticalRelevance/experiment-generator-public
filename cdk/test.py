from typing import get_args, Any, Dict, List, Optional, Tuple, Union, _GenericAlias
import types


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

from types_cl import *
# test = ['a', 'b', '1']
# arg_type = eval("List[str]")

# test = {
#     "test": {
#         "test2": {
#             "test3" : "final"
#         }
#     }
# }
# arg_type = eval("Dict[str, Dict[str, str]]")

# test = [{'type': 'Ready', 'status': 'False', 'lastTransitionTime': '2023-01-01T00:00:00Z'}, {'type': 'www.example.com/feature-1', 'status': 'False', 'lastTransitionTime': '2023-01-01T00:00:00Z'}]
# arg_type = eval("List[Dict[str, str]]")

# arg_type = eval("Secrets")
# test = {
#     "test": {
#         "test": "fin"
#     }
# }

arg_type = eval("Tuple[str]")
test = ('test', 'test')
outer_type, inner_type = outer_inner_types(arg_type)

print(check_inner_types(test, outer_type, inner_type))

# from typing import Literal

# def accepts_only_four(x: Literal[4]):
#     print(x)

# accepts_only_four(10)

# ttype = "Literal[4, 5, 6]"
# atype = eval(ttype)
# test = 4
# outer_type, inner_type = outer_inner_types(atype)
# if outer_type == Literal:
#     print(test in inner_type)

