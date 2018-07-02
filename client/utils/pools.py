import logging
from multiprocessing import Pool
from multiprocessing import Lock

from face.common import utils
from face.common import constants as consts

LOG = logging.getLogger(__name__)


class GPUPool(object):
    def __init__(self, total, process):

        self.pools = {i: Pool(process) for i in range(total)}
        self.lock = Lock()

        self.tasks = []

    def apply_async(self, target, args, gpu_no):
        with self.lock:
            self.tasks.append(self.pools[gpu_no].apply_async(target, args))

    def get(self):
        for t in self.tasks:
            try:
                LOG.debug(t.get())
            except Exception:
                LOG.exception('Sub cut job: %s failed', t)

    def close(self):
        [p.close() for p in self.pools.values()]

    def join(self):
        try:
            [p.join() for p in self.pools.values()]
        except KeyboardInterrupt:
            [p.terminate() for p in self.pools.values()]
            [p.join() for p in self.pools.values()]


conf = utils.parse_ymal(consts.CONFIG_FILE)['train']
gpupool = GPUPool(conf['cut']['gpu']['total'], conf['cut']['gpu']['process'])
