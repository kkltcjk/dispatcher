import json
import time

import requests
from django.http import HttpResponse
from face.common import utils
from face.common import constants as consts
from face.cut import _wapper
from face.cut.train import TrainIpcV1

from utils.pools import gpupool


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
    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']

    for i in range(4):
        obj = TrainIpcV1(configuration, '')
        gpupool.apply_async(wrapper_mock, (obj, ''), 0)

    obj = TrainIpcV1(conf, path)
    obj.update_gpu(0)
    obj.update_disk(0)
    gpupool.apply_async(wrapper, (obj, path), 0)


def _report_status(path):
    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']
    headers = {'Content-Type': 'application/json'}
    url = 'http://{}/task/update'.format(conf['server']['controller'])
    data = {'path': path}
    resp = requests.post(url, data=json.dumps(data), headers=headers)
