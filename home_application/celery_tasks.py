# -*- coding: utf-8 -*-
"""
celery 任务示例

本地启动celery命令: python  manage.py  celery  worker  --settings=settings
周期性任务还需要启动celery调度命令：python  manage.py  celerybeat --settings=settings
"""
import datetime,time
import base64

from celery import task
from celery.schedules import crontab
from celery.task import periodic_task

from common.log import logger

import views

from home_application.models import host_use,monitor_list

from blueking.component.shortcuts import get_client_by_user
import paramiko
import sys,os
from django.forms.models import model_to_dict 
from io import StringIO

#写前端页面，通过输入秘钥的值，登录通过paramiko，ssh下发命令，获取虚下发命令的主机列表
#获取结果展示
#获取到结果后，判断结果的值，如果不在阈值范围内，就执行resize操作

@task
def get_monitor_data():
    m_list=[]
    res={}
    result=''
    host_used=""
    cmd="""
        #!/bin/bash

        MEMORY=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
        DISK=$(df -h | awk '$NF=="/"{printf "%s", $5}')
        CPU=$(top -bn1 | grep load | awk '{printf "%.2f%%", $(NF-2)}')
        DATE=$(date "+%Y-%m-%d %H:%M:%S")
        echo -e "$DATE|$MEMORY|$DISK|$CPU"
    """
    moni_list = list(monitor_list.objects.all())

    for ml in moni_list:
        temp = model_to_dict(ml)
        m_list.append({'data':temp})
    
    for l in m_list:
        host=l.get('data').get('ip')
        user=l.get('data').get('user')
        key=l.get('data').get('passwd')
        connecttype=l.get('data').get('connecttype')
        s = paramiko.SSHClient()
        s.load_system_host_keys()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if(connecttype=='pravitekey'):
            privatekeyfile = os.path.expanduser('d:\\ff.pem')
            private_key = paramiko.RSAKey.from_private_key_file(privatekeyfile)
            s.connect(host,22,user,pkey=private_key,timeout=60)
        if(connecttype=='passwd'):
            s.connect(hostname=host, port=22, username=user, password=key)

        stdin,stdout,stderr = s.exec_command(cmd)
        result=stdout.read()
        temp=result.split("|")
        s.close()
        if(temp):
            h_use = host_use(ip=host,memory=temp[1],disk=temp[2],cpu=temp[3],time=temp[0],region="public",moudle="consul",clound_area="default area",system="linux")
            h_use.save()

  #下一步动作，在周期任务取host_use库表，查询每个主机的cpu\disk\memory使用情况，根据条件执行resize

def execute_task(client, biz_id, job_instance_id, ip):
    """
    执行 celery 异步任务

    调用celery任务方法:
        task.delay(arg1, arg2, kwarg1='x', kwarg2='y')
        task.apply_async(args=[arg1, arg2], kwargs={'kwarg1': 'x', 'kwarg2': 'y'})
        delay(): 简便方法，类似调用普通函数
        apply_async(): 设置celery的额外执行选项时必须使用该方法，如定时（eta）等
                      详见 ：http://celery.readthedocs.org/en/latest/userguide/calling.html
    """
    now = datetime.datetime.now()
    logger.error(u"celery 定时任务启动，将在60s后执行，当前时间：{}".format(now))
    # 调用定时任务



@periodic_task(run_every=crontab(minute='*/1', hour='*', day_of_week="*"))
def get_time():
    """
    celery 周期任务示例

    run_every=crontab(minute='*/5', hour='*', day_of_week="*")：每 5 分钟执行一次任务
    periodic_task：程序运行时自动触发周期任务
    """
    get_monitor_data()


    



