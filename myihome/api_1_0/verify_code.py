#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
from flask import current_app, jsonify, make_response, request
from . import api
from myihome.utils.captcha.captcha import captcha # 导入captcha工具
# 导入redis数据库和常量
from myihome import redis_store, constants, db
# 导入事先约定好的响应码
from myihome.utils.response_code import RET
from myihome.models import User
from myihome.libs.yuntongxun.sms import CCP


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
    # Redis Setex命令为指定的key设置值及其过期时间。如果key已经存在， SETEX命令将会替换旧的值。SETEX KEY_NAME TIMEOUT VALUE
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



# GET 127.0.0.1:5000/sms_codes/<phone_num>?image_code=xxx&image_code_id=xxx

# 手机号在提取的时候就进行了校验1[34578]都是可以的
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):phone_num>")
def get_sms_code(phone_num):
    """
    获取短信验证码
    1.获取参数
    2.校验参数
    3.业务处理
    4.从redis中取出真实的图片验证码
    5.与用户填写的信息进行对比
    6.判断手机号是否存在
    7.如果手机号不存在,则生成短信验证码
    8.保存真实的短信验证码
    9.发送短信
    10.返回值
    :param mobile:
    :return:
    """
    # 获取参数, args是一个字典
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')

    # 检验参数all()校验参数是否完整
    if not all([image_code, image_code_id]):
        # 表示参数不完整,返回json
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 逻辑处理
    # 从redis中取出验证码图片的真实值, 进行网络操作可能会出现错误,需要捕获一下
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        #
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    # 可能过期,判断真实值是否过期,redis中如果过期则返回None
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg='验证码失效')

    # 删除redis中的图片验证码,防止用户使用同一个验证码验证多次
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        # 这里删除验证码不成功也不会造成崩溃,不用直接返回给用用户,返回是没有道理的,让用户验证就可以
        current_app.logger.error(e)

    # 验证用户填写的验证码与redis中的真实值是否相等,统一为小写,python3中会出现b''这种情况,需要在初始化链接redis的时候设置参数decode_responses=True
    # print(image_code)   # 3Mj9
    # print(real_image_code) # b'3Mj9'
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')

    # 判断对于这个手机号的操作,在60秒内有没有之前的记录,如果有,则认为用户操作频繁,不接受处理
    try:
        send_flag = redis_store.get("send_sms_code_%s" % phone_num)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示在60秒之前有过发送的记录
            return jsonify(errno=RET.REQERR,errmsg="请求过于频繁,请于60秒之后重试")

    # 判断手机号是否已注册
    # 对数据库的操作需要把异常捕获补上:这里的异常捕获和else逻辑集合使用
    try:
        # 有且只有一条,否则是没有,所以使用first()函数过滤
        user = User.query.filter_by(phone_num=phone_num).first()
    except Exception as e:
        # 如果数据库出现问题只把错误信息保存下来(因为不想失去用户),否则会走下面的else逻辑
        current_app.logger.error(e)
    else:
        # user对象能够存在的前提是没有发生异常,如果发生异常user可能就没有,所以这里应该使用else进行判断
        # 在Django中获取单条记录不存在时会抛出异常,凡是在Flask中会返回None值
        if user is not None:
            # 表示手机号已经存在
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')

    # 生成短信验证码 6 位, "%06d"的意思就是保证有6位数,不够前面补0
    # import random
    sms_code = "%06d" % random.randint(0, 999999)  # %06d  表示生成6位整数，不够的前边补0 ，如029541

    # 保存短信验证码到redis中
    try:
        # 由于有效期,所以单条存储数据,使用字符串类型
        redis_store.setex("sms_code_%s" % phone_num, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给这个手机号的记录,防止用户在60s内再次发出短信验证码操作, 1这个键说明的是存在(仅仅作为一个记录)
        redis_store.setex("send_sms_code_%s" % phone_num, constants.SEND_SMS_CODE_INTERVAL, 1)

    except Exception as e:
        current_app.logger.error(e)
        # 保存错误的时候直接就返回了,因为下面的逻辑都无法保证了
        return jsonify(errno=RET.DBERR, errmsg='短信验证码保存异常')

    # 发送短信验证码
    # 第三方的错误出现错误不能保证,所以也需要进行捕获
    try:
        # from ihome.libs.yuntongxun.sms import CCP
        ccp = CCP()
        # (电话号码,[验证码,有效时间])
        result = ccp.sendTemplateSMS(phone_num, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='验证码发送异常')

    if result == 0:
        # 发送成功
        return jsonify(errno=RET.OK, errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送失败')

