#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 图片验证码Redis有效期， 单位：秒
IMAGE_CODE_REDIS_EXPIRES = 300

# 短信验证码Redis有效期5分钟，单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码的时间间隔60秒，单位：秒
SEND_SMS_CODE_INTERVAL = 300

# 登录错误的尝试次数
LOGIN_ERROR_MAX_TIMES = 5

# 登录错误的限制时间间隔10分钟,单位:秒
LOGIN_ERROR_FORBID_TIME = 600

# 七牛空间域名
QINIU_DOMIN_PREFIX = "http://oyucyko3w.bkt.clouddn.com/"

# 城区信息redis缓存时间，单位：秒
AREA_INFO_REDIS_EXPIRES = 7200

# 首页展示最多的房屋数量
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据的Redis缓存时间，单位：秒
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 房屋详情页展示的评论最大数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋详情页面数据Redis缓存时间，单位：秒
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 房屋列表页面每页显示条目数
HOUSE_LIST_PAGE_CAPACITY = 2

# 房屋列表页面Redis缓存时间，单位：秒
HOUSE_LIST_REDIS_EXPIRES = 7200
