#!/usr/bin/env python
# -*-encoding:UTF-8-*-


# import functools
#
# def login_required(func):
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         pass
#
#     return wrapper
#
#
# @login_required
# def test():
#     """test python"""
#     pass
#
#
# # test -> wrapper
#
# print(test.__name__)  # wrapper.__name__
# print(test.__doc__)  # wrapper.__doc__

import functools

def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pass

    return wrapper

@login_required
def test():
    """test python"""
    pass


# test -> wrapper

print(test.__name__)  # wrapper.__name__
print(test.__doc__)  # wrapper.__doc__
