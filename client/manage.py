#!/usr/bin/env python
import os
import sys

from utils.pools import gpupool

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "client.settings")

    from django.core.management import execute_from_command_line

    try:
        execute_from_command_line(sys.argv)
    except KeyboardInterrupt:
        gpupool.close()
        gpupool.join()
    else:
        gpupool.close()
        gpupool.join()
