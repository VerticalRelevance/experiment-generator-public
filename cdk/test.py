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


test = ['a', 'b', 'c']
# ttype="list[str]"
# exec(f"""def a(x: {ttype}):
#     return x""")
# print(a(test))
# print(inner_type_match(a))

from typing import get_args

def outer_inner_types(arg):

    outer = arg.__name__
    outer = eval(outer)
    inner_args = get_args(arg)
    inner = inner_args[0]

    return outer, inner

def check_inner_type(iterable, outer, inner):

    inner_check = [isinstance(item, inner) for item in iterable]
    if all(inner_check):
        if type(iterable)==outer:
            return True
    else:
        return False 

arg_type = eval("list[str]")
outer_type, inner_type = outer_inner_types(arg_type)
print(check_inner_type(test, outer_type, inner_type))


