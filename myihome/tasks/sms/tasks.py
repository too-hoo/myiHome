#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from myihome.tasks.main import celery_app
from myihome.libs.yuntongxun.sms import CCP


@celery_app.task
def send_sms(to, datas, temp_id):
    """send sms through async_task"""
    # celery's client  only depend on the function name and the args.
    cpp = CCP()
    ret = cpp.sendTemplateSMS(to, datas, temp_id)
    # return celery async_result value
    return ret
