#!/usr/bin/env python
# -*-encoding:UTF-8-*-

# api/houses.py
import json

from flask import current_app, jsonify, request, g, session

from myihome import redis_store, constants, db
from myihome.utils.commons import login_required
from . import api
from myihome.models import Area, House, Facility, HouseImage, User, Order
from myihome.utils.response_code import RET
from myihome.utils.image_storage import storage
from datetime import datetime  # remember to import datetime from datetime!

@api.route('/areas')
def get_area_info():
    """获取区域信息"""
    # try to get data from redis
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # cache data in redis
            current_app.logger.info("hit redis area_info")
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查新数据库
    try:
        # 查询出所有的数据到列表
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    area_dict_li = []
    # 将每一个城区信息对象转换为字典,然后拼接到列表中
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # 将数据转换为json字符串,使用函数dict()将字典类型的数据转换成为json type string
    # save to redis
    resp_dict = dict(errno=RET.OK, errmsg='OK', data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis中,整体存,整体取
    try:
        # (name, expires_time, key)
        # must set area_data expire_time for the issue of sync_problem between redis and mysql
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    # 将查询到的数据data和对应的信息返回
    return resp_json, 200, {"Content-Type": "application/json"}


# houses.py

@api.route('/houses/info', methods=['POST'])
@login_required  # must login
def save_house_info():
    """保存房屋的基本信息：发布
    前端发送过来的json数据
    {
        "title": "",
        "price": "",
        "area_id": "",
        "address": "",
        "room_count": "",
        "acreage": "",
        "unit": "",
        "capacity": "",
        "beds": "",
        "deposit": "",
        "min_days": "",
        "max_days": "",
        "facility": ["7", "8"]   # save pick_up to list and return
    }
    """
    # 获取数据
    user_id = g.user_id

    # accept the json_type data
    house_data = request.get_json()

    title = house_data.get('title')  # 标题
    price = house_data.get('price')  # 单价 of house
    area_id = house_data.get('area_id')  # 区域的编号
    address = house_data.get('address')  # 地址
    room_count = house_data.get('room_count')  # 房间数
    acreage = house_data.get('acreage')  # 面积
    unit = house_data.get('unit')  # 布局（几厅几室）
    capacity = house_data.get('capacity')  # 可容纳人数
    beds = house_data.get('beds')  # 卧床数目
    deposit = house_data.get('deposit')  # 押金
    min_days = house_data.get('min_days')  # 最小入住天数
    max_days = house_data.get('max_days')  # 最大入住天数

    # 校验必填参数，facility非必填
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 对单价和押金作出判断，是否是数字，判断方法：可否转换成数字
    # change price to integer:price->float->int
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 判断城区是否存在，防止发布的城区在数据库中没有，进行过滤操作
    # judge the existence of area id, for security ,you must verify the args from the frontend
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据异常')

    # 如果城区在数据库中不存在
    if area is None:
        return jsonify(errno=RET.NODATA, errmsg='城区信息有误')

    # 其他验证，略

    # 保存数据, create a object to save the basic data, other data will be processe below
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        room_count=room_count,
        address=address,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 处理房屋设施信息
    facility_ids = house_data.get('facility')

    # 如果用户勾选了设施信息，再保存到数据库
    if facility_ids:
        # ["7", "8", ..]
        # 过滤出设施数据在数据库中存在的数据
        try:
            # must add filter before insert into DB for security.  all(): for all data, first(): single data
            # will return a list:facilities
            # "filter_by" only support the single opt:"=" operation, so, change it to "filter"
            # "Facility.id.in_()" function is provided by SQLAlchemy to solve the clause(SQL子句):"in" operation
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库异常')

        if facilities:
            # 表示有合法的设施数据,listType
            # 保存数据库, dynamic add facilities to house object
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()  # commit all data at once
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据错误')

    # 保存数据成功, return house_id to continue finish the form submit
    return jsonify(errno=RET.OK, errmsg='保存数据成功', data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """ save the image of house
    args: pic house_id
    :return:
    """
    image_file = request.files.get("house_image")  # get data from form_data directly
    house_id = request.form.get("house_id")

    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="args error")

    # judge the Correctness of house_id
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="DB error")

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="House not exist")

    # read the image and change to binary
    image_data = image_file.read()

    # save the image to qiniu cloud storage, and it return the pic_name
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="save the picture failed")

    # save the picture to DB
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    # solution of the house main picture, setting the index_image_url,
    # so the first image would be the default house image
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="save picture data error")

    # return the url to show the image in frontend
    image_url = constants.QINIU_DOMIN_PREFIX + file_name

    return jsonify(errno=RET.OK, errmsg="OK", data={"image_url": image_url})


# GET 127.0.0.1:5000/user/houses

