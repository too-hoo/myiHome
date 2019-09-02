#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from celery import Celery
from myihome.tasks import config

# define celery object
celery_app = Celery("myihome")

# import config.py message
# or : celery_app.config_from_object("myihome.tasks.config")
celery_app.config_from_object(config)

# auto search async_task, it will find the default file: task.py
celery_app.autodiscover_tasks(["myihome.tasks.sms"])

