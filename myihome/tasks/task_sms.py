#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from celery import Celery
from myihome.libs.yuntongxun.sms import CCP

# define celery object
celery_app = Celery("myihome", broker="redis://127.0.0.1:6379/1")


@celery_app.task
def send_sms(to, datas, temp_id):
    """send sms through async_task"""
    cpp = CCP()
    cpp.sendTemplateSMS(to, datas, temp_id)

