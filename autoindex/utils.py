import os
import sys


def error(err):
    print err
    sys.exit(1)


def mkdir(path):
    """Ensures a directory exists"""
    try:
        os.mkdir(path)
    except OSError:
        pass
