#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 导入基础的正则转换器
from werkzeug.routing import BaseConverter


# 自定义正则转换器
class ReConverter(BaseConverter):
    """自定义静态文件路由转换器"""

    def __init__(self, url_map, regex):
        # 调用父类的初始化方法
        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


# xrange, 解决python3没有xrange的问题
def xrange(start, end=None, step=1):
    if end == None:
        end = start
        start = 0
    if step > 0:
        while start < end:
            yield start
            start += step
    elif step < 0:
        while start > end:
            yield start
            start += step
    else:
        return 'step can not be zero'
