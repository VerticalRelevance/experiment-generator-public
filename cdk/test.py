# import inspect
# import typing


# def testfunc(arg1: list[str]):
#     '''sample function'''
#     for arg in arg1:
#         print(arg)

# def inner_type_match(func):
#     '''gets type of signature'''
#     arg = inspect.signature(func)
#     print(arg.parameters)

#     # note exits after first iteration
#     for param in arg.parameters:
#         print(param)
#         step1 = arg.parameters[param].annotation
#         outer = step1.__name__
#         step2 = step1.__args__
#         inner = step2[0].__name__
#         return outer, inner

# # typefunc(testfunc)

# # import re

# # test = ['a', 'b', 'c']
# # in_type = type(test).__name__
# # arg_type = "List[str]"
# # if in_type != arg_type:
# #     if in_type in arg_type.lower():
# #         val_in_brackets = r"\[(.*?)\]"  
# #         match = re.findall(val_in_brackets, arg_type)
# #         # iterate over in_type to see if each value matches match[0]


# ttype="list[str]"
# exec(f"""def a(x: {ttype}):
#     return x""")
# print(a(test))
# print(inner_type_match(a))

from typing import get_args, Any, Union, Dict
import types

# test = ['a', 'b', 'c']
# test = {
#     "test": {
#         "test2": {
#             "test3" : "final"
#         }
#     }
# }

test = [{'type': 'Ready', 'status': 'False', 'lastTransitionTime': '2023-01-01T00:00:00Z'}, {'type': 'www.example.com/feature-1', 'status': 'False', 'lastTransitionTime': '2023-01-01T00:00:00Z'}]

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
        if isinstance(inner, tuple) and (outer == dict or outer == Dict):
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
        if isinstance(inner, tuple) and (outer == tuple or outer == list):
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
        elif isinstance(inner, types.GenericAlias):
            # for nested param types in param types
            out2, in2 = outer_inner_types(inner)
            if outer == list or tuple:
                values = iterable
            elif outer == dict or outer==Dict:
                values = iterable.values()
            inner_check = [check_inner_types(val, out2, in2) for val in values]
        else:
            inner_check = [isinstance_with_any(item, inner) for item in iterable]

        return all(inner_check)
    elif outer==Union:
        print('check union')
        for typ in inner:
            if isinstance(typ, types.GenericAlias):
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


# arg_type = eval("list[str]")
# arg_type = eval("list[dict[str, str]]")
# arg_type = eval("dict[str, dict]")
# arg_type = eval("list[dict[str, str]]")

arg_type = eval("Secrets")
test = {
    "test": {
        "test": "fin"
    }
}
# test = (test, test)
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

