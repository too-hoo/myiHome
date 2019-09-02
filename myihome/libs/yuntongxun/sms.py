# -*- coding: UTF-8 -*-

from myihome.libs.yuntongxun.CCPRestSDK import REST
import configparser

# 主帐号
accountSid = '8a216da86cdb6950016ce04bd90002df'

# 主帐号Token
accountToken = '5e1a1831ee4a4b41a0aa0eb9b3ccc401'

# 应用Id
appId = '8a216da86cdb6950016ce04bd95a02e6'

# 请求地址，格式如下，不需要写http://
serverIP = 'app.cloopen.com'

# 请求端口
serverPort = '8883'

# REST版本号
softVersion = '2013-12-26'


# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# @param $tempId 模板Id


class CCP(object):
    """自己封装的发送短信的辅助类,可以取相同的名字CCP"""
    # 用来保存对象的类属性
    instance = None

    def __new__(cls):
        # 使用单例模式,在__new__这里的时候还没有任何的对象产生
        # 判断CCP类有没有创建好的对象，如果没有，创建一个对象(并保存)，如果有，直接返回
        if cls.instance is None:
            obj = super(CCP, cls).__new__(cls)  # 调用父类创建对象,cls参数一定要传,和__init__()方法是不一样的

            # 初始化REST yuntongxun 初始化的时候只想运行一次这个代码,将self对象转换成obj对象
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            # 保存obj到实例instance中
            cls.instance = obj
        return cls.instance

    def sendTemplateSMS(self, to, datas, temp_Id):

        result = self.rest.sendTemplateSMS(to, datas, temp_Id)
        # 发送的短信后返回的信息打印
        # for k,v in result.items():
        #
        #     if k == 'templateSMS':
        #             for k, s in v.items():
        #                 print('%s:%s' % (k, s))
        #     else:
        #         print('%s:%s' % (k, v))
        # statusCode: 000000
        # smsMessageSid: 0ae37f75c9974b9a91d320ed078e1f45
        # dateCreated: 20190830115845
        # None
        status_code = result.get('statusCode')  # 不应该使用方括号,应该使用get()获取
        if status_code == '000000':
            return 0  # 000000表示发送成功
        return -1  # 发送失败, -1表示有问题


# 测试
if __name__ == '__main__':
    ccp = CCP()
    # ('手机号码',["验证码", 有效分钟], 短信模板)
    ret = ccp.sendTemplateSMS('13414851554', ["123", "5"], 1)
    print(ret)

# sendTemplateSMS(手机号码,内容数据,模板Id)
