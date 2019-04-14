#!/usr/bin/env python

from __future__ import with_statement

"""Using Cache with shelve.
"""

import os
import shelve
import tempfile
import threading
import unittest

from Listing6 import HTTPTestBase
from Listing8 import Cache

class CacheStorageLock:

    def __init__(self, shelf):
        self.lock = threading.Lock()
        self.shelf = shelf
        return

    def __getitem__(self, key):
        with self.lock:
            return self.shelf[key]

    def get(self, key, default=None):
        with self.lock:
            try:
                return self.shelf[key]
            except KeyError:
                return default

    def __setitem__(self, key, value):
        with self.lock:
            self.shelf[key] = value


class CacheShelveTest(HTTPTestBase):

    def setUp(self):
        HTTPTestBase.setUp(self)
        handle, self.shelve_filename = tempfile.mkstemp('.shelve')
        os.close(handle) # we just want the file name, so close the open handle
        os.unlink(self.shelve_filename) # remove empty file so shelve is not confused
        return

    def tearDown(self):
        try:
            os.unlink(self.shelve_filename)
        except AttributeError:
            pass
        HTTPTestBase.tearDown(self)
        return

    def test(self):
        storage = shelve.open(self.shelve_filename)
        locking_storage = CacheStorageLock(storage)
        try:
            fc = Cache(locking_storage)

            # First fetch the data through the cache
            parsed_data = fc.fetch(self.TEST_URL)
            self.failUnlessEqual(parsed_data.feed.title, 'CacheTest test data')

            # Now retrieve the same data directly from the shelf
            modified, shelved_data = storage[self.TEST_URL]
            
            # The data should be the same
            self.failUnlessEqual(parsed_data, shelved_data)
        finally:
            storage.close()
        return


if __name__ == '__main__':
    unittest.main()

