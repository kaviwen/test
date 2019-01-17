# -*- coding: utf-8 -*-

from common.mymako import render_mako_context,render_json
from blueking.component.shortcuts import get_client_by_request
import base64
import time
import pdb,json
from novaclient import client
from home_application.models import monitor_list,host_use
from django.core import serializers
from django.forms.models import model_to_dict   
import paramiko
import sys,os
from io import StringIO

ip_all=[]
ip_list=[]

def home_page(request):
    """
    首页
    """
#   定时任务
#   from home_application.celery_tasks import async_task
#   a=async_task.apply_async(args=[1,2,1],countdown=30)
#    from home_application.celery_tasks import get_time
#    get_time()



    return render_mako_context(request, '/home_application/home.html')
def host(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/host.html')
def flavor(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/flavor.html')

def remote(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/remote2.html')


def volume(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/volume.html')

def host_used(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/host_used.html')

def alarm(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/alarm.html')

def set(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/set.html')

def operate(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/operate.html')



def cpu_resize(request):
    """
    定义cpu调整的函数，将cpu_down_list，cpu_up_list传入，然后根据列表的主机清单一个个做调整操作
    """
    nova = create_client_nova()
    cpu_up_list,cpu_down_list,memory_up_list,memory_down_list,disk_up_list,disk_down_list = get_resize_list()
    flavor_list=nova.flavors.list()
    server_list=nova.servers.list()
    key_list,flavor_result=get_flavors_list()
    for c in cpu_down_list:                                   #减配置
        for s in server_list:
            if (c==s.networks['external']):                  #找到需要resize的ip在openstack里面对应的server_name及flavor
                server_name=s.name
                server_flavor_id=s.flavor['id']              
                for f in flavor_list:
                    pdb.set_trace()
                    if(f.id==server_flavor_id):                                            #根据flavor的vcpu核数找到下一个调整的flavor
                        vcpus=f.vcpus
                        p=key_list.index(vcpus)-1
                        if (p>=0):
                            flavor=flavor_result[p]
                            s.resize(server_name,flavor)           #差确认动作
                        else:
                            print("已是最小配置，如需继续调整，请申请人工处理")

    for c in cpu_up_list:                                   #减配置
        for s in server_list:
            if (c==s.networks['external']):                  #找到需要resize的ip在openstack里面对应的server_name及flavor
                server_name=s.name
                server_flavor_id=s.flavor['id']              
                for f in flavor_list:
                    pdb.set_trace()
                    if(f.id==server_flavor_id):                                            #根据flavor的vcpu核数找到下一个调整的flavor
                        vcpus=f.vcpus
                        p=key_list.index(vcpus)-1
                        if (p<=len(key_list)):
                            flavor=flavor_result[p]
                            s.resize(server_name,flavor)     #差确认动作
                        else:
                            print("已到最大配置，如需继续调整，请申请人工处理")    

    result={'res':True}                    
    return render_json(result)




def get_flavors_list():

#返回数据示例
#flavor_result=
#{1: u'adfc6ef5-0678-4f3c-9c75-8f9c82f000d7',
 #2: u'67cd2423-5e8d-4b24-8366-e7aa4ced5f6d',
 #4: u'c8ae7f6e-016b-4487-8b78-afe0672dcd55'}
#key_list=[1, 2, 4]

#将flavor的vcpu核数作为key，flavor的id作为值
#传入resize函数，需要resize的主机根据需要通过Key_list查找比原本vcpu大或者小的模板，执行resize


    flavor_list=[]
    flavor_result={}
    key_list=[]
    nova = create_client_nova()
    flavor_list=nova.flavors.list()
    for f in flavor_list:
        flavor_result[f.vcpus]=f
    key_list=flavor_result.keys()
    key_list.sort()
    return key_list,flavor_result      #返回数据示例：key_list=[1, 2, 4]



def get_resize_list():    #获取需要做调整的主机列表
     
    """
    获取需要做调整的主机列表
    返回数据示例:
    cpu_down_list=[[u'172.50.19.242'], [u'172.50.19.244']]
    cpu_up_list,cpu_down_list,memory_up_list,memory_down_list,disk_up_list,disk_down_list=[[u'172.50.19.242'], [u'172.50.19.244']]
    """

    aver_cpu_list=[]
    aver_disk_list=[]
    aver_memory_list=[]
    server_result=[]

    cpu_up_list=[]         #cpu>0.8,放入需要cpu调增的列表
    cpu_down_list=[]       #cpu<0.2,放入需要cpu调减的列表

    memory_up_list=[]
    memory_down_list=[]

    disk_up_list=[]
    disk_down_list=[]

    aver_cpu_list,aver_disk_list,aver_memory_list=average_monitor_data()
    #server_result=home_application.views.openstack_host_list()   #取openstack环境的主机列表
    #对取出的平均值，判断每一个值是否超过阈值，超过则把对应的键存到list里面（键是对应主机的ip），然后再根据需要进行resize的主机进行resize
    #阈值设定20%<cpu<80%,20%<memory<80%,20%<disk<80%
    for cpu in aver_cpu_list:
        aver_cpu=float(cpu.values()[0])
        if(aver_cpu>0.8):
            cpu_up_list.append(cpu.keys())  #cpu>0.8,将ip放入需要cpu调增的列表
        if(aver_cpu<0.2):
            cpu_down_list.append(cpu.keys())

    for memory in aver_memory_list:
        aver_memory=float(memory.values()[0])
        if(aver_memory>0.8):
            memory_up_list.append(memory.keys())  #memory>0.8,将ip放入需要memory调增的列表
        if(aver_memory<0.2):
            memory_down_list.append(memory.keys())    

    for disk in aver_disk_list:
        aver_disk=float(disk.values()[0])
        if(aver_disk>0.8):
            disk_up_list.append(disk.keys())  #disk>0.8,将ip放入需要disk调增的列表
        if(aver_disk<0.2):
            disk_down_list.append(disk.keys())     

    return cpu_up_list,cpu_down_list,memory_up_list,memory_down_list,disk_up_list,disk_down_list





#定义监控数据处理程序，并根据监控数据判断是否执行resize函数
def average_monitor_data():
    moni_data=[]
    moni_data=[]
    aver_cpu_list=[]
    aver_disk_list=[]
    aver_memory_list=[]
    moni_list=monitor_list.objects.all().values('ip')  #主机监控列表：[{'ip': u'172.50.19.242'}, {'ip': u'172.50.19.244'}]
    for m in moni_list:  #取出每台主机的监控数据
        list_temp=[]
        temp=list(host_use.objects.filter(ip=m['ip']))
        if(len(temp)>4):                              #如果超过了五个数据点，就开始取数，不超过五个数据点不做操作
            i=5
            while i>0:                                #从主机的监控数据中取出最近的5个数据点
                list_temp.append(model_to_dict(temp[-i]))    #model_to_dict()可以将数据库对象转换成字典对象
                i=i-1
            moni_data.append(list_temp)    #见数据示例
    if(moni_data):
        for m in moni_data:         #将每台主机对应的监控指标取出，并求和
            cpu=0
            disk=0
            memory=0
            for d in m:
                s=float(str(d['cpu'].strip('\n').strip('%')))/100
                cpu=s+cpu
                aver_cpu='%.5f' % (cpu/5)

                s1=float(str(d['disk'].strip('\n').strip('%')))/100
                disk=s1+disk
                aver_disk='%.5f' % (disk/5)

                s2=float(str(d['memory'].strip('\n').strip('%')))/100
                memory=s2+memory
                aver_memory='%.5f' % (memory/5)            
            aver_cpu_list.append({m[0]['ip']:aver_cpu}) #aver_cpu_list ：[{u'172.50.19.242': 0.012}, {u'172.50.19.244': 0.0238}]，监控列表中每个主机的最近五个数据点的cpu使用率平均值
            aver_disk_list.append({m[0]['ip']:aver_disk}) 
            aver_memory_list.append({m[0]['ip']:aver_memory})

    return aver_cpu_list,aver_disk_list,aver_memory_list




""" 
数据示例：moni_data      
[
    #每个list元素里面是一个监控主机的数据，每个监控主机取5个最近的数据点
    [{'clound_area': u'default area',
    'cpu': u'0.24%\n',
    'disk': u'39%',
     u'id': 7,
    'ip': u'172.50.19.242',
    'memory': u'36.71%',
    'time': u'2018-12-16 01:53:03'}
    {...},             
    {...},
    {...},
    {...}
    ],
    [{'clound_area': u'default area',
   'cpu': u'0.51%\n',
   'disk': u'35%',
   u'id': 12,
   'ip': u'172.50.19.244',
   'memory': u'5.20%',
   'moudle': u'consul',
   'region': u'public',
   'system': u'linux',
   'time': u'2018-12-16 01:55:09'},
    {...},
    {...},
    {...},
    {...}
]
]"""




def get_monitor_data():      #向监控主机发命令，取得监控数据
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







#根据监控列表向监控主机下发任务，并获取监控数据
def get_monitor_data(request):
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
            privatekeyfile = os.path.expanduser('d:\\ff.pem')   #下一步解决秘钥由用户上传，目前是写死的
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
    
    return render_json(result)

  
    
    


#获取用户输入需监控的主机列表
def get_monitor_list(request):
    user = request.POST.get('user')
    ip = request.POST.get('ip')
    passwd = request.POST.get('passwd')
    connecttype = request.POST.get('radio')
    if(ip):
        moni_list = monitor_list(user=user,passwd=passwd,ip=ip,connecttype=connecttype)
        moni_list.save()
#        return redirect("/homepage")
    moni_list =  monitor_list.objects.all() 
    data = {}
    province  = serializers.serialize("json",moni_list) #serializers.serialize函数接受一个格式和queryset，返回序列化后的数据  
    res = {'result': True, 'data': json.loads(province)}
    
    return render_json(res)


def openstack_host_list():    #获取对接的openstack环境的主机列表
    server_result=[]
    nova = create_client_nova()
    server_list=nova.servers.list()
    for server in server_list:
        server_result.append({
                'name': server.name,
                'id': server.id,
                'status':server.status,
                'ip':server.networks.values()[0]
            })
    return server_result

def get_openstack_server_list(request):    #响应前端，讲主机列表展示在前端页面
    server_result=openstack_host_list()
    result = {'result': True, 'data': server_result}
#    pdb.set_trace()
    return render_json(result)


def get_openstack_flavor_list(request):   
    flavor_list=[]
    flavor_result=[]
    nova = create_client_nova()
    flavor_list=nova.flavors.list()
    for flavor in flavor_list:
        flavor_result.append({
            'name':flavor.name,
            'id':flavor.id,
            'ram':flavor.ram,
        })
    result = {'result': True, 'data': flavor_result}
    return render_json(result)

def get_openstack_volume_list(request):
    volume_list=[]
    volume_result=[]
    nova = create_client_nova()
   
    volume_list=nova.volumes.list()
    for volume in volume_list:
        volume_result.append({
            'name':volume.name,
            'size':volume.size,
            'status':volume.status,
        })
    result = {'result': True, 'data': volume_result}
    return render_json(result)

def create_client_nova():
    from novaclient import client
    return client.Client(
        version='2.1',
        username='admin',
        password='123456',
        project_name='admin',
        project_domain_name='default',
        user_domain_name='default',
        auth_url='http://controller:5000/v3'
    )

    

def get_biz_list(request):
    """
    获取所有业务
    """
    biz_list = []
    client = get_client_by_request(request)
    kwargs = {
        'fields': ['bk_biz_id','bk_biz_name']
    }
    resp = client.cc.search_business(**kwargs)

    if resp.get('result'):
        data = resp.get('data', {}).get('info', {})
        for _d in data:
            biz_list.append({
                'name': _d.get('bk_biz_name'),
                'id': _d.get('bk_biz_id'),
            })

    result = {'result': resp.get('result'), 'data': biz_list}
    return render_json(result)
#    return (biz_list)

def get_ip_by_bizid(request):
    """
    获取业务下IP
    """
    biz_id = int(request.GET.get('biz_id'))
    client = get_client_by_request(request)
    kwargs = { 'bk_biz_id': biz_id,
               'condition': [
                {
                    'bk_obj_id': 'biz',
                    'fields': ['bk_biz_id'],
                    'condition': [
                        {
                            'field': 'bk_biz_id',
                            'operator': '$eq',
                            'value': biz_id
                        }
                    ]
                }
            ]
        }
    resp = client.cc.search_host(**kwargs)
    global ip_list
    ip_list = ["all",]
    if resp.get('result'):
        data = resp.get('data', {}).get('info', {})
        for _d in data:
            _hostinfo = _d.get('host', {})
            if _hostinfo.get('bk_host_innerip') not in ip_list:
                ip_list.append(_hostinfo.get('bk_host_innerip'))
    global ip_all
    ip_all = [{'ip': _ip} for _ip in ip_list]
    result = {'result': resp.get('result'), 'data': ip_all}
    return render_json(result)

def get_instance_id(client,biz_id,ip):

    cmd=base64.b64encode("""
        #!/bin/bash

        MEMORY=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
        DISK=$(df -h | awk '$NF=="/"{printf "%s", $5}')
        CPU=$(top -bn1 | grep load | awk '{printf "%.2f%%", $(NF-2)}')
        DATE=$(date "+%Y-%m-%d %H:%M:%S")
        echo -e "$DATE|$MEMORY|$DISK|$CPU"
    """)
    

#    区分是查询一个主机还是多台主机，当传进来的IP是一个列表则是多台主机，多台主机是ip_list第一个元素为all，需要删除再传给api。

    if(isinstance(ip, list)):
        if(ip_list[0]=='all'):
            ip_list.pop(0)
        ip_all = [{'ip': _ip,'bk_cloud_id':0} for _ip in ip_list]
    else:
        ip_all=[{'ip': ip,'bk_cloud_id':0}]
       
    args={"bk_biz_id":biz_id,"script_content":cmd,"account":"root","ip_list":ip_all}      
    # 调用作业平台API，或者作业执行实例ID  
    res = client.job.fast_execute_script(**args)
    job_instance_id = res.get('data',{})['job_instance_id'] 
    result = res.get('result',{})
    result = {'result': result, 'data': job_instance_id}

    if(result.get('result')):
        return(result)
    else:
        return('-1')


def execute_job(request):
    """
    执行磁盘容量查询作业
    """
    biz_id = request.POST.get('biz_id')
    ip = request.POST.get('ip')
    if(ip=='all'):
        ip=ip_all
    # 调用作业平台API，或者作业执行实例ID 
    client = get_client_by_request(request)
    result = get_instance_id(client, biz_id, ip)
    return render_json(result)



def get_capacity(request):
    """
    获取作业执行结果，并解析执行结果展示
    """

    job_instance_id = request.GET.get('job_instance_id')
    biz_id = request.GET.get('biz_id')
    ip = request.GET.get('ip')

    # 调用作业平台API，或者作业执行详情，解析获取磁盘容量信息
    client = get_client_by_request(request)
    is_finish, capacity_data = get_host_capaticy(client, biz_id, job_instance_id, ip)


    #下一步，将capacity_data数据入库，再通过读取数据库传给ajax。以此来实现展示时的删除操作。

    return render_json({'code': 0, 'message': 'success', 'data': capacity_data,'result':is_finish})


def get_host_capaticy(client, biz_id, job_instance_id, ip):

    kwargs = {
        'bk_biz_id': biz_id,
        'job_instance_id': job_instance_id,
        }
#    time.sleep(3)
    resp = client.job.get_job_instance_log(**kwargs)
    capacity_data=[]
    is_finish = False
    result = resp.get('data')[0].get('is_finished')
    logs = []
    host_useds=[]
    ip=[]
    i=0
    region = "公共组件"
    if(result) :
        data = resp.get('data')
        for _d in data[0]['step_results'][0].get('ip_logs'):
#            if _d.get('is_finished'):
            if (result):
                is_finish = True
                logs.append(_d.get('log_content'))
                ip.append(_d.get('ip'))
        """
        将logs=[u'2018-10-13 19:01:04|21.39%|19%|2.43%\n', u'2018-10-13 19:01:03|45.34%|6%|0.03%\n']转换为
        host_used=[[u'2018-10-13 19:01:04', u'21.39%', u'19%', u'2.43%\n'],[u'2018-10-13 19:01:03', u'45.34%', u'6%', u'0.03%\n']]
        """
        for log in logs:
            log=log.split("|")
            host_useds.append(log)   

        
        
        for host_used in host_useds:                      
            host=host_used[1]+'/'+host_used[2]+'/'+host_used[3]
#            pdb.set_trace()
            capacity_data.append({
                "ip":ip[i],
                "host_used":host,
                "time":host_used[0],
                "region":region,
                "moudle":"consul",
                "clound_area":"default area",
                "system":"linux"
            })
            i=i+1     
#        logs = [{'logs': res} for res in log]
#        result = {"result":is_finish,"data":capacity_data}


        return is_finish,capacity_data
    else:
        return is_finish,'-1'


"""
get_host_capaticy返回数据示例：







"""

def resize(request):
    if request.method == 'POST':
        servername = request.POST.get('servername','').strip()
        flavorname = request.POST.get('flavorname','').strip()
        openstackapi.resize_server(servername,flavorname)

        servers = openstackapi.get_servers()
        flavors = openstackapi.get_flavors()
        images = openstackapi.get_images()
        networks = openstackapi.get_networks()
        return render_to_response('home_application/homepage.html',
                                  {'servers': servers, 'flavors': flavors, 'images': images, 'networks': networks,
                                   })

    else:
        print("get方式请求")
        return render_to_response('home_application/homepage.html')