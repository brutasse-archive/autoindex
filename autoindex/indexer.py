import logging
import os
import tarfile
import zipfile

from contextlib import closing
from pip.download import is_archive_file
from pip.util import splitext

logger = logging.getLogger(__name__)

DIST_PAGE = """<!doctype html>
<html>
 <head>
  <title>Links for {dist}</title>
 </head>
 <body>
  <h1>Links for {dist}</h1>
{links}
 </body>
</html>"""

DIST = """  <a href="../../{package}">{package}</a><br>"""

INDEX_PAGE = """<!doctype html>
<html>
 <head>
  <title>Simple index</title>
 </head>
 <body>
{links}
 </body>
</html>"""

INDEX_LINK = """  <a href="{dist}/index.html">{dist}</a><br>"""


class Archive(object):
    def pkg_info(self):
        """Fetches the content of the archive's PKG-INFO"""
        for name in self.names():
            if len(name.split('/')) == 2 and name.endswith('PKG-INFO'):
                break
        else:
            raise AttributeError("No PKG-INFO found")

        return self.content(name)


class ZipArchive(Archive):
    def __init__(self, file_name):
        self.file_name = file_name
        self.zip_file = zipfile.ZipFile(file_name, 'r')

    def names(self):
        """Returns the file names in the archive."""
        return self.zip_file.namelist()

    def content(self, name):
        """Reads the content of a file."""
        return self.zip_file.read(name)

    def close(self):
        return self.zip_file.close()


class TarArchive(Archive):
    def __init__(self, file_name):
        self.file_name = file_name
        self.tar_file = tarfile.TarFile.open(file_name, 'r')

    def names(self):
        return self.tar_file.getnames()

    def content(self, name):
        return self.tar_file.extractfile(name).read()

    def close(self):
        return self.tar_file.close()


def metadata(distribution):
    """
    Extracts the metadata from a distribution's PKG-INFO.
    """
    name, ext = splitext(distribution)
    archive = {
        '.zip': ZipArchive,
        '.tar.gz': TarArchive,
        '.tar.bz2': TarArchive,
        '.tar.tgz': TarArchive,
        '.tar': TarArchive,
    }[ext](distribution)

    with closing(archive) as arc:
        try:
            pkg_info = arc.pkg_info()
        except AttributeError:
            # Do it the dumb way -- extract name and version from filename
            file_name, ext = splitext(arc.file_name.rsplit('/')[-1])
            name, version = file_name.rsplit('-', 1)
        else:
            name = None
            version = None
            for line in pkg_info.split('\n'):
                if line.startswith('Name: '):
                    name = line.split()[1]
                elif line.startswith('Version: '):
                    version = line.split()[1]
                if name and version:
                    break
    return name, version


def int_maybe(value):
    """Hey, I just saw this value
    And this is crazy
    But I want an int
    So cast it, maybe?"""
    try:
        return int(value)
    except ValueError:
        return value


def mkdir(path):
    """Ensures a directory exists"""
    try:
        os.mkdir(path)
    except OSError:
        pass


def index(directory):
    logger.info("Indexing {0}".format(directory))
    files = os.listdir(directory)
    dist_info = {}

    # Collect all distributions
    for f in files:
        if is_archive_file(f):
            full_path = os.path.join(directory, f)
            name, version = metadata(full_path)
            dist_info.setdefault(name, []).append([version, f])

    # Sort by version numbers
    for package, versions in dist_info.iteritems():
        dist_info[package] = sorted(
            versions, key=lambda d: map(int_maybe, d[0].split('.')),
        )

    # Write index
    logger.debug("Writing index")
    index_dir = os.path.join(directory, 'index')
    mkdir(index_dir)

    index_links = "\n".join((
        INDEX_LINK.format(dist=dist) for dist in sorted(dist_info)
    ))
    with open(os.path.join(index_dir, 'index.html'), 'w') as index:
        index.write(INDEX_PAGE.format(links=index_links))

    for package, version in dist_info.iteritems():
        logger.debug("Writing index for {0}".format(package))
        package_dir = os.path.join(index_dir, package)
        mkdir(package_dir)

        links = "\n".join((
            DIST.format(package=v[1]) for v in version
        ))
        with open(os.path.join(package_dir, 'index.html'), 'w') as index:
            index.write(DIST_PAGE.format(dist=package, links=links))
    logger.info("Indexing done")
