#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import current_app, jsonify, make_response

from . import api
from myihome.utils.captcha.captcha import captcha # 导入captcha工具
# 导入redis数据库和常量
from myihome import redis_store, constants
# 导入事先约定好的响应码
from myihome.utils.response_code import RET

# 前端访问的路径:/资源/前端生成的编号
# GET 127.0.0.1:5000/image_codes/<image_code_id>

@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):
    """
    获取验证码图片
    :param image_code_id: 图片验证码编号(需要接收)
    :return: 如果出现异常，返回异常信息，否则，返回验证码图片
    """
    # 套路:获取参数,检验参数,业务逻辑处理,返回值
    # 生成验证码图片
    # 名字，真实文本，图片数据
    name, text, image_code = captcha.generate_captcha()

    # 将编号以及验证码的真实值保存到redis（选择字符串）中，并设置有效期（自定义有效期为180秒，设置成了常量，在constants中）
    # redis:
    #   字符串:"key":xxx <--
    #   列表:(redis中的列表保存的还是字符串的值,和python有本质的区别)image_codes:["编号:","",""] -----麻烦
    #   哈希:"image_codes":{"id1":"abc","":""} 里面存放的还是字符串, 哈希使用的方法  hset("image_code","id1","abc"), 有就取,没有就存  --有效期不方便

    # 选用单条维护记录,选用字符串,直接使用set函数设置字符串即可
    # redis_store.set('iamge_code_%s' % image_code_id, text)
    # redis_store.expire('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES)
    # 将以上合并写,setex(记录名,有效期,记录值), 网络连接可能有问题,使用要捕获一下异常,默认保存在0号数据库
    try:
        redis_store.setex('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR, errmsg="save image code failed")
        # 出现异常,没有必要返回图片了，返回json格式的提示使用jsonify()函数
        return jsonify(errno=RET.DBERR, errmsg="保存图片验证码失败")

    # 没有异常 返回验证码图片，并指定一下头make_response:修改内容类型Content-Type(默认为test/html)类型为image,不改不认识图片
    resp = make_response(image_code)
    resp.headers['Content-Type'] = 'image/jpg'
    return resp
