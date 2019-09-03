#!/usr/bin/env python
# -*-encoding:UTF-8-*-
import os

from alipay import AliPay
from flask import g, current_app, jsonify, request

from myihome import constants, db
from myihome.models import Order
from myihome.utils.response_code import RET
from . import api
from myihome.utils.commons import login_required


# POST 127.0.0.1:5000/api/v1.0/orders/<int:order_id>/payment
@api.route("/orders/<int:order_id>/payment", methods=['POST'])
@login_required
def order_pay(order_id):
    """start alipay"""

    # get user id
    user_id = g.user_id

    # judge the order status
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.errer(e)
        return jsonify(errno=RET.DBERR, errmsg='DB ERROR')

    if order is None:
        return jsonify(errno=RET.NODATA, errmsg='ORDER DATA ERROR')

    app_private_key_string = open(os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read()

    # create alipay sdk tools object
    alipay_client = AliPay(
        appid="2016101300679257",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    # 手机网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
    order_string = alipay_client.api_alipay_trade_wap_pay(
        out_trade_no=order.id,  # order_id
        total_amount=str(order.amount / 100.0),  # amount from DB and convert to string
        subject='爱家租房 %s' % order.id,  # special subject
        return_url="http://127.0.0.1:5000/payComplete.html",  # return url
        notify_url=None  # 可选, 不填则使用默认notify url
    )

    # create alipay address and so it to user
    pay_url = constants.ALIPAY_URL_PREFIX + order_string
    return jsonify(errno=RET.OK, errmsg="OK", data={"pay_url": pay_url})


# PUT 127.0.0.1:5000/api/v1.0/order/payment

@api.route("/order/payment", methods=['PUT'])
@login_required
def save_order_payment_result():
    """
    save the result of payment,and redirect to payComplete.html page. meanwhile returm the
    formType data from alipay, such as:

     /orders.html?charset=utf-8
     &out_trade_no=1
     &method=alipay.trade.wap.pay.return
     &total_amount=798.00
     &sign=aONlDGPkHCgvpF7JlzT......QW0PqhP2jMKA%3D%3D
     &trade_no=2019090322001403331000089566
     &auth_app_id=2016101300679257
     &version=1.0
     &app_id=2016101300679257
     &sign_type=RSA2
     &seller_id=2088102179436454
     &timestamp=2019-09-03+17%3A38%3A46

    当在payComplete.html点击“Go back to My Order”时, 向后端发起请求,将数据保存,订单的状态改为“待评价”
    """
    # get parameters and convert to dict
    alipay_dict = request.form.to_dict()

    # 对支付宝的数据进行分离  提取出支付宝的签名参数sign 和剩下的其他数据
    alipay_sign = alipay_dict.pop("sign") # pop(): get and pop(delete)

    app_private_key_string = open(os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read()

    # create alipay sdk tools object
    alipay_client = AliPay(
        appid="2016101300679257",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    # verify the correctness of parameters with the help of tools
    # 如果确定参数是支付宝的，返回True，否则返回false
    result = alipay_client.verify(alipay_dict, alipay_sign)

    if result:
        # change the order status in database
        order_id = alipay_dict.get("out_trade_no")
        trade_no = alipay_dict.get("trade_no") # 支付宝交易的流水号

        try:
            Order.query.filter_by(id=order_id).update({"status":"WAIT_COMMENT", "trade_no":trade_no})
            db.session.commit()
        except Exception as e:
            current_app.logger.errer(e)
            db.session.rollback()

    return jsonify(errno = RET.OK, errmsg='OK')






