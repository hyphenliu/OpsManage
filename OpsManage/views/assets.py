#!/usr/bin/env python  
# _#_ coding:utf-8 _*_  
import os, xlrd, time, datetime
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from OpsManage.models import *
from django.db.models import Count
from OpsManage.utils.ansible_api_v2 import ANSRunner
from django.contrib.auth.models import Group, User
from OpsManage.utils import base
from OpsManage.tasks.assets import recordAssets
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from OpsManage.utils.logger import logger
from OpsManage.utils.execl import CellWriter


def getBaseAssets():
    try:
        groupList = Group.objects.all()
    except:
        groupList = []
    try:
        serviceList = Service_Assets.objects.all()
    except:
        serviceList = []
    try:
        zoneList = Zone_Assets.objects.all()
    except:
        zoneList = []
    # hyphen add 20180714
    try:
        typeList = Type_Assets.objects.all()
    except:
        typeList = []
    try:
        levelList = Level_Assets.objects.all()
    except:
        levelList = []
    try:
        statusList = Status_Assets.objects.all()
    except:
        statusList = []
    try:
        monitorList = Monitor_Assets.objects.all()
    except:
        monitorList = []
    try:
        providerList = Provider_Assets.objects.all()
    except:
        providerList = []
    try:
        contractList = Contract_Assets.objects.all()
    except:
        contractList = []
    try:
        maintenanceList = Maintenance_Assets.objects.all()
    except:
        maintenanceList = []
    # hyphen add end 20180714
    try:
        raidList = Raid_Assets.objects.all()
    except:
        raidList = []
    try:
        projectList = Project_Assets.objects.all()
    except:
        projectList = []
    return {"group": groupList, "project": projectList, "zone": zoneList,
            "raid": raidList, "service": serviceList, "monitor": monitorList,
            "contract": contractList, "provider": providerList, "status": statusList,
            "maintenance": maintenanceList, "type": typeList, "level": levelList}


@login_required(login_url='/login')
@permission_required('OpsManage.can_read_assets', login_url='/noperm/')
def assets_config(request):
    return render(request, 'assets/assets_config.html', {"user": request.user, "baseAssets": getBaseAssets()},
                  )


@login_required(login_url='/login')
@permission_required('OpsManage.can_add_assets', login_url='/noperm/')
def assets_add(request):
    if request.method == "GET":
        userList = User.objects.all()
        return render(request, 'assets/assets_add.html', {"user": request.user, "baseAssets": getBaseAssets(),
                                                          "userList": userList})


@login_required(login_url='/login')
@permission_required('OpsManage.can_read_assets', login_url='/noperm/')
def assets_list(request):
    userList = User.objects.all()
    assetsList = Assets.objects.all().order_by("-id")
    for ds in assetsList:
        ds.nks = ds.networkcard_assets_set.all()
    assetOnline = Assets.objects.filter(status=0).count()
    assetOffline = Assets.objects.filter(status=1).count()
    assetMaintain = Assets.objects.filter(status=2).count()
    assetsNumber = Assets.objects.values('assets_type').annotate(dcount=Count('assets_type'))
    return render(request, 'assets/assets_list.html', {"user": request.user, "totalAssets": assetsList.count(),
                                                       "assetOnline": assetOnline, "assetOffline": assetOffline,
                                                       "assetMaintain": assetMaintain, "baseAssets": getBaseAssets(),
                                                       "assetsList": assetsList, "assetsNumber": assetsNumber,
                                                       "userList": userList},
                  )


@login_required(login_url='/login')
@permission_required('OpsManage.can_read_assets', login_url='/noperm/')
def assets_view(request, aid):
    try:
        assets = Assets.objects.get(id=aid)
        userList = User.objects.all()

    except:
        return render(request, '404.html', {"user": request.user},
                      )
    if assets.assets_class in ['server', 'vmser']:
        try:
            asset_ram = assets.ram_assets_set.all()
        except:
            asset_ram = []
        try:
            asset_disk = assets.disk_assets_set.all()
        except:
            asset_disk = []
        try:
            asset_nks = assets.networkcard_assets_set.all()
        except Exception, ex:
            asset_nks = []
            logger.warn(msg="获取网卡设备资产失败: {ex}".format(ex=str(ex)))
        try:
            asset_body = assets.server_assets
        except:
            return render(request, 'assets/assets_view.html', {"user": request.user}, )
        return render(request, 'assets/assets_view.html', {"user": request.user, "asset_type": assets.assets_class,
                                                           "asset_main": assets, "asset_body": asset_body,
                                                           "asset_ram": asset_ram, "asset_disk": asset_disk,
                                                           "baseAssets": getBaseAssets(), "userList": userList,
                                                           "asset_nks": asset_nks},
                      )
    else:
        try:
            asset_body = assets.network_assets
        except:
            return render(request, 'assets/assets_view.html', {"user": request.user},
                          )
        return render(request, 'assets/assets_view.html', {"user": request.user, "asset_type": assets.assets_class,
                                                           "asset_main": assets, "asset_body": asset_body,
                                                           "baseAssets": getBaseAssets(), 'userList': userList},
                      )


@login_required(login_url='/login')
@permission_required('OpsManage.can_change_assets', login_url='/noperm/')
def assets_modf(request, aid):
    try:
        assets = Assets.objects.get(id=aid)
        userList = User.objects.all()
    except:
        return render(request, 'assets/assets_modf.html', {"user": request.user},
                      )
    if assets.assets_class in ['server', 'vmser']:
        try:
            asset_ram = assets.ram_assets_set.all()
        except:
            asset_ram = []
        try:
            asset_disk = assets.disk_assets_set.all()
        except:
            asset_disk = []
        try:
            asset_body = assets.server_assets
        except Exception, ex:
            logger.error(msg="修改资产失败: {ex}".format(ex=str(ex)))
            return render(request, '404.html', {"user": request.user},
                          )
        return render(request, 'assets/assets_modf.html', {"user": request.user, "asset_type": assets.assets_class,
                                                           "asset_main": assets, "asset_body": asset_body,
                                                           "asset_ram": asset_ram, "asset_disk": asset_disk,
                                                           "assets_data": getBaseAssets(), 'userList': userList},
                      )
    else:
        try:
            asset_body = assets.network_assets
        except:
            return render(request, 'assets/assets_modf.html', {"user": request.user},
                          )
        return render(request, 'assets/assets_modf.html', {"user": request.user, "asset_type": assets.assets_class,
                                                           "asset_main": assets, "asset_body": asset_body,
                                                           "assets_data": getBaseAssets(), 'userList': userList},
                      )


