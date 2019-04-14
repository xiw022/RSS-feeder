#!/usr/bin/env python
"""Tests with shove filesystem storage.
"""

import os
import shove
import tempfile
import threading
import unittest

from Listing6 import HTTPTestBase
from Listing8 import Cache

class CacheShoveTest(HTTPTestBase):

    def setUp(self):
        HTTPTestBase.setUp(self)
        self.shove_dirname = tempfile.mkdtemp('shove')
        return

    def tearDown(self):
        try:
            os.system('rm -rf %s' % self.storage_dirname)
        except AttributeError:
            pass
        HTTPTestBase.tearDown(self)
        return

    def test(self):
        # First fetch the data through the cache
        storage = shove.Shove('file://' + self.shove_dirname)
        try:
            fc = Cache(storage)
            parsed_data = fc.fetch(self.TEST_URL)
            self.failUnlessEqual(parsed_data.feed.title, 'CacheTest test data')
        finally:
            storage.close()

        # Now retrieve the same data directly from the shelf
        storage = shove.Shove('file://' + self.shove_dirname)
        try:
            modified, shelved_data = storage[self.TEST_URL]
        finally:
            storage.close()
            
        # The data should be the same
        self.failUnlessEqual(parsed_data, shelved_data)
        return


if __name__ == '__main__':
    unittest.main()
