#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
# request 获取参数, session全局的对象保存session
from flask import request, jsonify, current_app, session
from sqlalchemy.exc import IntegrityError  # sqlalchemy.exc封装了异常信息,如果数据库中出现重复键的问题就会抛出异常IntegrityError

from . import api
from myihome.utils.response_code import RET

from myihome import redis_store, db, constants
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


# 外边传入的json数据的时候一定都必须是双引号,单引号会出错
@api.route("/sessions", methods=["POST"])
def login():
    """用户登录
    参数: 手机号,密码
    :return:
    """
    # 获取参数
    req_dict = request.get_json()
    phone_num = req_dict.get("phone_num")
    password = req_dict.get("password")
    # 检验参数
    # 参数的完整的校验
    if not all([phone_num, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 手机号的格式
    if not re.match(r"1[34578]\d{9}", phone_num):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    # 判断错误次数是否超过限制,如果超过限制,则返回
    # redis记录: "access_nums_请求的ip": 次数
    user_ip = request.remote_addr  # 获取用户的IP地址
    try:
        access_nums = redis_store.get("access_num_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        # 等于5次的时候直接返回了
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg="非法请求次数过多,请稍后再试")

    # 从数据库中根据手机号查询用户数据的对象
    try:
        user = User.query.filter_by(phone_num=phone_num).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    # 用数据库的密码与用户填写的密码进行对比验证
    if user is None or not user.check_password(password):
        # 如果验证失败,记录错误次数,返回信息
        try:
            # 1 2 3 4 5 到第5次的时候才设置过期限制时间,第4次的时候设置为5了, 所以上面应该是>=号
            # 同时应该设置增加次数和过其时间,使用redis的内置函数incr和expire函数
            redis_store.incr("access_num_%s" % user_ip, amount=1)  # amount 指定每次增加的次数
            redis_store.expire("access_num_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)  # (键, 过期时间)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR, errmsg="用户名或者密码错误")
    # 如果验证相同成功,保存登录状态到session中
    session["name"] = user.name
    session["phone_num"] = user.phone_num
    session["user_id"] = user.id

    # 如果验证失败,记录错误的次数,返回信息
    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/sessions", methods=["GET"])
def check_login():
    """检查登录的状态"""
    # 尝试从session中获取用户的名字
    name = session.get("name")  # 使用get函数,不用操作字典的中括号的形式
    user_id = session.get("user_id")  # 使用get函数,不用操作字典的中括号的形式
    # 如果session中数据name名字存在, 则表示用户已经登录,否则未登录
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", user={"name": name,"user_id":user_id})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")

@api.route("/sessions", methods=["DELETE"])
def logout():
    """登出"""
    # 清楚session数据
    session.clear()
    return jsonify(errno=RET.OK, errmsg="OK")
