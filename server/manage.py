#!/usr/bin/env python
import os
import sys

from utils.pool import pool

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

    from django.core.management import execute_from_command_line

    try:
        execute_from_command_line(sys.argv)
    except KeyboardInterrupt:
        pool.close()
        pool.join()
    else:
        pool.close()
        pool.join()
