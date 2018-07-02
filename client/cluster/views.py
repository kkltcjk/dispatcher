import json
from multiprocessing import Pool

from django.http import HttpResponse
from face.common import utils
from face.common import constants as consts
from face.cluster.train import TrainClusterV1

pool = Pool(2)

# Create your views here.
def start(request):

    body = json.loads(request.body)

    try:
        path = body['path']
    except KeyError:
        resp = {'code': 1, 'msg': 'path param is None'}
        return HttpResponse(json.dumps(resp))

    conf = utils.parse_ymal(consts.CONFIG_FILE)
    obj = TrainClusterV1(conf, path)
    pool.apply_async(_wrapper, (obj, ))

    resp = {'code': 0, 'msg': 'success'}
    return HttpResponse(json.dumps(resp))


def _wrapper(obj):
    obj.run()
