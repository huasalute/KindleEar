#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#投递历史页面和维护投递历史

from operator import attrgetter
import datetime, json
from apps.base_handler import *
from apps.db_models import *
from google.appengine.api.datastore_errors import NeedIndexError
from bottle import route, post, request, response

@route("/logs")
def Mylogs():
    user = get_current_user()
    try:
        mylogs = DeliverLog.all().filter("username = ", user.name).order('-time').fetch(limit=10)
    except NeedIndexError: #很多人不会部署，经常出现没有建立索引的情况，干脆碰到这种情况直接消耗CPU时间自己排序得了
        mylogs = sorted(DeliverLog.all().filter("username = ", user.name), key=attrgetter('time'), reverse=True)[:10]

    #其他用户的推送记录
    logs = {}
    if user.name == ADMIN_NAME:
        for u in KeUser.all().filter("name != ", ADMIN_NAME):
            try:
                ul = DeliverLog.all().filter("username = ", u.name).order('-time').fetch(limit=5)
            except NeedIndexError:
                ul = sorted(DeliverLog.all().filter("username = ", user.name), key=attrgetter('time'), reverse=True)[:5]
            if ul:
                logs[u.name] =  ul

    #管理员可以查看所有用户的已推送期号，其他用户只能查看自己的已推送期号
    if user.name == ADMIN_NAME:
        try:
            lastDelivered = LastDelivered.all().order('-datetime').fetch(limit=100)
        except NeedIndexError:
            lastDelivered = sorted(LastDelivered.all().fetch(), key=attrgetter('datetime'), reverse=True)[:100]
    else:
        try:
            lastDelivered = LastDelivered.all().filter('username = ', user.name).order('-datetime').fetch(limit=100)
        except NeedIndexError:
            lastDelivered = sorted(LastDelivered.all().filter('username = ', user.name), key=attrgetter('datetime'), reverse=True)[:100]

    if len(lastDelivered) == 0:
        lastDelivered = None

    return render_page('logs.html', "Logs", current='logs',
        mylogs=mylogs, logs=logs, lastDelivered=lastDelivered)

#每天自动运行的任务，清理过期log
@route("/removelogs")
def RemoveLogs():
    #停止过期用户的推送
    for user in KeUser.all().filter('enable_send = ', True):
        if user.expires and (user.expires < datetime.datetime.utcnow()):
            user.enable_send = False
            user.put()

    #清理30天之前的推送记录
    query = DeliverLog.all()
    query.filter('datetime < ', datetime.datetime.utcnow() - datetime.timedelta(days=30))
    logs = query.fetch(1000)
    cnt = len(logs)
    db.delete(logs)

    #清理过期的已推送期号
    query = LastDelivered.all()
    query.filter('datetime < ', datetime.datetime.utcnow() - datetime.timedelta(days=90))
    logs = query.fetch(1000)
    db.delete(logs)

    return "{} lines delivery log removed.<br />".format(cnt)

#修改/删除已推送期号的AJAX处理函数
@post("/lastdelivered/<mgrType>")
def LastDeliveredAjaxPost(mgrType):
    response.content_type = 'application/json'
    user = get_current_user(forAjax=True)
    mgrType = mgrType.lower()

    if mgrType == 'delete':
        id_ = request.forms.id_
        try:
            id_ = int(id_)
        except:
            return json.dumps({'status': _('The id is invalid!')})

        dbItem = LastDelivered.get_by_id(id_)
        if dbItem:
            dbItem.delete()
            return json.dumps({'status':'ok'})
        else:
            return json.dumps({'status': _('The LastDelivered item(%d) not exist!') % id_})
    elif mgrType == 'change':
        id_ = request.forms.id_
        num = request.forms.num
        try:
            id_ = int(id_)
            num = int(num)
        except:
            return json.dumps({'status': _('The id or num is invalid!')})

        dbItem = LastDelivered.get_by_id(id_)
        if dbItem:
            dbItem.num = num
            dbItem.record = '' #手工修改了期号则清空文字描述
            dbItem.put()
            return json.dumps({'status': 'ok', 'num': num})
        else:
            return json.dumps({'status': _('The LastDelivered item ({}) not exist!').format(id_)})
    else:
        return json.dumps({'status': 'Unknown command: {}'.format(mgrType)})
