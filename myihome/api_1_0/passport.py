#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
# request 获取参数, session全局的对象保存session
from flask import request, jsonify, current_app, session
from sqlalchemy.exc import IntegrityError  # sqlalchemy.exc封装了异常信息,如果数据库中出现重复键的问题就会抛出异常IntegrityError

from . import api
from myihome.utils.response_code import RET

from myihome import redis_store, db
from myihome.models import User


# 路径构造,使用post的请求方式
@api.route("/users", methods=["POST"])
def register():
    """注册
    请求的参数：手机号，短信验证码，密码(不用校验两次验证码)
    参数格式：json(约定前端传递的数据格式)
    """
    # 获取请求的json格式的数据,返回字典格式数据
    req_dict = request.get_json()

    phone_num = req_dict.get('phone_num')
    sms_code = req_dict.get('sms_code')
    password = req_dict.get('password')
    password2 = req_dict.get('password2')

    # 检验参数的完整性
    if not all([phone_num, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='请求参数不完整')

    # 判断手机号格式,引入正则表达式进行验证,参数错误,手机号错误
    if not re.match(r"1[34578]\d{9}", phone_num):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式不正确')

    # 判断两次密码是否一致,参数错误PARAMERR
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg='两次密码不一致')

    # 业务逻辑处理
    # 验证短信验证码是否正确
    # 从redis中取出手机号对应的短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % phone_num)
    except Exception as e:
        # 记录错误信息到日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='读取真实短信验证码异常')

    # 判断是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码失效')

    # 删除redis中的短信验证码,防止重复使用校验
    try:
        redis_store.delete("sms_code_%s" % phone_num)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写短信验证码的正确性
    # 将用户输入的短信验证码与redis中的短信验证码进行比较,decode('utf-8')处理的是将b''类型解码为字符串
    # 但是如果在redis数据库连接的时候,指定decode_responses=True就可以忽略
    if sms_code != real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码填写错误')

    # 简化操作,两次操作数据库简化为一次
    # 判断手机号是否注册过，将注册信息保存到数据库中,名字默认先设置为phone_num,后面提供接口再进行更改
    user = User(name=phone_num, phone_num=phone_num)

    # 对于密码加盐加密,使用sha256
    # 保存的形式,$分割:password = "123456" + "abc"  sha256   abc$afhslhglsahfsaf22453
    # password: pbkdf2:sha256(加密算法):150000$BirDkKkC(盐值)$055619ca5212e8134fb2ee9bdd82297223df5501e6a34d987da7210a0991e71a(加密字符串)
    user.password_hash = password  # 密码加密,在保存到数据库之前需要对密码进行加密
    # from sqlalchemy.exc import IntegrityError
    try:
        # 数据库操作可能会出现异常
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # IntegrityError 重复键异常,这是一个具体的手机号重复异常
        # 数据库操作错误后回滚,一定需要回滚rollback和commit是配合起来使用的
        db.session.rollback()
        # 表示手机号出现了重复，即手机号被注册过了
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')

    # 将登陆状态保存到session中
    session['name'] = phone_num
    session['phone_num'] = phone_num
    session['user_id'] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg='注册成功')
