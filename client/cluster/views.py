import json

from django.http import HttpResponse

# Create your views here.
def start(request):

    body = json.loads(request.body)

    try:
        path = body['path']
    except KeyError:
        resp = {'code': 1, 'msg': 'path param is None'}
        return HttpResponse(json.dumps(resp))

    print(path)

    resp = {'code': 0, 'msg': 'success'}
    return HttpResponse(json.dumps(resp))
