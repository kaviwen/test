# -*- coding: utf-8 -*-

# import from apps here


# import from lib
# ===============================================================================
# from django.contrib import admin
# from apps.__.models import aaaa
#
# admin.site.register(aaaa)
# ===============================================================================
from django.contrib import admin

# Register your models here.
from home_application.models import host_use,monitor_list

admin.site.register(host_use)
admin.site.register(monitor_list)