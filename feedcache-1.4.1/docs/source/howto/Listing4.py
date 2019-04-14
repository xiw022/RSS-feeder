#!/usr/bin/env python
"""The first version of Cache
"""

import unittest
import feedparser

class Cache:
    def __init__(self, storage):
        self.storage = storage
        return

    def fetch(self, url):
        return feedparser.parse(url)

class CacheTest(unittest.TestCase):

    def testFetch(self):
        c = Cache({})
        parsed_feed = c.fetch('http://feeds.feedburner.com/FeedcacheReleases')
        self.failUnless(parsed_feed.entries)
        return

if __name__ == '__main__':
    unittest.main()
