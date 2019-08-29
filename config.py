# coding: utf-8

from flask import Flask, session
import redis
import logging

app = Flask(__name__)


class Config(object):
    """应用程序配置类"""

    # logging等级
    LOGGIONG_LEVEL = logging.DEBUG

    # 配置secret key,可以任意指定,但是一般正规生成.简单生成方法，ipthon 中 base64.b64encode(os.urandom(48))
    SECRET_KEY = 'ix4En7l1Hau10aPq8kv8tuzcVl1s2Zo6eA+5+R+CXor8G3Jo0IJvcj001jz3XuXl'

    # orm连接数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:123@127.0.0.1:3306/myihome'
    # 是否开启追踪
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # 显示sql语句
    # SQLALCHEMY_ECHO=True

    # 配置Redis数据库
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_DB = 1

    # 用到的时候直接去搜flask-session的配置即可
    # 配置session数据存储到redis数据库
    SESSION_TYPE = 'redis'
    # 指定存储session数据的redis的位置
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    # 开启session数据的签名,意思是让session数据不是以明文的形式存储
    SESSION_USE_SIGNER = True
    # 设置session的会话的超时时长:一天,全局指定
    PERMANENT_SESSION_LIFETIME = 3600 * 24


class DevelopmentConfig(Config):
    """开发模式的配置信息"""
    # 开启调试模式
    DEBUG = True
    # 环境默认是production的,更改为development,直接终端运行命令: export FLASK_ENV=development
    pass



class ProducrionConfig(Config):
    """生产环境模式的配置信息"""
    pass


config_map = {
    "develop": DevelopmentConfig,
    "product": ProducrionConfig
}
