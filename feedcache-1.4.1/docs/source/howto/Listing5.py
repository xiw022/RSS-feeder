#!/usr/bin/env python
"""The first version of Cache
"""

import time
import unittest
import feedparser

class Cache:
    def __init__(self, storage, timeToLiveSeconds=300):
        self.storage = storage
        self.time_to_live = timeToLiveSeconds
        return

    def fetch(self, url):
        now = time.time()
        cached_time, cached_content = self.storage.get(url, (None, None))

        # Does the storage contain a version of the data
        # which is older than the time-to-live?
        if cached_time is not None:
            age = now - cached_time
            if age <= self.time_to_live:
                return cached_content

        parsed_data = feedparser.parse(url)
        self.storage[url] = (now, parsed_data)
        return parsed_data

class CacheTest(unittest.TestCase):

    def testFetch(self):
        c = Cache({})
        parsed_feed = c.fetch('http://feeds.feedburner.com/FeedcacheReleases')
        self.failUnless(parsed_feed.entries)
        return

    def testReuseContentsWithinTimeToLiveWindow(self):
        url = 'http://feeds.feedburner.com/FeedcacheReleases'
        c = Cache({ url:(time.time(), 'prepopulated cache')})
        cache_contents = c.fetch(url)
        self.failUnlessEqual(cache_contents, 'prepopulated cache')
        return

if __name__ == '__main__':
    unittest.main()
