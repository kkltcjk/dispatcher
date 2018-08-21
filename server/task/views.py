import json
import os
import shutil
import subprocess

import requests
from django.http import HttpResponse
from face.common import utils
from face.common import constants as consts
from face.prepare.train import TrainPrepareV1

from task.models import Task

index = 0

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
    _remount(conf)
    _cut(conf, paths)

        
    resp = {'code': 0, 'msg': 'SUCCESS'}
    return HttpResponse(json.dumps(resp))


def update(request):
    # import pdb;pdb.set_trace()
    body = json.loads(request.body)

    try:
        path = body['path']
    except KeyError:
        resp = {'code': 1, 'msg': 'missing path args'}
        return HttpResponse(json.dumps(resp))

    ttype = body.get('type', 'cut')

    if ttype == 'cut':

        name = os.path.dirname(path)
        ipc = os.path.basename(path)

        _update_detail(name, ipc, 'status', 'finished')

        task = Task.objects.get(name=name)
        detail = json.loads(task.detail) if task.detail else {}

        if all([detail[k]['status'] == 'finished' for k in detail]):
            shutil.rmtree(name)
            _update_attr(name, 'procedure', 'clusting')
            _cluster(name)
    else:
        _update_attr(path, 'procedure', 'cleaning')
        _clean(path)
        
    resp = {'code': 0, 'msg': 'SUCCESS'}
    return HttpResponse(json.dumps(resp))


def tasks(request):
    all_tasks = Task.objects.all()
    data = [{'name': t.name, 'detail': t.detail, 'procedure': t.procedure} for t in all_tasks]
    return HttpResponse(json.dumps(data))


def _clean(path):
    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']

    scenario = os.path.basename(path)

    actual_count = len(os.listdir(os.path.join(conf['output']['path'][int(scenario) % conf['output']['total']], scenario, 'cluster/id_data_result')))
    identity_path = os.path.join(conf['identity_dir'], scenario, 'id_data_cluster')
    total_count = len(os.listdir(identity_path)) / 2

    url = 'http://{}/task/start'.format(conf['server']['clean'])
    data = {'path': path, 'date': '{}_{}_{}'.format(scenario, actual_count, total_count)}
    _send_request(url, data)


def _remount(conf):

    cmd = 'umount {}'.format(conf['mount']['remote'])
    subprocess.call(cmd, shell=True)

    cmd = 'mount -t nfs {} {}'.format(conf['mount']['remote'], conf['mount']['point'])
    subprocess.call(cmd, shell=True)


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

    global index

    workers = conf['server']['workers']
    sub_workers = workers[index % len(workers)]['subs']

    sub_index = 0
    for path in paths:
        _update_attr(path, 'procedure', 'cutting')

        for ddir in os.listdir(path):
            abs_ddir = os.path.join(path, ddir)
            if not os.path.isdir(abs_ddir):
                continue

            sub_idx = sub_index % len(sub_workers)
            _dispatch(sub_workers[sub_idx], abs_ddir)

            _update_detail(path, ddir, 'location', sub_workers[sub_idx])
            _update_detail(path, ddir, 'status', 'cutting')

            sub_index += 1

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
