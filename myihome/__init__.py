#!/usr/bin/env python
# -*-encoding:UTF-8-*-
# 这个是myihome目录的顶级文件,基础的配置都放在这里

import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, session
from config import config_map
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session  # 注意这是大写的,是一个类
from flask_wtf import CSRFProtect  # 虽然是前后端分离但是会使用到表单中的csrf防护
from myihome.utils.commons import ReConverter


import redis

# 数据库, 刚开始的时候只创建一个对象,还没有绑定app
db = SQLAlchemy()

# 创建redis连接对象,其他的模块会用到,所以在外面保留redis_store
redis_store = None

# error>warn>info>debug 级别依次降低
# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小(100M)、保存的日志文件个数上限(这里设置为10个,多了丢弃)
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
# 创建日志记录的格式     日志等级    输入日志信息的文件名  行数  日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

# 工厂模式
def create_app(config_name):
    """
    创建flask的应用对象
    :param config_name: str 配置模式的模式的名字("develop", "product")
    :return:
    """
    app = Flask(__name__)
    # 根据映射指定配置信息(开发模式,还是生产模式)
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 这里才将app与db绑定,使用app初始化db
    db.init_app(app)

    # 初始化redis工具, 根据生产或者开发环境,选择好之后,在使用global 将redis_store更新,外面就可以使用.
    global redis_store
    # 不用直接操作Config这个类,而是根据需要导入的config_class类中就可以获取到redis链接参数
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

    # 利用flask-session,将session数据保存到redis中(直接将app传递给类Session,里面会修改session机制,达到更改的目的)
    Session(app)

    # 为flask补充csrf防护,仅仅是一个防护机制.在Django中只要在中间件中发现post请求,都会过滤,
    # 但是在flask中没有中间件,但是有钩子@app.before_request防护
    CSRFProtect(app)

    # 为flask添加自定义的转换器,主要把这个转换器注册给全局的APP即可,蓝图最后被加载
    app.url_map.converters['re'] = ReConverter

    # 推迟导入,解决循环导包冲突问题, 用到了才导入
    from myihome import api_1_0  # 使用绝对目录的方式导入蓝图
    # 注册蓝图
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")

    # 注册提供静态文件的蓝图
    from myihome import web_html
    app.register_blueprint(web_html.html)

    return app
