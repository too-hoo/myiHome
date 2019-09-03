#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from flask import Blueprint

# 创建蓝图对象:api_1_0是名字,可以反向调用api
api = Blueprint("api_1_0", __name__)

# 导入蓝图的视图,一定要记得注册, 初始化之后才知道有,否则别人不知道,请求的参数是405!405!
from . import demo, verify_code, passport, profile, houses, orders, pay