@login_required(login_url='/login')
@permission_required('OpsManage.can_change_server_assets', login_url='/noperm/')
def assets_facts(request, args=None):
    if request.method == "POST" and request.user.has_perm('OpsManage.change_server_assets'):
        server_id = request.POST.get('server_id')
        genre = request.POST.get('type')
        if genre == 'setup':
            try:
                server_assets = Server_Assets.objects.get(id=request.POST.get('server_id'))
                if server_assets.keyfile == 1:
                    resource = [
                        {"ip": server_assets.ip, "port": int(server_assets.port), "username": server_assets.username,
                         "sudo_passwd": server_assets.sudo_passwd}]
                else:
                    resource = [{"ip": server_assets.ip, "port": server_assets.port, "username": server_assets.username,
                                 "password": server_assets.passwd, "sudo_passwd": server_assets.sudo_passwd}]
            except Exception, ex:
                logger.error(msg="更新资产失败: {ex}".format(ex=str(ex)))
                return JsonResponse({'msg': "数据更新失败-查询不到该主机资料~", "code": 502})
            ANS = ANSRunner(resource)
            ANS.run_model(host_list=[server_assets.ip], module_name='setup', module_args="")
            data = ANS.handle_cmdb_data(ANS.get_model_result())
            if data:
                for ds in data:
                    status = ds.get('status')
                    if status == 0:
                        try:
                            assets = Assets.objects.get(id=server_assets.assets_id)
                            Assets.objects.filter(id=server_assets.assets_id).update(sn=ds.get('serial'),
                                                                                     model=ds.get('model'),
                                                                                     manufacturer=ds.get(
                                                                                         'manufacturer'))
                        except Exception, ex:
                            logger.error(msg="获取服务器信息失败: {ex}".format(ex=str(ex)))
                            return JsonResponse({'msg': "数据更新失败-查询不到该主机的资产信息", "code": 403})
                        try:
                            Server_Assets.objects.filter(id=server_id).update(cpu_number=ds.get('cpu_number'),
                                                                              kernel=ds.get('kernel'),
                                                                              selinux=ds.get('selinux'),
                                                                              hostname=ds.get('hostname'),
                                                                              system=ds.get('system'),
                                                                              cpu=ds.get('cpu'),
                                                                              disk_total=ds.get('disk_total'),
                                                                              cpu_core=ds.get('cpu_core'),
                                                                              swap=ds.get('swap'),
                                                                              ram_total=ds.get('ram_total'),
                                                                              vcpu_number=ds.get('vcpu_number')
                                                                              )
                            recordAssets.delay(user=str(request.user),
                                               content="修改服务器资产：{ip}".format(ip=server_assets.ip), type="server",
                                               id=server_assets.id)
                        except Exception, ex:
                            logger.error(msg="更新服务器信息失败: {ex}".format(ex=str(ex)))
                            return JsonResponse({'msg': "数据更新失败-写入数据失败", "code": 400})
                        for nk in ds.get('nks'):
                            macaddress = nk.get('macaddress')
                            count = NetworkCard_Assets.objects.filter(assets=assets, macaddress=macaddress).count()
                            if count > 0:
                                try:
                                    NetworkCard_Assets.objects.filter(assets=assets, macaddress=macaddress).update(
                                        assets=assets, device=nk.get('device'),
                                        ip=nk.get('address'), module=nk.get('module'),
                                        mtu=nk.get('mtu'), active=nk.get('active'))
                                except Exception, ex:
                                    logger.warn(msg="更新服务器网卡信息失败: {ex}".format(ex=str(ex)))
                            else:
                                try:
                                    NetworkCard_Assets.objects.create(assets=assets, device=nk.get('device'),
                                                                      macaddress=nk.get('macaddress'),
                                                                      ip=nk.get('address'), module=nk.get('module'),
                                                                      mtu=nk.get('mtu'), active=nk.get('active'))
                                except Exception, ex:
                                    logger.warn(msg="写入服务器网卡信息失败: {ex}".format(ex=str(ex)))

                    else:
                        return JsonResponse({'msg': "数据更新失败-无法链接主机~", "code": 502})
                return JsonResponse({'msg': "数据更新成功", "code": 200})
            else:
                return JsonResponse({'msg': "数据更新失败-请检查Ansible配置", "code": 400})

        elif genre == 'crawHw': # 非ansible自带库
            try:
                server_assets = Server_Assets.objects.get(id=server_id)
                assets = Assets.objects.get(id=server_assets.assets_id)
                if server_assets.keyfile == 1:
                    resource = [
                        {"ip": server_assets.ip, "port": int(server_assets.port), "username": server_assets.username,
                         "sudo_passwd": server_assets.sudo_passwd}]
                else:
                    resource = [{"ip": server_assets.ip, "port": server_assets.port, "username": server_assets.username,
                                 "password": server_assets.passwd, "sudo_passwd": server_assets.sudo_passwd}]
            except Exception, ex:
                logger.error(msg="更新硬件信息失败: {ex}".format(ex=ex))
                return JsonResponse({'msg': "数据更新失败-查询不到该主机资料~", "code": 502})
            ANS = ANSRunner(resource)
            ANS.run_model(host_list=[server_assets.ip], module_name='crawHw', module_args="")
            data = ANS.handle_cmdb_crawHw_data(ANS.get_model_result())
            if data:
                for ds in data:
                    if ds.get('mem_info'):
                        for mem in ds.get('mem_info'):
                            if Ram_Assets.objects.filter(assets=assets, device_slot=mem.get('slot')).count() > 0:
                                try:
                                    Ram_Assets.objects.filter(assets=assets, device_slot=mem.get('slot')).update(
                                        device_slot=mem.get('slot'), device_model=mem.get('serial'),
                                        device_brand=mem.get('manufacturer'), device_volume=mem.get('size'),
                                        device_status="Online"
                                    )

                                except Exception, ex:
                                    return JsonResponse({'msg': "数据更新失败-写入数据失败", "code": 400})
                            else:
                                try:
                                    Ram_Assets.objects.create(device_slot=mem.get('slot'),
                                                              device_model=mem.get('serial'),
                                                              device_brand=mem.get('manufacturer'),
                                                              device_volume=mem.get('size'),
                                                              device_status="Online", assets=assets
                                                              )
                                    recordAssets.delay(user=str(request.user),
                                                       content="修改服务器资产：{ip}".format(ip=server_assets.ip),
                                                       type="server", id=server_assets.id)
                                except Exception, e:
                                    return JsonResponse({'msg': "数据更新失败-写入数据失败", "code": 400})
                    if ds.get('disk_info'):
                        for disk in ds.get('disk_info'):
                            if Disk_Assets.objects.filter(assets=assets, device_slot=disk.get('slot')).count() > 0:
                                try:
                                    Disk_Assets.objects.filter(assets=assets, device_slot=disk.get('slot')).update(
                                        device_serial=disk.get('serial'), device_model=disk.get('model'),
                                        device_brand=disk.get('manufacturer'), device_volume=disk.get('size'),
                                        device_status="Online"
                                    )

                                except Exception, e:
                                    return JsonResponse({'msg': "数据更新失败-写入数据失败", "code": 400})
                            else:
                                try:
                                    Disk_Assets.objects.create(device_serial=disk.get('serial'),
                                                               device_model=disk.get('model'),
                                                               device_brand=disk.get('manufacturer'),
                                                               device_volume=disk.get('size'),
                                                               device_status="Online", assets=assets,
                                                               device_slot=disk.get('slot')
                                                               )
                                    recordAssets.delay(user=str(request.user),
                                                       content="修改服务器资产：{ip}".format(ip=server_assets.ip),
                                                       type="server", id=server_assets.id)
                                except Exception, e:
                                    return JsonResponse({'msg': "数据更新失败-写入数据失败", "code": 400})

                return JsonResponse({'msg': "数据更新成功", "code": 200})
            else:
                return JsonResponse({'msg': "数据更新失败，系统可能不支持，未能获取数据", "code": 400})

    else:
        return JsonResponse({'msg': "您没有该项操作的权限~", "code": 400})


