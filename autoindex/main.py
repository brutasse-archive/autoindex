import args
import os
import urlparse
import sys

from . import watcher, indexer, mirror
from .utils import error

ACTIONS = ['mirror', 'watch', 'index']

def show_help():
    print """Usage: %s -d directory [-i indexserver] action
Available actions: watch, index, mirror.""" % sys.argv[0]
    sys.exit(1)


def main():
    action = None
    directory = None
    index_server = 'http://pypi.python.org'
    index_set = False

    for name, target in args.grouped.iteritems():
        if name == '_' and action is None:
            action = target[0]
        elif name == '_':  # Only one action at once
            show_help()

        if name == '-d' and directory is None and target:
            directory = target[0]
            if len(target) > 1:
                action = target[1]
        elif name == '-d':
            show_help()

        if name == '-i' and index_set is False and target:
            index_server = target[0]
            index_set = True
            if len(target) > 1:
                action = target[1]
        elif name == '-i':
            show_help()

    if action is None or directory is None:
        show_help()

    if action not in ACTIONS:
        show_help()

    directory = os.path.abspath(directory)

    if action == 'index':
        indexer.index(directory)

    elif action == 'watch':
        watcher.watch(directory)

    elif action == 'mirror':
        parsed = urlparse.urlparse(index_server)
        if parsed.scheme not in ['http', 'https']:
            error("Invalid URL scheme: {0}".format(repr(parsed.scheme)))

        parsed = list(parsed)
        parsed[2] = '/simple/'

        index_url = urlparse.urlunparse(parsed)
        mirror.mirror(directory, index_url)
    sys.exit(0)
