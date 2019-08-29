#!/usr/bin/env python
# -*- coding:utf-8 -*-
# 静态文件加载的显示文件

from flask import Blueprint, current_app, make_response
from flask_wtf import csrf  # 引入CSRF防御

# 提供静态文件的蓝图
html = Blueprint("web_html", __name__)


# 127.0.0.1:5000/()
# 127.0.0.1:5000/(index.html)
# 127.0.0.1:5000/(register.html)
# 127.0.0.1:5000/(favico.ico) # 浏览器会自己请求这个资源,它是网站的标志


# 可能什么都提取不到也有可能提取到一个文件名.*代表最少是0个,html_file_name对应的是我们提取的文件名字
@html.route("/<re(r'.*'):html_file_name>")
def get_html(html_file_name):
    """提供html文件"""
    # 可以直接到静态文件哪里找到返回,也可以使用flask提供的一个方法current_app.send_static_file,专门让我们返回静态文件的
    # 如果html_file_name为空，表示访问的路径为/ , 请求的是主页,直接等于index.html即可
    if not html_file_name:
        html_file_name = 'index.html'

    # 如果html_file_name不是favicon.ico
    if html_file_name != 'favicon.ico':
        html_file_name = 'html/' + html_file_name # 直接拼接html/

    # 创建一个csrf_token的值
    csrf_token = csrf.generate_csrf()

    # flask 提供的返回静态文件的方法,默认是到static目录下面去找
    # flask 提供的返回静态文件的方法, 在返回之前先使用make_response接受一下响应体设置cookie之后再返回
    resp = make_response(current_app.send_static_file(html_file_name))

    # 设置cookie值包含CSRF的token值
    resp.set_cookie('csrf_token', csrf_token)
    return resp