@login_required(login_url='/login')
@permission_required('OpsManage.can_change_server_assets', login_url='/noperm/')
def assets_import(request):
    if request.method == "POST":
        f = request.FILES.get('import_file')
        filename = os.path.join(os.getcwd() + '/upload/', f.name)
        if os.path.isdir(os.path.dirname(filename)) is not True: os.makedirs(os.path.dirname(filename))
        fobj = open(filename, 'wb')
        for chrunk in f.chunks():
            fobj.write(chrunk)
        fobj.close()

        # 读取上传的execl文件内容方法
        def getAssetsData(fname=filename):
            bk = xlrd.open_workbook(fname)
            dataList = []
            try:
                server = bk.sheet_by_name("server")
                net = bk.sheet_by_name("net")
                for i in range(1, server.nrows):
                    dataList.append(server.row_values(i))
                for i in range(1, net.nrows):
                    dataList.append(net.row_values(i))
            except Exception, e:
                return []
            return dataList

        # 录入信息时增加基础数据表信息
        def checkInsertItems(assets):
            resultStr = '设备[%s]插入出现如下错误，请配置基础数据表：' % assets.get('name')
            errFlag = False
            # 检查确认相关item已经被录入到对应的基础数据配置表里
            # tableInsertList = ['assets_class', 'assets_type', 'put_zone', 'contract',
            #                    'provider', 'maintenance', 'status', 'monitor_status',
            #                    'group', 'business', 'project']
            assetClass = assets.get('assets_class')
            assetType = assets.get('assets_type')
            putZone = assets.get('put_zone')
            manufacturer = assets.get('manufacturer')
            provider = assets.get('provider')
            status = assets.get('status')
            monitorStatus = assets.get('monitor_status')
            group = assets.get('group')
            business = assets.get('business')
            project = assets.get('project')
            contract = assets.get('contract')
            maintenance = assets.get('maintenance')
            if not Type_Assets.objects.get(assets_type=assetClass).count():
                resultStr += '设备类别【%s】不存在；' % assetClass
                errFlag = True
            if not Type_Assets.objects.get(assets_type=assetType).count():
                resultStr += '设备类型【%s】不存在；' % assetType
                errFlag = True
            if not Zone_Assets.objects.get(zone_name=putZone).count():
                resultStr += '机房名【%s】不存在；' % putZone
                errFlag = True
            if not Provider_Assets.objects.get(provider_name=manufacturer).count():
                resultStr += '制造商【%s】不存在；' % manufacturer
                errFlag = True
            if not Provider_Assets.objects.get(provider_name=provider).count():
                resultStr += '维保服务商【%s】不存在；' % provider
                errFlag = True
            if not Status_Assets.objects.get(status_name=status).count():
                resultStr += '设备状态【%s】不存在；' % status
                errFlag = True
            if not Monitor_Assets.objects.get(monitor_name=monitorStatus).count():
                resultStr += '监控状态【%s】不存在；' % monitorStatus
                errFlag = True
            if not Group.objects.get(name=group).count():
                resultStr += '使用部门名【%s】不存在；' % group
                errFlag = True
            if not Project_Assets.objects.get(project_name=project).count():
                resultStr += '业务系统【%s】不存在；' % project
                errFlag = True
            if not Service_Assets.objects.get(service_name=business).count():
                resultStr += '业务项目【%s】不存在；' % business
                errFlag = True
            if not Contract_Assets.objects.get(contract_name=contract).count():
                resultStr += '资产合同【%s】不存在；' % contract
                errFlag = True
            if not Maintenance_Assets.objects.get(maintenance_name=maintenance).count():
                resultStr += '维保合同【%s】不存在；' % maintenance
                errFlag = True

        dataList = getAssetsData(fname=filename)
        # 获取服务器列表
        for data in dataList:
            assets = {
                'assets_class': data[0],
                'assets_type': data[1],
                'name': data[2],
                'put_zone': data[3],
                'put_rack': data[4],
                'model': data[5],
                'sn': data[6],
                'management_ip': data[7],
                'manufacturer': data[8],
                'contract': data[10],
                'provider': data[11],
                'service_contact': data[12],
                'service_level': data[13],
                'maintenance': data[15],
                'buy_user': data[17],
                'status': data[18],
                'monitor_status': data[19],
                'group': data[20],
                'business': data[21],
                'project': data[22],
            }
            if data[9]: assets['enter_time'] = xlrd.xldate.xldate_as_datetime(data[9], 0)
            if data[14]: assets['service_start'] = xlrd.xldate.xldate_as_datetime(data[14], 0)
            if data[16]: assets['expire_date'] = xlrd.xldate.xldate_as_datetime(data[16], 0)
            if assets.get('assets_class') in ['vmser', 'server']:
                server_assets = {
                    'ip': data[23],
                    'keyfile': data[24],
                    'username': data[25],
                    'passwd': data[26],
                    'hostname': data[27],
                    'port': data[28],
                    'raid': data[29],
                    'line': data[30],
                }
            else:
                net_assets = {
                    'ip': data[23],
                    'bandwidth': data[24],
                    'port_detail': data[25],
                    'ios_version': data[26],
                    'models_sn': data[27],
                    'asset_level': data[28],
                    'cpu': data[29],
                    'stone': data[30],
                    'configure_detail': data[31]
                }
            count = Assets.objects.filter(name=assets.get('name')).count()
            if count == 1:  # 如果资产列表里有该设备，则更新设备信息
                assetsObj = Assets.objects.get(name=assets.get('name'))
                Assets.objects.filter(name=assets.get('name')).update(**assets)
                try:
                    if assets.get('assets_class') in ['vmser', 'server']:
                        Server_Assets.objects.filter(assets=assetsObj).update(**server_assets)
                    elif assets.get('assets_class') in ['network', 'security', 'storage', 'office']:
                        Network_Assets.objects.filter(assets=assetsObj).update(**net_assets)
                except  Exception, ex:
                    print ex
            else:  # 资产列表里没有该设备名，则新增设备

                try:
                    assetsObj = Assets.objects.create(**assets)
                except Exception, ex:
                    logger.warn(msg="批量写入资产失败: {ex}".format(ex=str(ex)))
                if assetsObj:

                    try:
                        if assets.get('assets_class') in ['vmser', 'server']:
                            Server_Assets.objects.create(assets=assetsObj, **server_assets)
                        elif assets.get('assets_class') in ['network', 'security', 'storage', 'office']:
                            Network_Assets.objects.create(assets=assetsObj, **net_assets)
                    except Exception, ex:
                        logger.warn(msg="批量更新资产失败: {ex}".format(ex=str(ex)))
                        assetsObj.delete()
        return HttpResponseRedirect('/assets_list')


