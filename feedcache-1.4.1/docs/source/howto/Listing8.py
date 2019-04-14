#!/usr/bin/env python
"""Cache class with conditional HTTP GET support.
"""

import feedparser
import time
import unittest
import UserDict

import Listing6 # For the test base class

class Cache:

    def __init__(self, storage, timeToLiveSeconds=300, userAgent='feedcache'):
        self.storage = storage
        self.time_to_live = timeToLiveSeconds
        self.user_agent = userAgent
        return

    def fetch(self, url):
        modified = None
        etag = None
        now = time.time()

        cached_time, cached_content = self.storage.get(url, (None, None))

        # Does the storage contain a version of the data
        # which is older than the time-to-live?
        if cached_time is not None:
            if self.time_to_live:
                age = now - cached_time
                if age <= self.time_to_live:
                    return cached_content
            
            # The cache is out of date, but we have
            # something.  Try to use the etag and modified_time
            # values from the cached content.
            etag = cached_content.get('etag')
            modified = cached_content.get('modified')

        # We know we need to fetch, so go ahead and do it.
        parsed_result = feedparser.parse(url,
                                         agent=self.user_agent,
                                         modified=modified,
                                         etag=etag,
                                         )

        status = parsed_result.get('status', None)
        if status == 304:
            # No new data, based on the etag or modified values.
            # We need to update the modified time in the
            # storage, though, so we know that what we have
            # stored is up to date.
            self.storage[url] = (now, cached_content)

            # Return the data from the cache, since
            # the parsed data will be empty.
            parsed_result = cached_content
        elif status == 200:
            # There is new content, so store it unless there was an error.
            error = parsed_result.get('bozo_exception')
            if not error:
                self.storage[url] = (now, parsed_result)

        return parsed_result


class SingleWriteMemoryStorage(UserDict.UserDict):
    """Cache storage which only allows the cache value 
    for a URL to be updated one time.
    """

    def __setitem__(self, url, data):
        if url in self.keys():
            modified, existing = self[url]
            # Allow the modified time to change, 
            # but not the feed content.
            if data[1] != existing:
                raise AssertionError('Trying to update cache for %s to %s' \
                                         % (url, data))
        UserDict.UserDict.__setitem__(self, url, data)
        return


class CacheConditionalGETTest(Listing6.HTTPTestBase):

    def setUp(self):
        Listing6.HTTPTestBase.setUp(self)
        self.cache = Cache(storage=SingleWriteMemoryStorage(),
                           timeToLiveSeconds=0, # so we do not reuse the local copy
                           )
        return

    def testFetchOnceForEtag(self):
        # Fetch data which has a valid ETag value, and verify
        # that while we hit the server twice the response
        # codes cause us to use the same data.

        # First fetch populates the cache
        response1 = self.cache.fetch(self.TEST_URL)
        self.failUnlessEqual(response1.feed.title, 'CacheTest test data')

        # Remove the modified setting from the cache so we know
        # the next time we check the etag will be used
        # to check for updates.  Since we are using an in-memory
        # cache, modifying response1 updates the cache storage
        # directly.
        response1['modified'] = None

        # Wait so the cache data times out
        time.sleep(1)

        # This should result in a 304 status, and no data from
        # the server.  That means the cache won't try to
        # update the storage, so our SingleWriteMemoryStorage
        # should not raise and we should have the same
        # response object.
        response2 = self.cache.fetch(self.TEST_URL)
        self.failUnless(response1 is response2)

        # Should have hit the server twice
        self.failUnlessEqual(self.server.getNumRequests(), 2)
        return

    def testFetchOnceForModifiedTime(self):
        # Fetch data which has a valid Last-Modified value, and verify
        # that while we hit the server twice the response
        # codes cause us to use the same data.

        # First fetch populates the cache
        response1 = self.cache.fetch(self.TEST_URL)
        self.failUnlessEqual(response1.feed.title, 'CacheTest test data')

        # Remove the etag setting from the cache so we know
        # the next time we check the modified time will be used
        # to check for updates.  Since we are using an in-memory
        # cache, modifying response1 updates the cache storage
        # directly.
        response1['etag'] = None

        # Wait so the cache data times out
        time.sleep(1)

        # This should result in a 304 status, and no data from
        # the server.  That means the cache won't try to
        # update the storage, so our SingleWriteMemoryStorage
        # should not raise and we should have the same
        # response object.
        response2 = self.cache.fetch(self.TEST_URL)
        self.failUnless(response1 is response2)

        # Should have hit the server twice
        self.failUnlessEqual(self.server.getNumRequests(), 2)
        return
    
if __name__ == '__main__':
    unittest.main()
