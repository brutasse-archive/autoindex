import logging
import os
import signal

from pip.download import is_archive_file
from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes

from .indexer import index

logger = logging.getLogger(__name__)


class IndexProcess(ProcessEvent):
    def __init__(self, wm, mask):
        self.wm = wm
        self.mask = mask
        self.queue = set()

    def update_watch(self, directory):
        self.wm.add_watch(directory, mask=self.mask)

    def process_IN_CREATE(self, event):
        logger.debug("Created {0}".format(event.pathname))
        if os.path.isdir(event.pathname):
            self.update_watch(event.pathname)
        else:
            self.index_alarm(event)

    def process_IN_MODIFY(self, event):
        logger.debug("Modified {0}".format(event.pathname))
        self.index_alarm(event)

    def process_IN_DELETE(self, event):
        logger.debug("Deleted {0}".format(event.pathname))
        self.index_alarm(event)

    def index_alarm(self, event):
        if is_archive_file(event.pathname):
            logger.debug("Queuing indexing")
            self.queue.add(os.path.dirname(event.pathname))
            signal.setitimer(signal.ITIMER_REAL, 5)


def watch(directory):
    logger.info("Watching {0}".format(directory))

    flags = EventsCodes.ALL_FLAGS
    mask = flags['IN_CREATE'] | flags['IN_MODIFY'] | flags['IN_DELETE']

    wm = WatchManager()
    wm.add_watch(directory, mask, rec=True)

    process = IndexProcess(wm, mask)
    notifier = Notifier(wm, process)

    def update_index(*args):
        while process.queue:
            # This is slightly sub-optimal, would be better to pop all
            # elements at once but this operation needs to be atomic.
            dist_dir = process.queue.pop()
            index(directory, only=[dist_dir])

    signal.signal(signal.SIGALRM, update_index)
    notifier.loop()
