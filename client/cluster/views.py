import json
from multiprocessing import Pool

import requests
from django.http import HttpResponse
from face.common import utils
from face.common import constants as consts
from face.cluster.train import TrainClusterV1


def _report_status(path):
    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']

    headers = {'Content-Type': 'application/json'}
    url = 'http://{}/task/update'.format(conf['server']['controller'])
    data = {'path': path, 'type': 'cluster'}
    resp = requests.post(url, data=json.dumps(data), headers=headers)


def _wrapper(obj, path):
    obj.run()
    _report_status(path)

pool = Pool(2)

# Create your views here.
def start(request):

    # import pdb;pdb.set_trace()
    body = json.loads(request.body)

    try:
        path = body['path']
    except KeyError:
        resp = {'code': 1, 'msg': 'path param is None'}
        return HttpResponse(json.dumps(resp))

    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']
    obj = TrainClusterV1(conf, path)
    pool.apply_async(_wrapper, (obj, path))

    resp = {'code': 0, 'msg': 'success'}
    return HttpResponse(json.dumps(resp))