@login_required(login_url='/login')
@permission_required('OpsManage.can_read_assets', login_url='/noperm/')
def assets_search(request):
    AssetFieldsList = [n.name for n in Assets._meta.fields]
    ServerAssetFieldsList = [n.name for n in Server_Assets._meta.fields]
    if request.method == "GET":
        manufacturerList = [m.manufacturer for m in Assets.objects.raw(
            'SELECT id,manufacturer from opsmanage_assets WHERE  manufacturer is not null GROUP BY manufacturer')]
        modelList = [m.model for m in Assets.objects.raw(
            'SELECT id,model from opsmanage_assets WHERE model is not null  GROUP BY model')]
        providerList = [m.provider for m in Assets.objects.raw(
            'SELECT id,provider from opsmanage_assets WHERE provider is not null GROUP BY provider')]
        cpuList = [a.cpu for a in
                   Assets.objects.raw('SELECT id,cpu from opsmanage_server_assets WHERE cpu is not null GROUP BY cpu')]
        buyUserList = User.objects.all()
        selinuxList = [m.selinux for m in Assets.objects.raw(
            'SELECT id,selinux from opsmanage_server_assets WHERE selinux is not null GROUP BY selinux')]
        systemList = [m.system for m in Assets.objects.raw(
            'SELECT id,system from opsmanage_server_assets WHERE system is not null GROUP BY system')]
        kernelList = [m.kernel for m in Assets.objects.raw(
            'SELECT id,kernel from opsmanage_server_assets WHERE kernel is not null GROUP BY kernel')]
        return render(request, 'assets/assets_search.html', {"user": request.user, "baseAssets": getBaseAssets(),
                                                             "manufacturerList": manufacturerList,
                                                             "modelList": modelList,
                                                             "providerList": providerList, "cpuList": cpuList,
                                                             "buyUserList": buyUserList, "selinuxList": selinuxList,
                                                             "systemList": systemList, 'kernelList': kernelList,
                                                             },
                      )
    elif request.method == "POST":
        AssetIntersection = list(set(request.POST.keys()).intersection(set(AssetFieldsList)))
        ServerAssetIntersection = list(set(request.POST.keys()).intersection(set(ServerAssetFieldsList)))
        assetsList = []
        data = dict()
        # 格式化查询条件
        for (k, v) in request.POST.items():
            if v is not None and v != u'':
                data[k] = v
        if list(set(['enter_time', 'expire_date', 'vcpu_number',
                     'cpu_core', 'cpu_number', 'ram_total',
                     'swap', 'disk_total']).intersection(set(request.POST.keys()))):
            try:
                enter_time = request.POST.get('enter_time').split('-')
                data.pop('enter_time')
                data['enter_time__gte'] = enter_time[0] + '-01-01'
                data['enter_time__lte'] = enter_time[1] + '-01-01'
            except:
                pass
            try:
                expire_date = request.POST.get('expire_date').split('-')
                data.pop('expire_date')
                data['expire_date__gte'] = expire_date[0] + '-01-01'
                data['expire_date__lte'] = expire_date[1] + '-01-01'
            except:
                pass
            try:
                vcpu_number = request.POST.get('vcpu_number').split('-')
                data.pop('vcpu_number')
                data['vcpu_number__gte'] = int(vcpu_number[0])
                data['vcpu_number__lte'] = int(vcpu_number[1])
            except:
                pass
            try:
                cpu_number = request.POST.get('cpu_number').split('-')
                data.pop('cpu_number')
                data['cpu_number__gte'] = int(cpu_number[0])
                data['cpu_number__lte'] = int(cpu_number[1])
            except:
                pass
            try:
                cpu_core = request.POST.get('cpu_core').split('-')
                data.pop('cpu_core')
                data['cpu_core__gte'] = int(cpu_core[0])
                data['cpu_core__lte'] = int(cpu_core[1])
            except:
                pass
            try:
                swap = request.POST.get('swap').split('-')
                data.pop('swap')
                data['swap__gte'] = int(swap[0])
                data['swap__lte'] = int(swap[1])
            except:
                pass
            try:
                disk_total = request.POST.get('disk_total').split('-')
                data.pop('disk_total')
                data['disk_total__gte'] = int(disk_total[0]) * 1024
                data['disk_total__lte'] = int(disk_total[1]) * 1024
            except:
                pass
            try:
                ram_total = request.POST.get('ram_total').split('-')
                data.pop('ram_total')
                data['ram_total__gte'] = int(ram_total[0])
                data['ram_total__lte'] = int(ram_total[1])
            except:
                pass

        if data.has_key('ip'): # 不能按实际录入的ip地址查找 hyphen.liu
            for ds in NetworkCard_Assets.objects.filter(ip=data.get('ip')):
                if ds.assets not in assetsList: assetsList.append(ds.assets)

        else:
            if len(AssetIntersection) > 0 and len(ServerAssetIntersection) > 0:
                assetsData = dict()
                for a in AssetIntersection:
                    for k in data.keys():
                        if k.find(a) != -1:
                            assetsData[k] = data[k]
                            data.pop(k)
                serverList = [a.assets_id for a in Server_Assets.objects.filter(**data)]
                assetsData['id__in'] = serverList
                assetsList.extend(Assets.objects.filter(**assetsData))

            elif len(AssetIntersection) > 0 and len(ServerAssetIntersection) == 0:
                assetsList.extend(Assets.objects.filter(**data))

            elif len(AssetIntersection) == 0 and len(ServerAssetIntersection) > 0:
                for ds in Server_Assets.objects.filter(**data):
                    if ds.assets not in assetsList: assetsList.append(ds.assets)

        baseAssets = getBaseAssets()
        dataList = []
        for a in assetsList:
            nks = ''
            if a.management_ip:
                liTags = ''
                for ns in a.networkcard_assets_set.all():
                    if ns.ip != 'unkown' and ns.ip != a.management_ip:
                        liTag = '''<li><span class="label label-success">内</span>:<code>{address}</code></li>'''.format(
                            address=ns.ip)
                        liTags = liTags + liTag
                nks = '''<ul class="list-unstyled">
                            <li><span class="label label-danger">外</span>:<code>{management_ip}</code></li>
                            {liTags}
                        </ul>'''.format(management_ip=a.management_ip, liTags=liTags)
            elif a.server_assets.ip:
                liTags = ''
                for ns in a.networkcard_assets_set.all():
                    if ns.ip != 'unkown' and ns.ip != a.server_assets.ip:
                        liTag = '''<li><span class="label label-success">内</span>:<code>{address}</code></li>'''.format(
                            address=ns.ip)
                        liTags = liTags + liTag
                nks = '''<ul class="list-unstyled">
                            <li><span class="label label-danger">外</span>:<code>{server_ip}</code></li>
                            {liTags}
                        </ul>'''.format(server_ip=a.server_assets.ip, liTags=liTags)
            management_ip = '''{ip}'''.format(ip=nks)
            name = '''{name}'''.format(name=a.name)
            model = '''{model}'''.format(model=a.model)
            for p in baseAssets.get('project'):
                if p.project_name == a.project:
                    project = '''{project}'''.format(project=p.project_name)
                    break
                else:
                    project = '''[{project}]<li><code>不在</code></li>基础配置表[业务系统]里'''.format(project=a.project)
            for s in baseAssets.get('service'):
                if s.service_name == a.business:
                    service = '''{service}'''.format(service=s.service_name)
                    break
                else:
                    service = '''[{service}]<li><code>不在</code></li>基础配置表[业务项目]里'''.format(service=a.business)
            status = '''<button type="button" class="btn btn-outline btn-default">{status}</button>'''.format(
                status=a.status)
            if a.enter_time:
                enter_time = '''{enter_time}'''.format(enter_time=a.enter_time)
            else:
                enter_time = '''{enter_time}'''.format(enter_time=str(a.create_date)[0:10])
            group = '''{groupname}'''.format(groupname=a.group)
            for z in baseAssets.get('zone'):
                if z.zone_name == a.put_zone:
                    put_zone = '''{zone_name}'''.format(zone_name=z.zone_name)
                    break
                else:
                    put_zone = '''[{zone_name}]<li><code>不在</code></li>基础配置表[机房位置]里'''.format(zone_name=a.put_zone)
            try:
                if a.assets_class in ["server", "vmser"]:
                    assets_type_div = '''
                                        <div class="btn-group">                
                                           <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
                                                  <font class="glyphicon glyphicon-refresh"></font>
                                               <span class="caret"></span>
                                           </button>                                                                                            
                                             <ul class="dropdown-menu" role="menu">
                                                  <li>
                                                      <a href="javascript:" onclick='assetsUpdate(this,{server_assets_id},"{server_assets_ip}","setup")'>更新主体信息</a>
                                                  </li>        
                                                  <li>
                                                      <a href="javascript:" onclick='assetsUpdate(this,{server_assets_id},"{server_assets_ip}","crawHw")'>更新内存硬盘</a>
                                                  </li>                                         
                                             </ul>
                                        </div>'''.format(server_assets_id=a.server_assets.id,
                                                         server_assets_ip=a.server_assets.ip)
                else:
                    assets_type_div = ''' <div class="btn-group">                
                           <button type="button" class="btn btn-default  disabled">
                                  <font class="glyphicon glyphicon-refresh"></font>
                               </span>
                           </button>                                                                                            
                        </div>'''
            except:
                pass
            opt = '''                
                     <a href="/assets_view/{id}" style="text-decoration:none;"><button  type="button" class="btn btn-default"><abbr title="查看详细信息"><i class="glyphicon glyphicon-info-sign"></i></abbr></button></a>
                     {assets_type_div}
                     <a href="/assets_mod/{id}" style="text-decoration:none;"><button  type="button" class="btn btn-default"><abbr title="修改资料"><i class="glyphicon glyphicon-edit"></button></i></abbr></a>
                     <button  type="button" class="btn btn-default" onclick="deleteAssets(this,{id})"><i class="glyphicon glyphicon-trash"></i></button>
                 '''.format(id=a.id, assets_type_div=assets_type_div)
            dataList.append(
                {"详情": '',
                 '全选': '<input type="checkbox" value="{id}" name="ckbox"/>'.format(id=a.id),
                 '资产ID': a.id,
                 '资产类型': a.assets_type,
                 '管理IP': management_ip,
                 '资产编号': name,
                 '设备型号': model,
                 '机房位置': put_zone,
                 '业务系统': project,
                 '业务类型': service,
                 '使用部门': group,
                 '设备状态': status,
                 '操作': opt}
            )
        return JsonResponse({'msg': "数据查询成功", "code": 200, 'data': dataList, 'count': 0})


