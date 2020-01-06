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


def sms(request):
    '''
    :param request: ?username=wangkai
    :return: ok
    '''

    try:
        alert_all = json.loads(request.body.decode('utf-8'))
        alert_app = alert_all['alerts'][0]['labels']['job']
        alert_item = alert_all['alerts'][0]['labels']['alertname']
        alert_instance = alert_all['alerts'][0]['labels']['instance']
        alert_summary = alert_all['alerts'][0]['annotations']['summary']
        alert_value = alert_all['alerts'][0]['annotations']['value']
        alert_startsAt = alert_all['alerts'][0]['startsAt']
        alert_endsAt = alert_all['alerts'][0]['endsAt']
    except Exception as e:
        print('Error:',e)
        # alert_app = '---'
        # alert_item = '---'
        # alert_instance = '---'
        # alert_summary = '---'
        # alert_value = '---'
        # alert_startsAt = '---'
        # alert_endsAt = '---'
    else:
        # 告警模板
        alert_msg = f'''
        应用名称：{alert_app}
        告警项目：{alert_item}
        告警实例：{alert_instance}
        告警描述：{alert_summary}
        当前值：{alert_value}
        开始时间: {alert_startsAt}
        '''
    # print(alert_msg)

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

    for tel_num in person_lst:
        conn.search('dc=qdingnet,dc=cn', '(sAMAccountName={})'.format(tel_num), attributes=["telephoneNumber"])
        phone = conn.entries[0].telephoneNumber
        main(str(phone),alert_msg)

    return HttpResponse('ok')