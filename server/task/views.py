import json
import os
import time

import requests
from django.http import HttpResponse
from face.common import utils
from face.common import constants as consts
from face.prepare.train import TrainPrepareV1

from task.models import Task

# Create your views here.
def start(request):
    body = json.loads(request.body)

    try:
        paths = body['paths']
    except KeyError:
        resp = {'code': 1, 'msg': 'missing paths args'}
        return HttpResponse(json.dumps(resp))

    if not isinstance(paths, list):
        resp = {'code': 1, 'msg': 'paths must be list'}
        return HttpResponse(json.dumps(resp))

    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']

    _init_task(paths)
    _prepare(conf, paths)

    # import pdb;pdb.set_trace()
    _init_details(paths)
    _dispatch(conf, paths)
        
    resp = {'code': 0, 'msg': 'SUCCESS'}
    return HttpResponse(json.dumps(resp))


def update(request):
    body = json.loads(request.body)

    try:
        path = body['path']
    except KeyError:
        resp = {'code': 1, 'msg': 'missing path args'}
        return HttpResponse(json.dumps(resp))

    name = os.path.dirname(path)
    ipc = os.path.basename(path)

    task = Task.objects.filter(name=name)[0]
    detail = json.loads(task.detail)
    detail[ipc] = 1
    task.detail = json.dumps(detail)
    task.save()

    if all(detail.values()):
        _cluster(path)
        
    resp = {'code': 0, 'msg': 'SUCCESS'}
    return HttpResponse(json.dumps(resp))


def tasks(request):
    all_tasks = Task.objects.all()
    data = [{'name': t.name, 'detail': t.detail, 'procedure': t.procedure} for t in all_tasks]
    return HttpResponse(json.dumps(data))


def _cluster(path):
    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']

    headers = {'Content-Type': 'application/json'}
    url = 'http://{}/cluster/start'.format(conf['server']['cluster'])
    data = {'path': path}
    try:
        resp = requests.post(url, data=json.dumps(data), headers=headers)
    except Exception as e:
        print(e)
    else:
        pass


def _init_task(paths):
    for path in paths:
        task = Task.objects.create(name=path, procedure=0)


def _update_procedure(name, value):
    task = Task.objects.filter(name=name)[0]
    task.procedure = value
    task.save()


def _update_detail(name, value):
    task = Task.objects.filter(name=name)[0]
    task.detail = value
    task.save()


def _prepare(conf, paths):
    obj = TrainPrepareV1(conf, paths)
    obj.run()

    for path in paths:
        _update_procedure(path, 1)


def _dispatch(conf, paths):

    workers = conf['server']['worker']

    index = 0
    for path in paths:
        _update_procedure(path, 2)
        for ddir in os.listdir(path):
            abs_ddir = os.path.join(path, ddir)
            if not os.path.isdir(abs_ddir):
                continue

            idx = index % len(workers)
            _do_dispatch(workers[idx], abs_ddir)

            index += 1


def _do_dispatch(service, ddir):
    time.sleep(1)
    headers = {'Content-Type': 'application/json'}
    url = 'http://{}/cut/start'.format(service)
    data = {'path': ddir}
    try:
        resp = requests.post(url, data=json.dumps(data), headers=headers)
    except Exception as e:
        print(e)
    else:
        pass


def _init_details(paths):
    for path in paths:
        _init_detail(path)


def _init_detail(path):
    detail = {}
    for ddir in os.listdir(path):
        abs_ddir = os.path.join(path, ddir)
        if os.path.isdir(abs_ddir):
            detail[ddir] = 0
    _update_detail(path, json.dumps(detail))
