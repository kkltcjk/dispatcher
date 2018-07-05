import json

import requests
from django.http import HttpResponse
from face.common import utils
from face.common import constants as consts
from face.cut import _wapper
from face.cut.train import TrainIpcV1

from utils.pools import GPUPool

index = 0
conf = utils.parse_ymal(consts.CONFIG_FILE)['train']


def _report_status(path):
    headers = {'Content-Type': 'application/json'}
    url = 'http://{}/task/update'.format(conf['server']['controller'])
    data = {'path': path}
    resp = requests.post(url, data=json.dumps(data), headers=headers)


def wrapper(obj, path):
    _wapper(obj)
    _report_status(path)


gpupool = GPUPool(conf['cut']['gpu']['total'], conf['cut']['gpu']['process'])


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


def async_cut(path):
    global index

    gpu_idx = index % conf['cut']['gpu']['total']
    disk_idx = index % conf['cut']['disk']['total']

    obj = TrainIpcV1(conf, path)
    obj.update_gpu(gpu_idx)
    obj.update_disk(disk_idx)
    gpupool.apply_async(wrapper, (obj, path), gpu_idx)

    index += 1
