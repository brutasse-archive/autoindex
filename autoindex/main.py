import args
import sys

from . import watcher, indexer, mirror

ACTIONS = ['mirror', 'watch', 'index']

def show_help():
    print """Usage: %s -d directory [-i indexserver] action
Available actions: watch, index, mirror.""" % sys.argv[0]
    sys.exit(1)


def main():
    action = None
    directory = None
    index_server = 'https://pypi.python.org'
    index_set = False

    for name, target in args.grouped.iteritems():
        if name == '_' and action is None:
            action = target[0]
        elif name == '_':  # Only one action at once
            show_help()

        if name == '-d' and directory is None:
            directory = target[0]
            if len(target) > 1:
                action = target[1]
        elif name == '-d':
            show_help()

        if name == '-i' and index_set is False:
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

    print "Action: {0}".format(action)
    print "Directory: {0}".format(directory)
    print "Index server: {0}".format(index_server)
    sys.exit(0)
