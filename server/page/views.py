import os
import json

from django.shortcuts import render
from face.common import utils
from face.common import constants as consts

from task.models import Task

# Create your views here.
def tasks(request):
    conf = utils.parse_ymal(consts.CONFIG_FILE)['train']
    videos = []
    [[videos.append(os.path.join(p, ele)) for ele in os.listdir(p)] for p in conf['video']]

    schedule = [
        {
            'video': v,
            'ticket': 'Ready' if os.path.exists(os.path.join(conf['identity_dir'], os.path.basename(v), 'id_data_ticket')) else 'unReady',
            'identity': 'Ready' if os.path.exists(os.path.join(conf['identity_dir'], os.path.basename(v), 'id_data_cluster')) else 'unReady'
        } for v in videos
    ]

    tasks = Task.objects.all()
    running = [{'name': t.name, 'detail': t.detail, 'procedure': t.procedure} for t in tasks]

    context = {
        'schedule': schedule,
        'running': running
    }

    return render(request, 'tasks.html', context)


def detail(request):
    name = request.GET['name']

    task = Task.objects.get(name=name)
    context = {
        'name': name,
        'detail': json.loads(task.detail) if task.detail else {}
    }

    return render(request, 'detail.html', context)
