#!/usr/bin/env python  
# _#_ coding:utf-8 _*_  
import random,os
from OpsManage.utils import base
from django.http import HttpResponseRedirect,JsonResponse
from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from OpsManage.models import (Global_Config,Email_Config,Assets,
                              Cron_Config,Log_Assets,Project_Config,
                              Ansible_Playbook)
from orders.models import Order_System
from django.db.models import Count
from django.contrib.auth.decorators import permission_required

@login_required(login_url='/login')
def index(request):
    userList = User.objects.all()
    assetsList = Assets.objects.all().order_by("-id")
    for ds in assetsList:
        ds.nks = ds.networkcard_assets_set.all()
    assetOnline = Assets.objects.filter(status='已上线').count()
    assetOffline = Assets.objects.filter(status='已下线').count()
    assetMaintain = Assets.objects.filter(status='维修中').count()
    assetsNumber = Assets.objects.values('assets_type').annotate(dcount=Count('assets_type'))
    return render(request, 'index.html', {"user": request.user, "totalAssets": assetsList.count(),
                                                       "assetOnline": assetOnline, "assetOffline": assetOffline,
                                                       "assetMaintain": assetMaintain,
                                                         "assetsList":assetsList,"assetsNumber":assetsNumber,
                                                         'userList':userList},
                  )

def login(request):
    if request.session.get('username') is not None:
        return HttpResponseRedirect('/',{"user":request.user})
    else:
        username = request.POST.get('username')
        password = request.POST.get('password') 
        user = auth.authenticate(username=username,password=password)
        if user and user.is_active:
            auth.login(request,user)
            request.session['username'] = username
            return HttpResponseRedirect('/user/center/',{"user":request.user})
        else:
            if request.method == "POST":
                return render(request,'login.html',{"login_error_info":"用户名不存在，或者密码错误！","username":username},)  
            else:
                return render(request,'login.html') 
            
            
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/login')

def noperm(request):
    return render(request,'noperm.html',{"user":request.user}) 

@login_required(login_url='/login')
@permission_required('OpsManage.can_change_global_config',login_url='/noperm/')
def config(request):
    if request.method == "GET":
        try: 
            config = Global_Config.objects.get(id=1)
        except:
            config = None
        try:
            email = Email_Config.objects.get(id=1)
        except:
            email =None
        return render(request,'config.html',{"user":request.user,"config":config,
                                                 "email":email})
    elif request.method == "POST":
        if request.POST.get('op') == "log":
            try:
                count = Global_Config.objects.filter(id=1).count()
            except:
                count = 0
            if count > 0:
                Global_Config.objects.filter(id=1).update(
                                                      ansible_model =  request.POST.get('ansible_model'),
                                                      ansible_playbook =  request.POST.get('ansible_playbook'),
                                                      cron =  request.POST.get('cron'),
                                                      project =  request.POST.get('project'),
                                                      assets =  request.POST.get('assets',0),
                                                      server =  request.POST.get('server',0),
                                                      email =  request.POST.get('email',0),   
                                                      webssh =  request.POST.get('webssh',0),  
                                                      sql =  request.POST.get('sql',0),                                                 
                                                    )
            else:
                config = Global_Config.objects.create(
                                                      ansible_model =  request.POST.get('ansible_model'),
                                                      ansible_playbook =  request.POST.get('ansible_playbook'),
                                                      cron =  request.POST.get('cron'),
                                                      project =  request.POST.get('project'),
                                                      assets =  request.POST.get('assets'),
                                                      server =  request.POST.get('server'),
                                                      email =  request.POST.get('email'),
                                                      webssh =  request.POST.get('webssh',0),
                                                      sql =  request.POST.get('sql'), 
                                                    )    
            return JsonResponse({'msg':'配置修改成功',"code":200,'data':[]})   
        elif request.POST.get('op') == "email":
            try:
                count = Email_Config.objects.filter(id=1).count()
            except:
                count = 0
            if count > 0:
                Email_Config.objects.filter(id=1).update(
                                                      site =  request.POST.get('site'),
                                                      host =  request.POST.get('host',None),
                                                      port =  request.POST.get('port',None),
                                                      user =  request.POST.get('user',None),
                                                      passwd =  request.POST.get('passwd',None),
                                                      subject =  request.POST.get('subject',None),
                                                      cc_user =  request.POST.get('cc_user',None),                                                  
                                                    )
            else:
                Email_Config.objects.create(
                                            site =  request.POST.get('site'),
                                            host =  request.POST.get('host',None),
                                            port =  request.POST.get('port',None),
                                            user =  request.POST.get('user',None),
                                            passwd =  request.POST.get('passwd',None),
                                            subject =  request.POST.get('subject',None),
                                            cc_user =  request.POST.get('cc_user',None), 
                                            )    
            return JsonResponse({'msg':'配置修改成功',"code":200,'data':[]}) 
        