@login_required(login_url='/login')
def assets_log(request, page):
    if request.method == "GET":
        allAssetsList = Log_Assets.objects.all().order_by('-id')[0:1000]
        paginator = Paginator(allAssetsList, 25)
        try:
            assetsList = paginator.page(page)
        except PageNotAnInteger:
            assetsList = paginator.page(1)
        except EmptyPage:
            assetsList = paginator.page(paginator.num_pages)
        return render(request, 'assets/assets_log.html', {"user": request.user, "assetsList": assetsList})


@login_required(login_url='/login')
@permission_required('OpsManage.can_change_assets', login_url='/noperm/')
def assets_update(request):
    if request.method == "POST":
        fList = []
        sList = []
        resource = []
        serList = []
        #         if request.POST.get('model') == 'update':
        for ast in request.POST.getlist('assetsIds[]'):
            try:
                assets = Assets.objects.get(id=int(ast))
            except Exception, ex:
                logger.warn(msg="批量更新获取资产失败: {ex}".format(ex=str(ex)))
                continue
            if assets.assets_class in ['vmser', 'server']:
                try:
                    server_assets = Server_Assets.objects.get(assets=assets)
                except Exception, ex:
                    logger.warn(msg="批量更新获取服务器资产失败: {ex}".format(ex=str(ex)))
                    if server_assets.ip not in fList: fList.append(server_assets.ip)
                    continue
                serList.append(server_assets.ip)
                if server_assets.keyfile == 1:
                    resource.append(
                        {"ip": server_assets.ip, "port": int(server_assets.port), "username": server_assets.username,
                         "sudo_passwd": server_assets.sudo_passwd})
                else:
                    resource.append(
                        {"ip": server_assets.ip, "port": int(server_assets.port), "username": server_assets.username,
                         "password": server_assets.passwd, "sudo_passwd": server_assets.sudo_passwd})
        ANS = ANSRunner(resource)
        ANS.run_model(host_list=serList, module_name='setup', module_args="")
        data = ANS.handle_cmdb_data(ANS.get_model_result())
        if data:
            for ds in data:
                status = ds.get('status')
                sip = ds.get('ip')
                if status == 0:
                    assets = Server_Assets.objects.get(ip=ds.get('ip')).assets
                    assets.model = ds.get('model')
                    assets.save()
                    try:
                        Server_Assets.objects.filter(ip=ds.get('ip')).update(cpu_number=ds.get('cpu_number'),
                                                                             kernel=ds.get('kernel'),
                                                                             selinux=ds.get('selinux'),
                                                                             hostname=ds.get('hostname'),
                                                                             system=ds.get('system'), cpu=ds.get('cpu'),
                                                                             disk_total=ds.get('disk_total'),
                                                                             cpu_core=ds.get('cpu_core'),
                                                                             swap=ds.get('swap'),
                                                                             ram_total=ds.get('ram_total'),
                                                                             vcpu_number=ds.get('vcpu_number')
                                                                             )
                        if sip not in sList: sList.append(sip)
                    except Exception:
                        if sip not in fList: fList.append(sip)
                    for nk in ds.get('nks'):
                        macaddress = nk.get('macaddress')
                        count = NetworkCard_Assets.objects.filter(assets=assets, macaddress=macaddress).count()
                        if count > 0:
                            try:
                                NetworkCard_Assets.objects.filter(assets=assets, macaddress=macaddress).update(
                                    assets=assets, device=nk.get('device'),
                                    ip=nk.get('address'), module=nk.get('module'),
                                    mtu=nk.get('mtu'), active=nk.get('active'))
                            except Exception, ex:
                                logger.warn(msg="批量更新更新服务器网卡资产失败: {ex}".format(ex=str(ex)))
                        else:
                            try:
                                NetworkCard_Assets.objects.create(assets=assets, device=nk.get('device'),
                                                                  macaddress=nk.get('macaddress'),
                                                                  ip=nk.get('address'), module=nk.get('module'),
                                                                  mtu=nk.get('mtu'), active=nk.get('active'))
                            except Exception, ex:
                                logger.warn(msg="批量更新写入服务器网卡资产失败: {ex}".format(ex=str(ex)))
                else:
                    if sip not in fList: fList.append(sip)
        if sList:
            return JsonResponse({'msg': "数据更新成功", "code": 200, 'data': {"success": sList, "failed": fList}})
        else:
            return JsonResponse({'msg': "数据更新失败", "code": 500, 'data': {"success": sList, "failed": fList}})


