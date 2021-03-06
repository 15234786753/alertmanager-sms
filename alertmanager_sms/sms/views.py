from django.shortcuts import render,HttpResponse

# Create your views here.
import hashlib
import time
import requests
import urllib
import json
import sys
import logging
from ldap3 import Server, Connection, ALL, NTLM, ALL_ATTRIBUTES, LEVEL, SUBTREE

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    # filename='/tmp/zbxAlert/sms_alert.log',
                    filename='sms_alert.log',
                    filemode='a+')

def pwd_md5(pwd_text):
    m = hashlib.md5()
    m.update(pwd_text.encode("utf8"))
    pwd_md5 = m.hexdigest()
    return pwd_md5

def urlencode(content):
    content = content.decode('utf8')
    content = content.encode('gb2312')
    return urllib.quote(content)

def main(mobile,msg):
    url = 'http://www.dh3t.com/json/sms/Submit'
    current_time = time.strftime("%m%d%H%M%S", time.localtime(time.time()))
    pwd_text = "8uUri5hT"
    # mobile = sys.argv[1]
    # msg = sys.argv[2]
    logging.info("mobile: %s, msg: %s" % (mobile, msg))
    headers={
        'Content-Type': 'application/json',
    }

    data = {
    "account":"dh55021",
    "password":pwd_md5(pwd_text),
    "msgid":"2c92825934837c4d0134837dcba00150",
    "phones":mobile,
    "content":msg,
    "sign":"【千丁】","subcode":"",
    "sendtime":"",
    }

    logging.info('requests.post: %s' % json.dumps(data))
    ret = requests.post(url, data=json.dumps(data), headers=headers).json()
    logging.info("send sms response: %s" % ret)

alert_msg = None
alert_all = None
def sms(request):
    '''
    :param request: ?username=wangkai
    :return: ok
    '''
    # 获取姓名对应的手机号
    try:
        person = request.GET.get('username')
        person_lst = person.split('|')
    except AttributeError as e:
        print(f'Error:{e},person:{person_lst}')
    except Exception as eother:
        print(eother)

    if len(person_lst) == 0:
        person_lst = ['wangkai']

    server = Server('ldap://dc-01.qdingnet.cn', port=389, get_info=ALL)
    # conn =Connection(server,'dc=qdingnet,dc=cn','admin',auto_bind=True)
    conn = Connection(server, user='itadmin', password='Aa123456789', auto_bind=True)
    # 获取告警数据
    alert_all = json.loads(request.body.decode('utf-8'))
    print(alert_all,type(alert_all))
    alert_num = len(alert_all['alerts'])
    print(alert_num)
    for i in alert_num:
        try:
            # global alert_all
            alert_app = alert_all['alerts'][i]['labels']['job']
            alert_item = alert_all['alerts'][i]['labels']['alertname']
            alert_instance = alert_all['alerts'][i]['labels']['instance']
            alert_summary = alert_all['alerts'][i]['annotations']['summary']
            alert_value = alert_all['alerts'][i]['annotations']['value']
            alert_startsAt = alert_all['alerts'][i]['startsAt']
            alert_endsAt = alert_all['alerts'][i]['endsAt']
        except Exception as e:
            print('Error:',e)
            # print(alert_all)

        else:
            # 告警模板
            global alert_msg
            alert_msg = f'''
            应用名称：{alert_app}
            告警项目：{alert_item}
            告警实例：{alert_instance}
            告警描述：{alert_summary}
            当前值：{alert_value}
            开始时间: {alert_startsAt}
            '''
            print(alert_msg)

        for person in person_lst:
            conn.search('dc=qdingnet,dc=cn', '(sAMAccountName={})'.format(person), attributes=["telephoneNumber"])
            phone = conn.entries[0].telephoneNumber
            main(str(phone),alert_msg)

    return HttpResponse('ok')