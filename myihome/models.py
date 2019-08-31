#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from datetime import datetime
from . import db
from . import constants
# 导入对密码加密的hash函数和检查密码的hash函数
from werkzeug.security import generate_password_hash, check_password_hash


class BaseModel(object):
    """模型基类,下面的表会继承"""
    # 冗余字段是为了后面的数据分析方便
    # default设置默认值, onupdate将在记录更新的时候同步更新为当前时间
    create_time = db.Column(db.DateTime, default=datetime.now())  # 记录模型类创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now())  # 记录模型类更新时间


class User(BaseModel, db.Model):
    """用户模型类"""
    __tablename__ = 'ih_user_profile'

    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    name = db.Column(db.String(32), unique=True, nullable=False)  # 用户昵称
    password = db.Column(db.String(128), nullable=False)  # 加密的密码
    phone_num = db.Column(db.String(11), unique=True, nullable=False)  # 手机号
    real_name = db.Column(db.String(32))  # 真实姓名
    id_card = db.Column(db.String(20))  # 身份证号
    avatar_url = db.Column(db.String(128))  # 用户头像路径
    # 设置外键关联,房子和订单,backref反向映射
    houses = db.relationship('House', backref='user', lazy='dynamic')  # 用户发布的房屋, 使用懒加载模式为动态加载
    orders = db.relationship('Order', backref='user', lazy='dynamic')  # 用户下的订单

    # @property是将函数password_hash变成一个属性来存在的了,属性名字就是函数的名字
    @property
    def password_hash(self):
        """获取password属性的时候被调用"""
        # print(user.password)  # 读取属性的时候会被调用
        # 函数的返回值会作为属性值
        # 没有返回值,读取这个属性没有任何意义(因为该属性已经加密)
        # 通过抛出异常提示
        raise AttributeError(u'这个属性只能设置,不能读取访问该属性')

    # 对属性进行设置操作,通过构建出来的属性名.setter装饰器,添加一个设置行为
    # 使用这个装饰器,对应设置属性操作
    @password_hash.setter
    def password_hash(self, value):
        """
        对密码进行加密, 设置password属性时被调用, 设置密码加密
        设置属性 user.passord = "xxxxxx"
        :param value: 设置属性时的数据 value就是原始传入的xxxxxx明文密码
        :return:
        """
        self.password = generate_password_hash(value)

    # 可以通过User对象直接调用
    def check_password(self, password):
        """
         校验密码是否正确
        :param password: 用户登录输入的原始密码
        :return: 如果正确,返回true, 否则返回False
        """
        return check_password_hash(self.password, password)

    def to_dict(self):
        # 返回一个用户信息字典接口，使外界方便调用(将对象转换成为字典类型)
        user_info = {
            'user_id': self.id,
            'name': self.name,
            'phone_num': self.phone_num,
            'avatar_url': self.avatar_url,
            'create_time': self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        # 更新用户的头像信息:如果self.avatar_url 头像存在就在前面加上七牛的路径,否则为空
        if self.avatar_url:
            user_info['avatar_url'] = constants.QINIU_DOMIN_PREFIX + self.avatar_url if self.avatar_url else ""
        return user_info

    def to_auth_dict(self):
        """实名认证信息转换成为字典数据数据"""
        return {
            'real_name': self.real_name,
            'id_card': self.id_card
        }


class Area(BaseModel, db.Model):
    """城区"""
    __tablename__ = 'ih_area_info'

    id = db.Column(db.Integer, primary_key=True)  # 区域编号
    name = db.Column(db.String(32), nullable=False)  # 区域名字
    houses = db.relationship('House', backref='area')  # 区域的房屋

    def to_dict(self):
        """将对象转换为字典数据"""
        return {
            'aid': self.id,
            'aname': self.name
        }


# 房屋设施中间表，建立房屋与设施的多对多关系(多对多关系的处理)
# 这个是中间表,但是没有必要设置成为一个类,使用普通底层的方式建立一个表即可,下面在House中使用secondary关键字进行关联起来
# 将house_id和facility_id联合设置为主键,将这两个字段的编号当做唯一区分
house_facility = db.Table(
    "ih_house_facility",  # 表名
    db.Column('house_id', db.Integer, db.ForeignKey('ih_house_info.id'), primary_key=True),  # 房屋编号
    db.Column('facility_id', db.Integer, db.ForeignKey('ih_facility_info.id'), primary_key=True)  # 设施编号
)

class Facility(BaseModel, db.Model):
    """房屋设施信息模型类"""
    __tablename__ = 'ih_facility_info'

    id = db.Column(db.Integer, primary_key=True)  # 设施编号
    name = db.Column(db.String(32), nullable=False)  # 设施名字

class House(BaseModel, db.Model):
    """房屋模型类"""

    __tablename__ = 'ih_house_info'

    id = db.Column(db.Integer, primary_key=True)  # 房屋编号
    user_id = db.Column(db.Integer, db.ForeignKey('ih_user_profile.id'), nullable=False)  # 房屋主人编号
    area_id = db.Column(db.Integer, db.ForeignKey('ih_area_info.id'), nullable=False)  # 房屋地区编号
    title = db.Column(db.String(64), nullable=False)  # 标题
    price = db.Column(db.Integer, default=0)  # 单价 单位：分
    address = db.Column(db.String(512), default='')  # 地址
    room_count = db.Column(db.Integer, default=1)  # 房间数目
    acreage = db.Column(db.Integer, default=0)  # 房间面积
    unit = db.Column(db.String(32), default='')  # 房屋单元,几室几厅
    capacity = db.Column(db.Integer, default=1)  # 房屋能住多少人
    beds = db.Column(db.String(64), default="")  # 房屋床铺的配置
    deposit = db.Column(db.Integer, default=0)  # 房屋押金
    min_days = db.Column(db.Integer, default=1)  # 最少入住天数, 1表示限制
    max_days = db.Column(db.Integer, default=0)  # 最多入住天数，0表示不限制
    order_count = db.Column(db.Integer, default=0)  # 预订完成的该房屋的订单数
    index_image_url = db.Column(db.String(256), default="")  # 房屋主图片的路径

    # 多对多关系的特殊处理
    # 通过房子这个类查询出来里面的基础设施,secondary=house_facility的作用就是将
    # House类和Facility关联起来,在中间表中建立映射关系,进而可以将信息查询出来,省去查询中间表的操作
    facilities = db.relationship("Facility", secondary=house_facility)  # 房屋的设施

    images = db.relationship("HouseImage")  # 房屋的图片
    orders = db.relationship("Order", backref="house")  # 房屋的订单

    def to_basic_dict(self):
        """房屋基本信息字典"""
        return {
            "house_id": self.id,
            "title": self.title,
            "price": self.price,
            "area_name": self.area.name,
            "img_url": constants.QINIU_DOMIN_PREFIX + self.index_image_url if self.index_image_url else "",
            "room_count": self.room_count,
            "order_count": self.order_count,
            "address": self.address,
            "user_avatar": constants.QINIU_DOMIN_PREFIX + self.user.avatar_url if self.user.avatar_url else "",
            "ctime": self.create_time.strftime("%Y-%m-%d")
        }

    def to_full_dict(self):
        """房屋详细信息字典"""
        house_dict = {
            "hid": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name,
            "user_avatar": constants.QINIU_DOMIN_PREFIX + self.user.avatar_url if self.user.avatar_url else "",
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "room_count": self.room_count,
            "acreage": self.acreage,
            "unit": self.unit,
            "capacity": self.capacity,
            "beds": self.beds,
            "deposit": self.deposit,
            "min_days": self.min_days,
            "max_days": self.max_days,
        }
        # 房屋图片,存放多张图片返回前端显示
        img_urls = []
        for image in self.images:
            img_urls.append(constants.QINIU_DOMIN_PREFIX + image.url)
        house_dict["img_urls"] = img_urls

        # 房屋设施,存放多个设施返回前端显示
        facilities = []
        for facility in self.facilities:
            facilities.append(facility.id)
        house_dict["facilities"] = facilities

        # 评论信息
        comments = []
        orders = Order.query.filter(Order.house_id == self.id, Order.status == "COMPLETE", Order.comment != None) \
            .order_by(Order.update_time.desc()).limit(constants.HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS)
        for order in orders:
            comment = {
                "comment": order.comment,  # 评论的内容
                "user_name": order.user.name if order.user.name != order.user.mobile else "匿名用户",  # 发表评论的用户
                "ctime": order.update_time.strftime("%Y-%m-%d %H:%M:%S")  # 评价的时间
            }
            comments.append(comment)
        house_dict["comments"] = comments
        return house_dict


class HouseImage(BaseModel, db.Model):
    """房屋图片模型类"""
    __tablename__ = 'ih_house_image'

    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey('ih_house_info.id'), nullable=False) # 房屋编号
    url = db.Column(db.String(256), nullable=False)  # 图片路径


