#!/usr/bin/env python
# -*-encoding:UTF-8-*-
# name must the name :BROKER_URL and CELERY_RESULT_BACKEND
BROKER_URL = "redis://127.0.0.1:6379/1"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/2"