@login_required(login_url='/login')
@permission_required('OpsManage.can_delete_assets', login_url='/noperm/')
def assets_delete(request):
    if request.method == "POST":
        fList = []
        sList = []
        for ast in request.POST.getlist('assetsIds[]'):
            try:
                assets = Assets.objects.get(id=int(ast))
            except Exception, ex:
                logger.error(msg="删除资产失败: {ex}".format(ex=ex))
                continue
            if assets.assets_class in ['vmser', 'server']:
                try:
                    server_assets = Server_Assets.objects.get(assets=assets)
                except Exception, ex:
                    fList.append(assets.management_ip)
                    assets.delete()
                    continue
                sList.append(server_assets.ip)
                server_assets.delete()
            else:
                try:
                    net_assets = Network_Assets.objects.get(assets=assets)
                except Exception, ex:
                    fList.append(assets.management_ip)
                    assets.delete()
                    continue
                sList.append(assets.management_ip)
                net_assets.delete()
            assets.delete()
        return JsonResponse({'msg': "数据删除成功", "code": 200, 'data': {"success": sList, "failed": fList}})


@login_required(login_url='/login')
@permission_required('OpsManage.can_dumps_assets', login_url='/noperm/')
def assets_dumps(request):
    if request.method == "POST":
        dateStr = datetime.datetime.now().strftime('%Y%m%d')
        filename = 'assets_dumps-' + dateStr + '.xls'
        dRbt = CellWriter(filename)
        serSheet = dRbt.workbook.add_sheet('服务器设备资产', cell_overwrite_ok=True)
        netSheet = dRbt.workbook.add_sheet('网络设备资产', cell_overwrite_ok=True)
        bList = ['设备类型', '资产编号', '机房位置', '机架位置', '设备型号', '设备序列号', '管理IP', '制造商', '入网时间', '资产合同',
                 '维保服务商', '维保联系人', '维保服务级别', '维保开始时间', '维保合同', '过保时间', '资产归属人', '设备状态',
                 '监控状态', '使用部门', '所属业务系统', '所属业务项目', '主机地址', '认证方式', '账户', '主机名字', '端口', 'CPU型号',
                 'Raid类型', '物理CPU', '逻辑CPU', 'CPU核心数', '内存容量', '内核版本', 'Selinux状态', 'Swap分区', '磁盘空间',
                 '系统版本号', '机房线路']
        nList = ['设备类型', '资产编号', '机房位置', '机架位置', '设备型号', '设备序列号', '管理IP', '制造商', '入网时间', '资产合同',
                 '维保服务商', '维保联系人', '维保服务级别', '维保开始时间', '维保合同', '过保时间', '资产归属人', '设备状态',
                 '监控状态', '使用部门', '所属业务系统', '所属业务项目', '主机地址', '背板带宽', '端口情况', '操作系统版本', '模块序列号',
                 '设备级别', 'CPU型号', '内存容量', '配置说明', '管理用户', '端口']
        dRbt.writeBanner(sheetName=serSheet, bList=bList)
        dRbt.writeBanner(sheetName=netSheet, bList=nList)
        ncount = 0
        scount = 0
        count = 0
        for ast in request.POST.get('assetsIds').split(','):
            try:
                assets = Assets.objects.select_related().get(id=int(ast))
            except Exception, ex:
                logger.warn(msg=ex)
                continue
            if assets.assets_class in ['vmser', 'server']:
                sheet = serSheet
                scount += 1
                count = scount
                sheet.write(scount, 22, assets.server_assets.ip, dRbt.bodySttle())
                sheet.write(scount, 23, assets.server_assets.keyfile, dRbt.bodySttle())
                sheet.write(scount, 24, assets.server_assets.username, dRbt.bodySttle())
                sheet.write(scount, 25, assets.server_assets.hostname, dRbt.bodySttle())
                sheet.write(scount, 26, assets.server_assets.port, dRbt.bodySttle())
                sheet.write(scount, 27, assets.server_assets.cpu, dRbt.bodySttle())
                sheet.write(scount, 28, assets.server_assets.raid, dRbt.bodySttle())
                sheet.write(scount, 29, assets.server_assets.cpu_number, dRbt.bodySttle())
                sheet.write(scount, 30, assets.server_assets.vcpu_number, dRbt.bodySttle())
                sheet.write(scount, 31, assets.server_assets.cpu_core, dRbt.bodySttle())
                sheet.write(scount, 32, assets.server_assets.ram_total, dRbt.bodySttle())
                sheet.write(scount, 33, assets.server_assets.kernel, dRbt.bodySttle())
                sheet.write(scount, 34, assets.server_assets.selinux, dRbt.bodySttle())
                sheet.write(scount, 35, assets.server_assets.swap, dRbt.bodySttle())
                sheet.write(scount, 36, assets.server_assets.disk_total, dRbt.bodySttle())
                sheet.write(scount, 37, assets.server_assets.system, dRbt.bodySttle())
                sheet.write(scount, 38, assets.server_assets.line, dRbt.bodySttle())
            else:
                sheet = netSheet
                ncount += 1
                count = ncount
                sheet.write(ncount, 22, assets.network_assets.ip, dRbt.bodySttle())
                sheet.write(ncount, 23, assets.network_assets.bandwidth, dRbt.bodySttle())
                sheet.write(ncount, 24, assets.network_assets.port_detail, dRbt.bodySttle())
                sheet.write(ncount, 25, assets.network_assets.ios_version, dRbt.bodySttle())
                sheet.write(ncount, 26, assets.network_assets.models_sn, dRbt.bodySttle())
                sheet.write(ncount, 27, assets.network_assets.asset_level, dRbt.bodySttle())
                sheet.write(ncount, 28, assets.network_assets.cpu, dRbt.bodySttle())
                sheet.write(ncount, 29, assets.network_assets.stone, dRbt.bodySttle())
                sheet.write(ncount, 30, assets.network_assets.configure_detail, dRbt.bodySttle())
                sheet.write(ncount, 31, assets.network_assets.username, dRbt.bodySttle())
                sheet.write(ncount, 32, assets.network_assets.port, dRbt.bodySttle())
            sheet.write(count, 0, assets.assets_type, dRbt.bodySttle())
            sheet.write(count, 1, assets.name, dRbt.bodySttle())
            sheet.write(count, 2, assets.put_zone, dRbt.bodySttle())
            sheet.write(count, 3, assets.put_rack, dRbt.bodySttle())
            sheet.write(count, 4, assets.model, dRbt.bodySttle())
            sheet.write(count, 5, assets.sn, dRbt.bodySttle())
            sheet.write(count, 6, assets.management_ip, dRbt.bodySttle())
            sheet.write(count, 7, assets.manufacturer, dRbt.bodySttle())
            sheet.write(count, 8, str(assets.enter_time), dRbt.bodySttle())
            sheet.write(count, 9, assets.contract, dRbt.bodySttle())
            sheet.write(count, 10, assets.provider, dRbt.bodySttle())
            sheet.write(count, 11, assets.service_contact, dRbt.bodySttle())
            sheet.write(count, 12, assets.service_level, dRbt.bodySttle())
            sheet.write(count, 13, str(assets.service_start), dRbt.bodySttle())
            sheet.write(count, 14, assets.maintenance, dRbt.bodySttle())
            sheet.write(count, 15, str(assets.expire_date), dRbt.bodySttle())
            sheet.write(count, 16, assets.buy_user, dRbt.bodySttle())
            sheet.write(count, 17, assets.status, dRbt.bodySttle())
            sheet.write(count, 18, assets.monitor_status, dRbt.bodySttle())
            sheet.write(count, 19, assets.group, dRbt.bodySttle())
            sheet.write(count, 20, assets.project, dRbt.bodySttle())
            sheet.write(count, 21, assets.business, dRbt.bodySttle())
        dRbt.save()
        response = StreamingHttpResponse(base.file_iterator(filename))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment; filename={file_name}'.format(file_name=filename)
        return response


