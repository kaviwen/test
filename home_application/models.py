# -*- coding: utf-8 -*-
from django.db import models

class host_use(models.Model):
    ip = models.CharField(max_length=50,null=True,blank=True)
    cpu = models.CharField(max_length=50,null=True,blank=True)
    memory = models.CharField(max_length=50,null=True,blank=True)
    disk = models.CharField(max_length=50,null=True,blank=True)
    time = models.CharField(max_length=50,null=True,blank=True)
    region = models.CharField(max_length=50,null=True,blank=True)
    moudle = models.CharField(max_length=50,null=True,blank=True)
    clound_area = models.CharField(max_length=50,null=True,blank=True)
    system = models.CharField(max_length=50,null=True,blank=True)

    def __unicode__(self):
        return self.time
    
    class  Meta:
        ordering = ['id']

class monitor_list(models.Model):
    ip =models.CharField(max_length=50,null=True,blank=True)
    user =models.CharField(max_length=50,null=True,blank=True)
    passwd =models.CharField(max_length=50000,null=True,blank=True)
    connecttype = models.CharField(max_length=50,null=True,blank=True)
    def __unicode__(self):
        return self.ip
    
    class  Meta:
        ordering = ['id']