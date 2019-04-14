#!/usr/bin/env python
"""The first version of Cache
"""

import time
import unittest
import feedparser
from Listing5 import Cache
from Listing6 import HTTPTestBase

class CacheTest(HTTPTestBase):

    def testFetch(self):
        c = Cache({})
        parsed_feed = c.fetch(self.TEST_URL)
        self.failUnless(parsed_feed.entries)
        return

    def testReuseContentsWithinTimeToLiveWindow(self):
        c = Cache({ self.TEST_URL:(time.time(), 'prepopulated cache')})
        cache_contents = c.fetch(self.TEST_URL)
        self.failUnlessEqual(cache_contents, 'prepopulated cache')
        return

if __name__ == '__main__':
    unittest.main()