@login_required(login_url='/login')
@permission_required('OpsManage.can_read_assets', login_url='/noperm/')
def assets_server(request):
    if request.method == "POST":
        if request.POST.get('query') in ['service', 'project', 'group']:
            dataList = []
            if request.POST.get('query') == 'service':
                for ser in Assets.objects.filter(
                        business=request.POST.get('id')):  # ,assets_type__in=['server','vmser','switch','route']):
                    try:
                        project = Project_Assets.objects.get(id=ser.project).project_name
                    except Exception, ex:
                        project = '未知'
                        logger.warn(msg="查询主机业务系统信息失败: {ex}".format(ex=str(ex)))
                    try:
                        service = Service_Assets.objects.get(id=ser.business).service_name
                    except Exception, ex:
                        service = '未知'
                        logger.warn(msg="查询主机业务项目失败: {ex}".format(ex=str(ex)))
                    if ser.assets_class in ['server', 'vmser']:
                        dataList.append({"id": ser.server_assets.id, "ip": ser.server_assets.ip, "project": project,
                                         "service": service})
                    elif ser.assets_class in ['switch', 'route']:  # 需要修改
                        dataList.append({"id": ser.network_assets.id, "ip": ser.network_assets.ip, "project": project,
                                         "service": service})
            elif request.POST.get('query') == 'group':
                for ser in Assets.objects.filter(
                        group=request.POST.get('id')):  # assets_class__in=['server','vmser','switch','route']):
                    try:
                        project = Project_Assets.objects.get(id=ser.project).project_name
                    except Exception, ex:
                        project = '未知'
                        logger.warn(msg="查询主机业务系统信息失败: {ex}".format(ex=str(ex)))
                    try:
                        service = Service_Assets.objects.get(id=ser.business).service_name
                    except Exception, ex:
                        service = '未知'
                        logger.warn(msg="查询主机业务项目失败: {ex}".format(ex=str(ex)))
                    if ser.assets_class in ['server', 'vmser']:
                        dataList.append({"id": ser.server_assets.id, "ip": ser.server_assets.ip, "project": project,
                                         "service": service})
                    elif ser.assets_class in ['switch', 'route']:  # 需要修改
                        dataList.append({"id": ser.network_assets.id, "ip": ser.network_assets.ip, "project": project,
                                         "service": service})
            return JsonResponse({'msg': "主机查询成功", "code": 200, 'data': dataList})
        else:
            JsonResponse({'msg': "不支持的操作", "code": 500, 'data': []})
    else:
        return JsonResponse({'msg': "操作失败", "code": 500, 'data': "不支持的操作"})


