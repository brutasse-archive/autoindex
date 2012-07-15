import logging
import signal

from pip.download import is_archive_file
from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes

from .indexer import index

logger = logging.getLogger(__name__)


class IndexProcess(ProcessEvent):
    def process_IN_CREATE(self, event):
        logger.debug("Created {0}".format(event.pathname))
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
            signal.setitimer(signal.ITIMER_REAL, 5)


def watch(directory):
    logger.info("Watching {0}".format(directory))

    wm = WatchManager()
    flags = EventsCodes.ALL_FLAGS
    mask = flags['IN_CREATE'] | flags['IN_MODIFY'] | flags['IN_DELETE']

    process = IndexProcess()
    notifier = Notifier(wm, process)
    wm.add_watch(directory, mask, rec=False)

    def update_index(*args):
        index(directory)

    signal.signal(signal.SIGALRM, update_index)
    notifier.loop()