class Order(BaseModel, db.Model):
    """订单"""

    __tablename__ = "ih_order_info"

    id = db.Column(db.Integer, primary_key=True)  # 订单编号
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user_profile.id"), nullable=False)  # 下订单的用户编号
    house_id = db.Column(db.Integer, db.ForeignKey("ih_house_info.id"), nullable=False)  # 预订的房间编号
    begin_date = db.Column(db.DateTime, nullable=False)  # 预订的起始时间
    end_date = db.Column(db.DateTime, nullable=False)  # 预订的结束时间
    days = db.Column(db.Integer, nullable=False)  # 预订的总天数
    house_price = db.Column(db.Integer, nullable=False)  # 房屋的单价
    amount = db.Column(db.Integer, nullable=False)  # 订单的总金额
    status = db.Column(  # 订单的状态
        db.Enum(
            "WAIT_ACCEPT",  # 待接单,
            "WAIT_PAYMENT",  # 待支付
            "PAID",  # 已支付
            "WAIT_COMMENT",  # 待评价
            "COMPLETE",  # 已完成
            "CANCELED",  # 已取消
            "REJECTED"  # 已拒单
        ),
        default="WAIT_ACCEPT", index=True)
    comment = db.Column(db.Text)  # 订单的评论信息或者拒单原因
    trade_no = db.Column(db.String(128)) # 支付交易的编号

    def to_dict(self):
        """将订单信息转换成为字典数据"""
        return {
            "order_id": self.id,
            "title": self.house.title,
            "img_url": constants.QINIU_DOMIN_PREFIX + self.house.index_image_url if self.house.index_image_url else "",
            "start_date": self.begin_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "ctime": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "days": self.days,
            "amount": self.amount,
            "status": self.status,
            "comment": self.comment if self.comment else ""
        }
