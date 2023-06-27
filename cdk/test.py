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

from typing import get_args

# test = ['a', 'b', 'c']
test = {
    "test": {
        "test2": {
            "test3" : "final"
        }
    }
}

def outer_inner_types(arg):

    outer = arg.__name__
    outer = eval(outer)
    inner_args = get_args(arg)
    if len(inner_args) == 1:
        inner = inner_args[0]
    elif len(inner_args)>1:
        inner = inner_args

    return outer, inner

def check_inner_types(iterable, outer, inner):
    print(iterable)
    if type(iterable)==outer:
        if len(inner)==2:
            nested_inner_args = get_args(inner[1])
            if not nested_inner_args:
                print('no nest')
                inner_check = [isinstance(key, inner[0]) and isinstance(val, inner[1]) for key, val in iterable.items()]
                print(inner_check)
            elif (isinstance(key, inner[0]) for key, val in iterable.items()): # if key type matches
                print('check nested')
                nest_out, nest_in = outer_inner_types(inner[1])
                print(nest_out, nest_in)
                inner_check = [check_inner_types(val, nest_out, nest_in) for val in iterable.values()]
                print(inner_check)
            else:
                return False
        else:
            inner_check = [isinstance(item, inner) for item in iterable]

        return all(inner_check)    
    else:
        return False 

# arg_type = eval("list[str]")
# arg_type = eval("dict[str, dict]")
# outer_type, inner_type = outer_inner_types(arg_type)
# print(outer_type, inner_type)
# print(check_inner_types(test, outer_type, inner_type))

from typing import Literal

def accepts_only_four(x: Literal[4]):
    print(x)

# accepts_only_four(10)

# ttype = "Literal[4, 5, 6]"
# atype = eval(ttype)
# test = 4
# outer_type, inner_type = outer_inner_types(atype)
# if outer_type == Literal:
#     print(test in inner_type)

