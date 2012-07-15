import os
import requests
import urlparse

from bs4 import BeautifulSoup
from pip.download import is_archive_file

from .utils import error

DIST_URL = "{index}{dist}/"


def mirror(directory, index_url):
    print "Mirroring {0} to {1}".format(index_url, directory)

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
        self.urls = set()
        self.existing = set()

    def extract_links(self, urls, dist, found=set(), additional=set()):
        """
        Recursively extract download links from a URL.
        """
        for url in urls:
            response = requests.get(url)
            if response.status_code != 200:
                print "Yo response WTF"
                print response, url
                continue

            soup = BeautifulSoup(response.content)
            for link in soup.find_all('a'):
                if not 'href' in link.attrs:
                    continue

                potential = link.attrs['href']
                if not '://' in potential:
                    potential = urlparse.urljoin(url, potential)
                potential = urlparse.urlparse(potential)

                if dist in potential.path and is_archive_file(potential.path):
                    potential = list(potential)
                    potential[5] = ''
                    found.add(urlparse.urlunparse(potential))
                    continue

                if 'rel' in link.attrs and link.attrs['rel'] == [u'download'] and not is_archive_file(link.attrs['href']):
                    print "Download URL {0}".format(link.attrs['href'])
                    additional.add(urlparse.urlunparse(potential))

            found = found.union(self.extract_links(additional, dist, additional=set()))
        return found

    def fetch_dist(self, dist):
        print "Mirroring {0}".format(dist)
        files = set(os.listdir(self.directory))

        url = DIST_URL.format(index=self.index_url, dist=dist)
        links = self.extract_links([url], dist)

        to_download = [
            link for link in links if link.rsplit('/')[-1] not in files
        ]

        for download in to_download:
            print "Fetching {0}".format(download)
            response = requests.get(download)
            if not response.status_code == 200:
                print "Error fetching {0}, status {1}".format(
                    download, response.status_code,
                )
                continue

            file_name = os.path.join(self.directory, download.rsplit('/')[-1])
            with open(file_name, 'wb') as f:
                f.write(response.content)
