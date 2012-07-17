import logging
import os
import requests
import urlparse

from HTMLParser import HTMLParseError
from bs4 import BeautifulSoup
from pip.download import is_archive_file

from .utils import error, mkdir

DIST_URL = "{index}{dist}/"

logger = logging.getLogger(__name__)


def mirror(directory, index_url):
    logger.info("Mirroring {0} to {1}".format(index_url, directory))

    mirror_file = os.path.join(directory, 'mirror')

    try:
        with open(mirror_file, 'r') as f:
            dists = f.read().split()
    except IOError:
        error("Please create {0} with the packages you want to mirror.".format(
            mirror_file,
        ))

    mirror = Mirror(directory, index_url)

    for dist in dists:
        mirror.fetch_dist(dist.strip())


class Mirror(object):
    def __init__(self, directory, index_url):
        self.directory = directory
        self.index_url = index_url

    def extract_links(self, urls, dist, found=None):
        """
        Recursively extract download links from a URL.
        """
        if found is None:
            found = set()
        for url in urls:
            response = requests.get(url)
            if response.status_code != 200:
                logger.info("Non-200 response from {url}: {code}".format(
                    url=url, code=response.status_code,
                ))
                continue

            try:
                soup = BeautifulSoup(response.content)
            except HTMLParseError:
                logger.debug("Parse error: {0}".format(url))
                continue
            additional = set()
            for link in soup.find_all('a'):
                if not 'href' in link.attrs:
                    continue

                potential = link.attrs['href']
                if not '://' in potential:
                    potential = urlparse.urljoin(url, potential)
                potential = urlparse.urlparse(potential)

                if (dist in potential.path and
                    is_archive_file(potential.path) and
                    not potential.path.endswith('.mpkg.zip') and
                    not ".macosx-10." in potential.path):
                    potential = list(potential)
                    potential[5] = ''
                    found.add(urlparse.urlunparse(potential))
                    continue

                if ('rel' in link.attrs and
                    link.attrs['rel'] == [u'download'] and
                    not is_archive_file(link.attrs['href'])):
                    logger.debug("Download URL {0}".format(link.attrs['href']))
                    additional.add(urlparse.urlunparse(potential))

            found = found.union(self.extract_links(additional, dist))
        return found

    def fetch_dist(self, dist):
        logger.info("Mirroring {0}".format(dist))
        directory = os.path.join(self.directory, dist)
        mkdir(directory)

        files = set(os.listdir(directory))

        url = DIST_URL.format(index=self.index_url, dist=dist)
        links = self.extract_links([url], dist)

        to_download = [
            link for link in links if link.rsplit('/')[-1] not in files
        ]

        for download in to_download:
            logger.info("Fetching {0}".format(download))
            response = requests.get(download)
            if not response.status_code == 200:
                logger.error("Error fetching {0}, status {1}".format(
                    download, response.status_code,
                ))
                continue

            file_name = os.path.join(directory,
                                     download.rsplit('/')[-1].split('?')[0])
            with open(file_name, 'wb') as f:
                f.write(response.content)