@login_required(login_url='/login')
@permission_required('OpsManage.can_read_assets', login_url='/noperm/')
def assets_groups(request, id):
    try:
        project = Project_Assets.objects.get(id=id)
    except Project_Assets.DoesNotExist:
        return render(request, 'assets/assets_groups.html', {"user": request.user, "errorInfo": "业务系统不存在"})
    serviceList = Service_Assets.objects.filter(project=project)
    for ds in serviceList:
        dataList = []
        for ser in Assets.objects.select_related().filter(business=ds.id):
            if hasattr(ser, 'server_assets'):
                if ser.server_assets.ram_total:
                    ser.server_assets.ram_total = str(int(ser.server_assets.ram_total) / 1024) + 'GB'
                else:
                    ser.server_assets.ram_total = '0GB'
                if ser.server_assets.disk_total:
                    disk_total = int(ser.server_assets.disk_total) / 1024 / 1024
                    if disk_total > 1:
                        ser.server_assets.disk_total = str(int(ser.server_assets.disk_total) / 1024 / 1024) + 'TB'
                    else:
                        ser.server_assets.disk_total = str(int(ser.server_assets.disk_total) / 1024) + 'GB'
                else:
                    ser.server_assets.disk_total = '0GB'
            dataList.append(ser)
            ds.host = dataList
    totalServer = Assets.objects.filter(project=id).count()
    return render(request, 'assets/assets_groups.html', {"user": request.user, "project": project,
                                                         "serviceList": serviceList, "totalServer": totalServer})
