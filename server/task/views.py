import json
import os

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

    _prepare(conf, paths)
    _cut(conf, paths)

        
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

    _update_detail(name, ipc, 'status', 'finished')

    task = Task.objects.get(name=name)
    detail = json.loads(task.detail) if task.detail else {}

    if all([detail[k]['status'] == 'finished' for k in detail]):
        _update_attr(name, 'procedure', 'cutted')
        _cluster(name)
        
    resp = {'code': 0, 'msg': 'SUCCESS'}
    return HttpResponse(json.dumps(resp))


def tasks(request):
    all_tasks = Task.objects.all()
    data = [{'name': t.name, 'detail': t.detail, 'procedure': t.procedure} for t in all_tasks]
    return HttpResponse(json.dumps(data))


def _cluster(path):
    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']

    url = 'http://{}/cluster/start'.format(conf['server']['cluster'])
    data = {'path': path}
    _send_request(url, data)


def _update_attr(name, key, value):
    try:
        task = Task.objects.get(name=name)
    except Exception:
        task = Task.objects.create(name=name, procedure='preparing')

    setattr(task, key, value)
    task.save()


def _prepare(conf, paths):
    for path in paths:
        try:
            obj = TrainPrepareV1(conf, [path])
            obj.run()
        except Exception as e:
            print(e)
        else:
            _update_attr(path, 'procedure', 'prepared')


def _cut(conf, paths):

    workers = conf['server']['worker']

    index = 0
    for path in paths:
        _update_attr(path, 'procedure', 'cutting')

        for ddir in os.listdir(path):
            abs_ddir = os.path.join(path, ddir)
            if not os.path.isdir(abs_ddir):
                continue

            idx = index % len(workers)
            _dispatch(workers[idx], abs_ddir)

            _update_detail(path, ddir, 'location', workers[idx])
            _update_detail(path, ddir, 'status', 'cutting')

            index += 1


def _update_detail(path, ipc, key, value):
    task = Task.objects.get(name=path)

    detail = json.loads(task.detail) if task.detail else {}
    detail.setdefault(ipc, {})
    detail[ipc][key] = value

    task.detail = json.dumps(detail)
    task.save()


def _dispatch(service, ddir):
    url = 'http://{}/cut/start'.format(service)
    data = {'path': ddir}
    _send_request(url, data)


def _send_request(url, data):
    headers = {'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, data=json.dumps(data), headers=headers)
    except Exception as e:
        print(e)
