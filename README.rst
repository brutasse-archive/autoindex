Autoindex
=========

Autoindex lets you create a private index for pip, similar to `PyPI`_ but with
only the packages you need **and** additional private packages.

This lets you:

* Mirror the libraries you use (which you should absolutely do since some tend
  to disappear or become unavailable from time to time),

* Serve your proprietary packages on that index.

Packages are downloaded to a directory, the index is generated using this
directory and you only need a web server to serve that directory to the
public.

If you need security, just serve that index on SSL + HTTP Basic
authentication. Then to use it with pip::

    pip install -i https://user:password@pypi.example.com/index

Or, in a ``requirements.txt`` file:

    --index-url=https://user:password@pypi.example.com/index

Usage
-----

Install it somewhere on your machine::


    git clone git@github.com:brutasse/autoindex.git
    cd autoindex
    python setup.py install

Then create the autoindex public directory and configure your web server to
serve it::

    mkdir /var/www/autoindex

Create a ``/var/www/autoindex/mirror`` file that lists the packages you want
to mirror (one per line), for instance::

    Django
    raven

Note that if a package has dependencies, they must be listed as well.
Autoindex is that dumb, it won't parse deps for you.

Then setup a cron job to start mirroring::

    @daily /path/to/autoindex -d /var/www/autoindex mirror

Run it with the period you want, but don't be rude to PyPI. If you want to hit
another mirror than ``pypi.python.org``, make it so::

    /path/to/autoindex -d /var/www/autoindex -i http://a.pypi.python.org mirror

And finally, if you run this on a linux box (why wouldn't you?) you can run
the watcher to update the index when a file changes. This way making a release
is as simple as ``scp``'ing a file to the autoindex dir::

    /path/to/autoindex -d /var/www/autoindex watch

(Put this on a process supervisor like supervisor or circus, cause it may
crash.)

If you can't do that for some reason, just periodically regenerate the index::

    /path/to/autoindex -d /var/www/autoindex index

If you want to log new releases / stuff to Sentry, just install ``raven`` in
the same environment as ``autoindex`` and run the processes with a
``SENTRY_DSN`` environment variable.
