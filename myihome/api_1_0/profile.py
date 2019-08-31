#!/usr/bin/env python
# -*-encoding:UTF-8-*-
from myihome import db, constants
from myihome.models import User
from myihome.utils.image_storage import storage
from myihome.utils.response_code import RET
from . import api
from myihome.utils.commons import login_required  # 引入装饰器,因为需要登录才能访问
from flask import g, current_app, jsonify, request, session


@api.route("/users/avatar", methods=["POST"])
@login_required  # 应该放到地下成为一个整体
def set_user_avatar():
    """
    设置用户头像
    参数:图片(多媒体表单格式)  用户id(g.user.id)
    :return:
    """
    user_id = g.user_id

    # 获取图片
    images_file = request.files.get("avatar")

    if images_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

    image_data = images_file.read()

    # 调用七牛的上传图片的方法, 涉及到网络操作所以需要不会异常,同时七牛那边也有可能上传失败,所以需要捕获异常信息
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

    # 保存文件名到数据库中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    avatar_url = constants.QINIU_DOMIN_PREFIX + file_name
    # 保存成功返回
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})


@api.route("/users/", methods=["GET"])
@login_required  # 应该放到地下成为一个整体
def get_profile_info():
    """
    页面一加载显示用户信息,my.html和profile.html页面显示的数据这里加载
    :return:
    """
    user_id = g.user_id

    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")
    else:
        if user is not None:
            user_id = user.id
            name = user.name
            phone_num = user.phone_num
            avatar_url = constants.QINIU_DOMIN_PREFIX + user.avatar_url
            return jsonify(errno=RET.OK, errmsg="true",
                           user={"user_id": user_id, "name": name, "avatar_url": avatar_url, "phone_num": phone_num})
        else:
            return jsonify(errno=RET.NODATA, errmsg="用户信息不存在")


@api.route('/users', methods=['PUT'])
@login_required
def update_user_name():
    """修改用户信息视图函数
    登录验证
    获取参数
    查询用户,更新用户名
    修改session中的name
    profile.html页修改用户名信息
    :return: 相应结果
    """
    user_id = g.user_id
    req_dict = request.get_json()
    name = req_dict.get("name")

    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg='用户名不能为空')

    try:
        User.query.filter_by(id=user_id).update({"name": name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存用户名失败")
    else:
        session['name'] = name
        return jsonify(errno=RET.OK, errmsg="更新用户名成功")


@api.route('/users/auth', methods=['GET'])
@login_required
def user_auth():
    """用户实名认证
    登录验证
    查询用户,获取用户信息
    auth.html页获取用户信息
    :return: 相应结果
    """
    user_id = g.user_id

    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")
    else:
        if user is not None:
            real_name = user.real_name
            id_card = user.id_card
            return jsonify(errno=RET.OK, errmsg="true",
                           user_auth={"real_name": real_name, "id_card": id_card})
        else:
            return jsonify(errno=RET.NODATA, errmsg="用户信息不存在")


@api.route('/users/auth', methods=['POST'])
@login_required
def user_realname_auth():
    """用户实名验证
    登录验证
    获取参数
    查询用户,更新用户真实姓名和身份ID
    保存到session
    auth.html页用户实名认证信息
    :return: 相应结果
    """
    user_id = g.user_id
    req_dict = request.get_json()
    real_name = req_dict.get("real_name")
    id_card = req_dict.get("id_card")

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    try:
        User.query.filter_by(id=user_id).update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据异常用户实名认证失败")
    else:
        session['real_name'] = real_name
        session['id_card'] = id_card
        return jsonify(errno=RET.OK, errmsg="用户实名认证成功")
