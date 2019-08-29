#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from . import api
from myihome import db
import logging
from flask import current_app  # flask 封装的全局应用对象:当前的app


# 直接使用蓝图api
@api.route("/index")
def index():
    current_app.logger.error("error msg")
    current_app.logger.warn("warn msg")
    current_app.logger.info("info msg")
    current_app.logger.debug("debug msg")
    return "index page"
