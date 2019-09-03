#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from datetime import datetime

from flask import g, request, jsonify, current_app

from myihome import db, redis_store
from myihome.models import House, Order
from myihome.utils.commons import login_required
from myihome.utils.response_code import RET
from . import api


# POST api/v1.0/orders

# @api.route("/orders", methods=["POST"])
# @login_required
# def save_order():

@api.route("/orders", methods=['POST'])
@login_required
def save_order():
    """ save order
    args: user_id, house_id, start_time and end_time date
    args_Type: json Type
    :return:
    """
    user_id = g.user_id

    # get args
    order_data = request.get_json()

    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="args error")

    house_id = order_data.get("house_id") # the house_id that has been booked
    start_date_str = order_data.get("start_date") # 预定入住时间 Reservation time
    end_date_str = order_data.get("end_date") # Scheduled end time

    # verify the correctness of args
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="args ERROR")

    # process date
    try:
        # convert accept date_str type to dateType
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        assert start_date <= end_date

        # count the days that booking
        days = (end_date - start_date).days + 1  # datetime.timedelta :.days, seconds, max, min
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="datetime format ERROR")

    # check the existence of house
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='get the house info failed')

    if not house:
        return jsonify(errno=RET.DBERR, errmsg="House Not Exist")

    # judge the customer whether it is the landlord himself
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg='can not book your own house')

    # ensure during the time that customer has booked, house do not been booked by anyone else
    try:
        # check conflict Number of orders,
        count = Order.query.filter(Order.house_id == house_id,
                                   Order.begin_date <= end_date,
                                   Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="DB ERROR, please try again later")

    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="house has been reserved")

    # reserve amount
    amount = days * house.price

    # save the order data
    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="save order failed")
    return jsonify(errno=RET.OK, errmsg='OK', data={"order_id":order.id})


# GET IP/api/v1.0/user/orders?role=customer  role = landlord

@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_orders():
    """
    query user order info
    :return:
    """
    # get user_id
    user_id = g.user_id

    # the role of the user:
    # as a customer: to query the order of others people's house
    # as a landlord: to query the order of customer that has reserved
    role = request.args.get("role","")

    # check the order info
    try:
        if "landlord" == role:
            # As a landlord to query the order, query the house that belongs to himself first
            houses = House.query.filter(House.user_id == user_id).all()
            houses_ids = [house.id for house in houses]
            # then query the house_order that others has reserved
            orders = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc()).all()
        else:
            orders = Order.query.filter(Order.user_id==user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Query order info failed")

    # convert order info data into dictType data
    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())
    return jsonify(errno=RET.OK, errmsg="OK", data={"orders": orders_dict_list})



# PUT 127.0.0.1:5000/api/v1.0/orders/orderId/status

@api.route("/orders/<int:order_id>/status", methods=['PUT'])
@login_required
def accept_reject_order(order_id):
    """
    accept, reject
    :param order_id: order id
    :return:
    """
    # get user id
    user_id = g.user_id

    # get parameters
    req_data = request.get_json()
    # print(req_data)
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg='PARAMETERS ERROR')

    # action parameter shows the landlord's action:accept or reject
    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="PARAMETERS ERROR")

    try:
        # query the order by order_id, and the condition of order status is Pending receipt(待接单)
        order = Order.query.filter(Order.id==order_id, Order.status=="WAIT_ACCEPT").first()
        # order->user->house
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Can not get order data")

    # ensure that the landlord can modify his own house order
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="Invalid Operation")

    if action == "accept":
        # accept order, change order status to "WAIT_PAYMENT"
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        # reject order, Record the reasons for rejection
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="PARAMETERS ERROR")
        order.status = "REJECTED"
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="Operation Failed")
    return jsonify(errno=RET.OK, errmsg='OK')

# PUT 127.0.0.1:5000/api/v1.0/orders/orderId/comment


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """ save comment info
    :param order_id: order id
    :return:
    """
    # get user id
    user_id = g.user_id

    # get parameters
    req_data = request.get_json()
    comment = req_data.get("comment")

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="PARAMETERS ERROR")

    # 根据订单编号,检验该订单是自己下的订单,并且处于待评论的状态, 否则不予许评论
    try:
        order = Order.query.filter(Order.id==order_id, Order.user_id==user_id, Order.status=='WAIT_COMMENT').first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='Can not obtain order data')

    if not order:
        return jsonify(errno=RET.REQERR, errmsg='Can not OPERATION')

    # save comment
    try:
        # change the order status to "finished"
        order.status = 'COMPLETE'
        # add comment
        order.comment = comment
        # change and add 1 to the attribute:order_count in the DB table:ih_house_info
        house.order_count += 1
        # commit
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="OPERATION ERROR")

    # Because the evaluation information of the order is included in the housing details, in order to display the
    # latest evaluation information in the housing details, delete the details cache in redis about this order house.
    # 因为房屋详情中有订单的评价信息，为了让最新的评价信息展示在房屋详情中，所以删除redis中关于本订单房屋的详情缓存

    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg='OK')




















