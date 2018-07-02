import json
import time

import requests
from django.http import HttpResponse
from face.common import utils
from face.common import constants as consts
from face.cut import _wapper
from face.cut.train import TrainIpcV1

from utils.pools import gpupool

index = 0


# Create your views here.
def start(request):

    body = json.loads(request.body)

    try:
        path = body['path']
    except KeyError:
        resp = {'code': 1, 'msg': 'path param is None'}
        return HttpResponse(json.dumps(resp))
    
    async_cut(path)

    resp = {'code': 0, 'msg': 'success'}
    return HttpResponse(json.dumps(resp))


def wrapper(obj, path):
    _wapper(obj)
    _report_status(path)


def wrapper_mock(obj, path):
    time.sleep(1)


def async_cut(path):
    global index

    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']

    for i in range(4):
        obj = TrainIpcV1(conf, '')
        gpupool.apply_async(wrapper_mock, (obj, ''), 0)

    gpu_idx = index % conf['cut']['gpu']['total']
    disk_idx = index % conf['cut']['disk']['total']

    obj = TrainIpcV1(conf, path)
    obj.update_gpu(gpu_idx)
    obj.update_disk(disk_idx)
    gpupool.apply_async(wrapper, (obj, path), gpu_idx)


def _report_status(path):
    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']
    headers = {'Content-Type': 'application/json'}
    url = 'http://{}/task/update'.format(conf['server']['controller'])
    data = {'path': path}
    resp = requests.post(url, data=json.dumps(data), headers=headers)
