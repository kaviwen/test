# -*- coding: utf-8 -*-

from django.conf.urls import patterns

urlpatterns = patterns(
    'home_application.views',
    (r'^home_page/$', 'home_page'),
    (r'^host/$', 'host'),
    (r'^flavor/$', 'flavor'),
     (r'^volume/$', 'volume'),
    (r'^host_used/$', 'host_used'),
    (r'^alarm/$', 'alarm'),
    (r'^set/$', 'set'),
    (r'^operate/$', 'operate'),
    (r'^remote2/$', 'remote'),
    (r'^$', 'home_page'),
    (r'^get_biz_list/$', 'get_biz_list'),
    (r'^get_ip_by_bizid/$', 'get_ip_by_bizid'),
    (r'^execute_job/$', 'execute_job'),
    (r'^get_monitor_list/$', 'get_monitor_list'),
    (r'^get_capacity/$', 'get_capacity'),
    (r'^get_monitor_data/$', 'get_monitor_data'),  
    (r'^average_monitor_data/$', 'average_monitor_data'),  
    (r'^get_openstack_server_list/$', 'get_openstack_server_list'),
    (r'^get_openstack_flavor_list/$', 'get_openstack_flavor_list'),
    (r'^get_openstack_volume_list/$', 'get_openstack_volume_list'),    
    (r'^cpu_resize/$', 'cpu_resize'),  
)