@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    """get the entry of the landlord's house information"""
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses  # obtain the house info from Foreign key
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="get data failed")

    # Converting the house information queried into a dictionary and storing it in the list
    houses_list = []
    if houses:
        for houses in houses:
            houses_list.append(houses.to_basic_dict())
    # return the corresponding info and house data
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """get the house info displayed on the slides on the home page"""
    # try to get the cache data from redis
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        # recover the return data to None
        # 如果出现异常，继续往下走回抛出异常：ret还没有被定义过, so define  "ret = None"
        ret = None

    if ret:
        current_app.logger.info("hit house index info redis")
        # cause the storage_Type in redis is json_string, so return 执行字符串拼接 directly,
        return '{"errno":0, "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type": "application/json"}
    else:
        try:
            # do not need to show all the house data
            # query DB, and return the data of house'order count more then 5 record
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="query DB failed")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="query return NODATA")

        houses_list = []
        for house in houses:
            # if house has not set default image, jump
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # convert the data to json_str, and save to redis cache
        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)
        # return json_str 字符串拼接 , because it's more quickly then jsonify() function
        return '{"errno":0, "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/detail/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """get house detail"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则显示预定按钮，否则不显示，
    # 所以需要在后端返回登录用户的user_id
    # 尝试获取用户的登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id = -1
    login_user_id = session.get("user_id", "-1")

    # verify args
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="args error")

    # get data from redis first
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"login_user_id":%s, "house":%s}}' % (login_user_id, ret), \
               200, {"Content-Type": "application/json"}

    # query DB
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="query DB failed")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="house not exist")

    # convert house obj to dict
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="data error 1")

    # save data to redis
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"login_user_id":%s, "house":%s}}' % (login_user_id, json_house), \
               200, {"Content-Type": "application/json"}
    return resp


# GET /api/v1.0/houses?sd=20190902&ed=20190930&aid=10&sk=new&p=1
@api.route("/houses/search")
def get_house_list():
    """get house list info(search page)"""
    start_date = request.args.get("sd", "")  # get the start time that user wants
    end_date = request.args.get("ed", "")  # get the end time that user wants
    area_id = request.args.get("aid", "") # area id
    sort_key = request.args.get("sk", "new") # sort key ,default "new"
    page = request.args.get("p")  # page num

    # process time
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d") # strptime():convert str to time; strftime():convert time to str;

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")  # strptime():convert str to time; strftime():convert time to str;

        # print("start_date", start_date)
        # print("end_date", end_date)
        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="datetime error")

    # judge area id
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            return jsonify(errno=RET.PARAMERR, errmsg="area args error")

    # process page, default page = 1
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # get cache data
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            print("hit_list_house_data")
            return resp_json, 200, {"Content-Type":"application/json"}

    # args_list container of filter_condition
    filter_params = []

    # fill in the filter_args
    # time condition
    conflict_orders = None

    try:
        if start_date and end_date:
            # query the conflict order
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="DB error")

    if conflict_orders:
        # get conflict house_id from order
        conflict_house_ids = [order.house_id for order in conflict_orders]

        # if conflict_house_ids is not None, append the condition to the query_args
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))

    # area cond:
    if area_id:
        filter_params.append(House.area_id == area_id)

    # Not query the DB actually, only return the condition of query the DB
    # add sort_key cond:
    # 注意：这里测查询参数是不固定的，所以使用*args的形式
    if sort_key == "booking": # through order_count
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc": # price inc
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-des": # price desc
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else: # default new and old
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # process paginate
    # Here, opt the DB in fact,so catch the exception
    try:
        #                   current_page        page_capacity                        auto err_output
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="DB error")


    # get page data
    house_li = page_obj.items
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    # get total page
    total_page = page_obj.pages

    resp_dict = dict(errno=RET.OK, errmsg="OK", data={"total_page":total_page, "houses":houses, "current_page":page})
    resp_json = json.dumps(resp_dict)

    # for the meaning of cache
    if page <= total_page:
        # setting cache data in redis
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
        # hashType
        try:
            # redis_store.hset(redis_key, page, resp_json)
            # redis_store.expire(redis_key, constants.HOUSE_LIST_REDIS_EXPIRES)

            # create redis pipeline object, it can execute Multiple statement at once
            pipeline = redis_store.pipeline()

            # start Multiple statement record
            pipeline.multi()

            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUSE_LIST_REDIS_EXPIRES)

            # execute statement
            pipeline.execute()

        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {"Content-Type":"application/json"}


# redis store cache
#
# "house_start_end_area_id_sk_page"
# (errno=RET.OK, errmsg="OK", data={"total_page":total_page, "houses":houses, "current_page":page})
#
# in redis all kinds of data are base on stringType
#
# "house_start_end_area_id_sk":hash
# {
#     "1":{},
#     "2":{},
# }















