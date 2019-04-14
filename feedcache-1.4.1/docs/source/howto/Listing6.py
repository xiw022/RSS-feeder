#!/usr/bin/env python
"""Simple HTTP server for testing the feed cache.
"""

import BaseHTTPServer
import email.utils
import logging
import md5
import threading
import time
import unittest
import urllib


def make_etag(data):
    """Given a string containing data to be returned to the client,
    compute an ETag value for the data.
    """
    _md5 = md5.new()
    _md5.update(data)
    return _md5.hexdigest()


class TestHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    "HTTP request handler which serves the same feed data every time."

    FEED_DATA = """<?xml version="1.0" encoding="utf-8"?>

<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-us">
  <title>CacheTest test data</title>
  <link href="http://localhost/feedcache/" rel="alternate"></link>
  <link href="http://localhost/feedcache/atom/" rel="self"></link>
  <id>http://localhost/feedcache/</id>
  <updated>2006-10-14T11:00:36Z</updated>
  <entry>
    <title>single test entry</title>
    <link href="http://www.example.com/" rel="alternate"></link>
    <updated>2006-10-14T11:00:36Z</updated>
    <author>
      <name>author goes here</name>
      <email>authoremail@example.com</email>
    </author>
    <id>http://www.example.com/</id>
    <summary type="html">description goes here</summary>
    <link length="100" href="http://www.example.com/enclosure" type="text/html" rel="enclosure">
    </link>
  </entry>
</feed>"""

    # The data does not change, so save the ETag and modified times
    # as class attributes.
    ETAG = make_etag(FEED_DATA)
    MODIFIED_TIME = email.utils.formatdate(usegmt=True)

    def do_GET(self):
        "Handle GET requests."

        if self.path == '/shutdown':
            # Shortcut to handle stopping the server
            self.server.stop()
            self.send_response(200)
            
        else:
            incoming_etag = self.headers.get('If-None-Match', None)
            incoming_modified = self.headers.get('If-Modified-Since', None)

            send_data = True

            # Does the client have the same version of the data we have?
            if self.server.apply_modified_headers:
                if incoming_etag == self.ETAG:
                    self.send_response(304)
                    send_data = False

                elif incoming_modified == self.MODIFIED_TIME:
                    self.send_response(304)
                    send_data = False

            # Now optionally send the data, if the client needs it
            if send_data:
                self.send_response(200)
                self.send_header('Content-Type', 'application/atom+xml')
                self.send_header('ETag', self.ETAG)
                self.send_header('Last-Modified', self.MODIFIED_TIME)
                self.end_headers()

                self.wfile.write(self.FEED_DATA)
        return


class TestHTTPServer(BaseHTTPServer.HTTPServer):
    """HTTP Server which counts the number of requests made
    and can stop based on client instructions.
    """

    def __init__(self, applyModifiedHeaders=True):
        self.apply_modified_headers = applyModifiedHeaders
        self.keep_serving = True
        self.request_count = 0
        BaseHTTPServer.HTTPServer.__init__(self, ('', 9999), TestHTTPHandler)
        return

    def getNumRequests(self):
        "Return the number of requests which have been made on the server."
        return self.request_count

    def stop(self):
        "Stop serving requests, after the next request."
        self.keep_serving = False
        return

    def serve_forever(self):
        "Main loop for server"
        while self.keep_serving:
            self.handle_request()
            self.request_count += 1
        return


class HTTPTestBase(unittest.TestCase):
    "Base class for tests that use a TestHTTPServer"

    TEST_URL = 'http://localhost:9999/'

    CACHE_TTL = 0

    def setUp(self):
        self.server = self.getServer()
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.setDaemon(True) # so the tests don't hang if cleanup fails
        self.server_thread.start()
        return

    def getServer(self):
        "Return a web server for the test."
        return TestHTTPServer()

    def tearDown(self):
        # Stop the server thread
        ignore = urllib.urlretrieve('http://localhost:9999/shutdown')
        time.sleep(1)
        self.server.server_close()
        self.server_thread.join()
        return


class HTTPTest(HTTPTestBase):

    def testResponse(self):
        # Verify that the server thread responds
        # without error.
        filename, response = urllib.urlretrieve(self.TEST_URL)
        return

if __name__ == '__main__':
    unittest.main()
