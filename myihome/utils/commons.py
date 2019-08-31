#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 导入基础的正则转换器
from werkzeug.routing import BaseConverter
# 使用中间人g对象作为装饰器和被装饰函数中的参数传递者
from flask import session, jsonify, g
from myihome.utils.response_code import RET
import functools  # python的内置模块,存放函数工具

# 自定义正则转换器
class ReConverter(BaseConverter):
    """自定义静态文件路由转换器"""

    def __init__(self, url_map, regex):
        # 调用父类的初始化方法
        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


# xrange, 解决python3没有xrange的问题
def xrange(start, end=None, step=1):
    if end == None:
        end = start
        start = 0
    if step > 0:
        while start < end:
            yield start
            start += step
    elif step < 0:
        while start > end:
            yield start
            start += step
    else:
        return 'step can not be zero'


# 定义验证登录状态的装饰器
# 闭包:外层一般就是定义为被装饰的函数(view_func(例如这里是:set_user_avatar))"@外层函数"
def login_required(view_func):
    # 内层函数一般定义为wrapper,并且由于参数不确定,使用*args, **kwargs待定
    # 这个函数装饰器专门是用来装饰内层函数的,
    # 1参数:外层函数接受的参数,直接传给里面的就可以了,
    # 2意义:内层装饰器加上之后会改变一些特性:functools的wraps会将wrapper相关的属性和名字恢复为view_func的属性和名字,参考文档的工程目录下的   demo.py
    @functools.wraps(view_func)  # 在写装饰器的时候需要将这个内层装饰器补上
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态
        user_id = session.get("user_id")

        # 如果用户是登录的,执行视图函数
        if user_id is not None:
            # g对象的应用,保存user_id,让其作为参数传递对象,在视图函数中可以通过g对象获取保存数据
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            # 如果未登录,返回未登录的信息
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    return wrapper


# 使用中间人g对象作为装饰器和被装饰函数中的参数传递者,g对象就是提供来保存数据的
# 在一次请求之中如果涉及到多个函数请求参数的时候就可以使用g对象来传参数
@login_required
def set_user_avatar():
    # user_id = session.get("user_id")
    user_id = g.user_id
    pass

# set_user_avatar() 的执行就是执行wrapper-> wrapper() 直接传递参数到wrapper()里面

