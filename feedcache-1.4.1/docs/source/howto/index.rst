================================
Caching RSS Feeds With feedcache
================================

.. note::

   This article was originally printed in Python Magazine Volume 1
   Issue 11, November, 2007.

The past several years have seen a steady increase in the use of RSS
and Atom feeds for data sharing.  Blogs, podcasts, social networking
sites, search engines, and news services are just a few examples of
data sources delivered via such feeds. Working with internet services
requires care, because inefficiencies in one client implementation may
cause performance problems with the service that can be felt by all of
the consumers accessing the same server. In this article, I describe
the development of the **feedcache** package, and give examples of how
you can use it to optimize the use of data feeds in your application.

.. highlight:: python
    :linenothreshold: 10

I frequently find myself wanting to listen to one or two episodes from
a podcast, but not wanting to subscribe to the entire series. In order
to scratch this itch, I built a web based tool, hosted at
http://www.castsampler.com/, to let me pick and choose individual
episodes from a variety of podcast feeds, then construct a single feed
with the results. Now I subscribe to the single feed with my podcast
client, and easily populate it with new episodes when I encounter any
that sound interesting. The `feedcache
<http://www.doughellmann.com/projects/feedcache/>`_ package was
developed as part of this tool to manage accessing and updating the
feeds efficiently, and has been released separately under the BSD
license.

Example Feed Data
-----------------

The two most common publicly implemented formats for syndicating web
data are RSS (in one of a few versions) and Atom. Both formats have a
similar structure. Each feed begins with basic information about the
data source (title, link, description, etc.). The introductory
information is followed by a series of "items", each of which
represents a resource like a blog post, news article, or podcast. Each
item, in turn, has a title, description, and other information like
when it was written. It may also refer to one or more attachments, or
enclosures.

Listing 1 shows a sample RSS 2.0 feed and Listing 2 shows a sample
Atom feed. Each sample listing contains one item with a single podcast
enclosure. Both formats are XML, and contain essentially the same
data. They use slightly different tag names though, and podcast
enclosures are handled differently between the two formats, which can
make working with different feed formats more work in some
environments. Fortunately, Python developers do not need to worry
about the differences in the feed formats, thanks to the Universal
Feed Parser.

Listing 1
~~~~~~~~~

.. literalinclude:: Listing1.xml
    :linenos:

Listing 2
~~~~~~~~~

.. literalinclude:: Listing2.xml
    :linenos:

Universal Feed Parser
---------------------

Mark Pilgrim's Universal Feed Parser is an open source module that
manages most aspects of downloading and parsing RSS and Atom feeds.
Once the feed has been downloaded and parsed, the parser returns an
object with all of the parsed data easily accessible through a single
API, regardless of the original feed format.

Listing 3 shows a simple example program for accessing feeds with
`feedparser <http://www.feedparser.org/>`_. On line 9, a URL from the
command line arguments is passed to ``feedparser.parse()`` to be
downloaded and parsed. The results are returned as a
FeedParserDict. The properties of the FeedParserDict can be accessed
via the dictionary API or using attribute names as illustrated on line
10.

Listing 3
~~~~~~~~~

.. literalinclude:: Listing3.py
    :linenos:

When the sample program in Listing 3 is run with the URL for the feed
of **feedcache** project releases, it shows the titles for the
releases available right now:

::

    $ python Listing3.py http://feeds.feedburner.com/FeedcacheReleases
    feedcache Releases: feedcache 0.1
    feedcache Releases: feedcache 0.2
    feedcache Releases: feedcache 0.3
    feedcache Releases: feedcache 0.4
    feedcache Releases: feedcache 0.5

Every time the program runs, it fetches the entire feed, whether the
contents have changed or not. That inefficiency might not matter a
great deal for a client program that is not run frequently, but the
inefficiencies add up on the server when many clients access the same
feed, especially if they check the feed on a regular basis. This
inefficient behavior can become an especially bad problem for the
server if the feed contents are produced dynamically, since each
client incurs a certain amount of CPU, I/O, and bandwidth load needed
to produce the XML representation of the feed. Some sites are
understandably strict about how often a client can retrieve feeds, to
cut down on heavy bandwidth and CPU consumers. Slashdot, for example,
returns a special feed with a warning to any client that accesses
their RSS feed too frequently over a short span of time.

A Different Type of Podcast Aggregator
--------------------------------------

A typical aggregator design would include a monitor to regularly
download the feeds and store the fresh information about the feed and
its contents in a database. The requirements for CastSampler are a
little different, though.

CastSampler remembers the feeds to which a user has subscribed, but
unlike other feed aggregators, it only downloads the episode metadata
while the user is choosing episodes to add to their download
feed. Since the user does not automatically receive every episode of
every feed, the aggregator does not need to constantly monitor all of
the feeds. Instead, it shows a list of episodes for a selected feed,
and lets the user choose which episodes to download. Then it needs to
remember those selected episodes later so it can produce the combined
feed for the user's podcast client.

If every item from every feed was stored in the database, most of the
data in the database would be for items that were never selected for
download. There would need to be a way to remove old data from the
database when it expired or was no longer valid, adding to the
maintenance work for the site. Instead, CastSampler only uses the
database to store information about episodes selected by the user.
The rest of the data about the feed is stored outside of the database
in a form that makes it easier to discard old data when the feed is
updated.  This division eliminates a lot of the data management effort
behind running the site.

Feedcache Requirements
----------------------

An important goal for this project was to make CastSampler a polite
consumer of feeds, and ensure that it did not overload servers while a
user was selecting podcast episodes interactively. By caching the feed
data for a short period of time, CastSampler could avoid accessing
feeds every time it needed to show the feed data. A persistent cache,
written to disk, would let the data be reused even if the application
was restarted, such as might happen during development. Using a cache
would also improve responsiveness, since reading data from the local
disk would be faster than fetching the feed from the remote server. To
further reduce server load, **feedcache** is designed to take
advantage of conditional GET features of HTTP, to avoid downloading
the full feed whenever possible.

Another goal was to have a small API for the cache. It should take
care of everything for the caller, so there would not need to be many
functions to interact with it. To retrieve the contents of a feed, the
caller should only have to provide the URL for that feed. All other
information needed to track the freshness of the data in the cache
would be managed internally.

It was also important for the cache to be able to store data in
multiple ways, to make it more flexible for other programmers who
might want to use it. Although CastSampler was going to store the
cache on disk, other applications with more computing resources or
tighter performance requirements might prefer to hold the cache in
memory. Using disk storage should not be hard coded into the cache
management logic.

These requirements led to a design which split the responsibility for
managing the cached data between two objects. The **Cache** object
tracks information about a feed so it can download the latest version
as efficiently as possible, only when needed. Persistent storage of
the data in the cache is handled by a separate back end storage
object.  Dividing the responsibilities in this way maximizes the
flexibility of the **Cache**, since it can concentrate on tracking
whether the feed is up to date without worrying about storage
management. It also let **Cache** users take advantage of multiple
storage implementations.

The Cache Class
---------------

Once the basic requirements and a skeleton design were worked out, the
next step was to start writing tests so the implementation of
**Cache** could begin. Working with a few simple tests would clarify
how a **Cache** user would want to access feeds. The first test was to
verify that the **Cache** would fetch feed data.

::

    import unittest, cache
    class CacheTest(unittest.TestCase):
        def testFetch(self):
            c = cache.Cache({})
            parsed_feed = c.fetch('http://feeds.feedburner.com/FeedcacheReleases')
            self.failUnless(parsed_feed.entries)

Since the design separated storage and feed management
responsibilities, it was natural to pass the storage handler to the
**Cache** when it is initialized. The dictionary API is used for the
storage because there are several storage options available that
support it. The shelve module in the Python standard library stores
data persistently using an object that conforms to the dictionary API,
as does the `shove <http://pypi.python.org/pypi/shove>`_ library from
L.C. Rees. Either library would work well for the final
application. For initial testing, using a simple dictionary to hold
the data in memory was convenient, since that meant the tests would
not need any external resources.

After constructing the **Cache**, the next step in the test is to
retrieve a feed. I considered using using the ``__getitem__()`` hook,
but since **Cache** would not support any of the other dictionary
methods, I rejected it in favor of an explicit method,
``fetch()``. The caller passes a feed URL to ``fetch()``, which
returns a FeedParserDict instance.  Listing 4 shows the first version
of the **Cache** class that works for the test as it is written. No
actual caching is being done, yet. The **Cache** instance simply uses
the **feedparser** module to retrieve and parse the feed.

Listing 4
~~~~~~~~~

.. literalinclude:: Listing4.py
    :linenos:

Throttling Downloads
--------------------

Now that **Cache** could successfully download feed data, the first
optimization to make was to hold on to the data and track its age.
Then for every call to ``fetch()``, **Cache** could first check to see
if fresh data was already available locally before going out to the
server to download the feed again.

Listing 5 shows the version of **Cache** with a download throttle, in
the form of a ``timeToLiveSeconds`` parameter. Items already in the
cache will be reused until they are older than
``timeToLiveSeconds``. The default value for ``timeToLiveSeconds``
means that any given feed will not be checked more often than every
five minutes.

Listing 5
~~~~~~~~~

.. literalinclude:: Listing5.py
    :linenos:

The new implementation of ``fetch()`` stores the current time along
with the feed data when the storage is updated. When ``fetch()`` is
called again with the same URL, the time in the cache is checked
against the current time to determine if the value in the cache is
fresh enough. The test on line 38 verifies this behavior by
pre-populating the **Cache**'s storage with data, and checking to see
that the existing cache contents are returned instead of the contents
of the feed.

Conditional HTTP GET
--------------------

Conditional HTTP GET allows a client to tell a server something about
the version of a feed the client already has. The server can decide if
the contents of the feed have changed and, if they have not, send a
short status code in the HTTP response instead of a complete copy of
the feed data. Conditional GET is primarily a way to conserve
bandwidth, but if the feed has not changed and the server's version
checking algorithm is efficient then the server may use fewer CPU
resources to prepare the response, as well.

When a server implements conditional GET, it uses extra headers with
each response to notify the client. There are two headers involved,
and the server can use either or both together, in case the client
only supports one. **Cache** supports both headers.

Although timestamps are an imprecise way to detect change, since the
time on different servers in a pool might vary slightly, they are
simple to work with. The ``Last-Modified`` header contains a timestamp
value that indicates when the feed contents last changed. The client
sends the timestamp back to the server in the next request as
``If-Modified-Since``. The server then compares the dates to determine
if the feed has been modified since the last request from the client.

A more precise way to determine if the feed has changed is to use an
*Entity Tag* in the ``ETag`` header. An ``ETag`` is a hashed
representation of the feed state, or of a value the server can use to
quickly determine if the feed has been updated. The data and algorithm
for computing the hash is left up to the server, but it should be less
expensive than returning the feed contents or there won't be any
performance gains. When the client sees an ``ETag`` header, it can
send the associated value back to the server with the next request in
the ``If-None-Match`` request header. When the server sees
``If-None-Match``, it computes the current hash and compares it to the
value sent by the client. If they match, the feed has not changed.

When using either ``ETag`` or modification timestamps, if the server
determines that the feed has not been updated since the previous
request, it returns a response code of ``304``, or "Not Modified" and
includes nothing in the body of the response. When it sees the ``304``
status in the response from the server, the client should reuse the
version of the feed it already has.

Creating a Test Server
----------------------

In order to write correct tests to exercise conditional GET in
**feedcache**, more control over the server would be important. The
feedburner URL used in the earlier tests might be down, or return
different data if a feed was updated. It would be necessary for the
server to respond reliably with data the test code knew in advance,
and to be sure it would not stop responding if it was queried too
often by the tests. The tests also control which of the headers
(``ETag`` or ``If-Modified-Since``) was used to determine if the feed
had changed, so both methods could be tested independently. The
solution was to write a small test HTTP server that could be managed
by the unit tests and configured as needed. Creating the test server
was easy, using a few standard library modules.

The test server code, along with a base class for unit tests that use
it, can be found in Listing 6. The ``TestHTTPServer`` (line 91) is
derived from ``BaseHTTPServer.HTTPServer``. The ``serve_forever()``
method (line 112) has been overridden with an implementation that
checks a flag after each request to see if the server should keep
running. The test harness sets the flag to stop the test server after
each test. The ``serve_forever()`` loop also counts the requests
successfully processed, so the tests can determine how many times the
**Cache** fetches a feed.

Listing 6
~~~~~~~~~

.. literalinclude:: Listing6.py
    :linenos:

The test server processes incoming HTTP requests with
``TestHTTPHandler`` (line 24), derived from
``BaseHTTPServer.BaseHTTPRequestHandler``. ``TestHTTPHandler``
implements ``do_GET()`` (line 55) to respond to HTTP GET requests.
Feed data for the tests is hard coded in the ``FEED_DATA`` class
attribute (line 27). The URL path ``/shutdown`` is used to tell the
server to stop responding to requests. All other paths are treated as
requests for the feed data. The requests are processed by checking the
``If-None-Match`` and ``If-Modified-Since`` headers, and responding
either with a ``304`` status or with the static feed data.

``HTTPTestBase`` is a convenience base class to be used by other
tests. It manages a ``TestHTTPServer`` instance in a separate thread,
so the tests can all run in a single process. Listing 7 shows what the
existing tests look like, rewritten to use the ``HTTPTestBase`` as a
base class. The only differences are the base class for the tests and
the use of ``self.TEST_URL``, which points to the local test server
instead of the **feedburner** URL from Listing 5.

Listing 7
~~~~~~~~~

.. literalinclude:: Listing7.py
    :linenos:

Implementing Conditional HTTP GET
---------------------------------

With these testing tools in place, the next step was to enhance the
**Cache** class to monitor and use the conditional HTTP GET
parameters.  Listing 8 shows the final version of **Cache** with these
features. The ``fetch()`` method has been enhanced to send the
``ETag`` and modified time from the cached version of the feed to the
server, when they are available.

Listing 8
~~~~~~~~~

.. literalinclude:: Listing8.py
    :linenos:

The **FeedParserDict** object returned from ``feedparser.fetch()``
conveniently includes the ``ETag`` and modified timestamp, if the
server sent them. On lines 38-39, once the cached feed is determined
to be out of date, the ``ETag`` and modified values are retrieved so
they can be passed in to ``feedparser.parse()`` on line 42.

Since the updated client sends ``ETag`` and ``If-Modified-Since``
headers, the server may now respond with a status code indicating that
the cached copy of the data is still valid. It is no longer sufficient
to simply store the response from the server before returning it. The
status code must be checked, as on line 49, and if the status is
``304`` then the timestamp of the cached copy is updated. If the
timestamp was not updated, then as soon as the cached copy of the feed
exceeded the time-to-live, the **Cache** would request a new copy of
the feed from the server every time the feed was accessed. Updating
the timestamp ensures that the download throttling remains enforced.

Separate tests for each conditional GET header are implemented in
``CacheConditionalGETTest``. To verify that the **Cache** handles the
``304`` status code properly and does not try to update the contents
of the storage on a second fetch, these tests use a special storage
class. The **SingleWriteMemoryStorage** raises an **AssertionError**
if the a value is modified after it is set the first time. An
``AssertionError`` is used, because that is how ``unittest.TestCase``
signals a test failure, and modifying the contents of the storage is a
failure for these tests.

Each test method of ``CacheConditionalGETTest`` verifies handling for
one of the conditional GET headers at a time. Since the test server
always sets both headers, each test clears one value from the cache
before making the second request. The remaining header value is sent
to the server as part of the second request, and the server responds
with the ``304`` status code.

Persistent Storage With shelve
------------------------------

All of the examples and tests so far have used in-memory storage
options. For CastSampler, though, the cache of feed data needed to be
stored on disk. As mentioned earlier, the **shelve** module in the
standard library provides a simple persistent storage mechanism. It
also conforms to the dictionary API used by the **Cache** class.

Using **shelve** by itself works in a simple single threaded case but
it isn't clear from its documentation whether **shelve** supports
write access from multiple concurrent threads. To ensure the shelf is
not corrupted, a thread lock should be used. ``CacheStorageLock`` is a
simple wrapper around **shelve** that uses a lock to prevent more than
one thread from accessing the shelf simultaneously. Listing 9 contains
the code for the ``CacheStorageLock`` and a test that illustrates
using it to combine a **Cache** and **shelve**.

Listing 9
~~~~~~~~~

.. literalinclude:: Listing9.py
    :linenos:

The test ``setUp()`` method uses ``tempfile`` to create a temporary
filename for the cache. The temporary file has to be deleted in
``setUp()`` because if the file exists, but is empty, **shelve**
cannot determine which database module to use to open an empty
file. The ``test()`` method fetches the data from the server, then
compares the returned data with the data in the shelf to verify that
they are the same.

``CacheStorageLock`` uses a ``threading.Lock`` instance to control
access to the shelf. It only manages access for the methods known to
be used by **Cache**. The lock is acquired and released using the
``with`` statement, which is new for Python 2.6. Since this code was
written with Python 2.5, the module starts with a ``from __future__``
import statement to enable the syntax for ``with``.

Other Persistence Options
-------------------------

At any one time, **shelve** only allows one process to open a shelf
file to write to it. In applications with multiple processes that need
to modify the cache, alternative storage options are
desirable. **Cache** treats its storage object as a dictionary, so any
class that conforms to the dictionary API can be used for back end
storage. The ``shove`` module, by L. C. Rees, uses the dictionary API
and offers support for a variety of back end storage options. The
supported options include relational databases, BSD-style databases,
Amazon's S3 storage service, and others.

The filesystem store option was particularly interesting for
CastSampler. With **shove**'s file store, each key is mapped to a
filename. The data associated with the key is pickled and stored in
the file. By using separate files, it is possible to have separate
threads and processes updating the cache simultaneously. Although the
**shove** file implementation doesn't handle file locking, for my
purposes it was unlikely that two threads would try to update the same
feed at the same time.

Listing 10 includes a test that illustrates using **shove** file
storage with **feedcache**. The primary difference in the APIs for
**shove** and **shelve** is the syntax for specifying the storage
destination. Shove uses a URL syntax to indicate which back end should
be used. The format for each back end is described in the docstrings.

Listing 10
~~~~~~~~~~

.. literalinclude:: Listing10.py
    :linenos:

Using feedcache With Multiple Threads
-------------------------------------

Up to this point, all of the examples have been running in a single
thread driven by the **unittest** framework. Now that integrating
**shove** and **feedcache** has been shown to work, it is possible to
take a closer look at using multiple threads to fetch feeds, and build
a more complex example application. Spreading the work of fetching
data into multiple processing threads is more complicated, but yields
better performance under most circumstances because while one thread
is blocked waiting for data from the network, another thread can take
over and process a different URL.

Listing 11 shows a sample application which accepts URLs as arguments
on the command line and prints the titles of all of the entries in the
feeds. The results may be mixed together, depending on how the
processing control switches between active threads. This example
program is more like a traditional feed aggregator, since it processes
every entry of every feed.

Listing 11
~~~~~~~~~~

.. literalinclude:: Listing11.py
    :linenos:

The design uses queues to pass data between two different types of
threads to work on the feeds. Multiple threads use **feedcache** to
fetch feed data. Each of these threads has its own **Cache**, but they
all share a common **shove** store. A single thread waits for the feed
entries to be added to its queue, and then prints each feed title and
entry title.

The ``main()`` function sets up two different queues for passing data
in and out of the worker threads. The ``url_queue`` (lines 23-25)
contains the URLs for feeds, taken from the command line arguments.
The ``entry_queue`` (line 33) is used to pass feed content from the
threads that fetch the feeds to the queue that prints the results. A
**shove** filesystem store (line 36) is used to cache the feeds. Once
all of the worker threads are started (lines 40-51), the rest of the
main program simply waits for each stage of the work to be completed
by the threads.

The last entries added to the ``url_queue`` are ``None`` values, which
trigger the worker thread to exit. When the ``url_queue`` has been
drained (line 54), the worker threads can be cleaned up. After the
worker threads have finished, ``(None, None)`` is added to the
``entry_queue`` to trigger the printing thread to exit when all of the
entries have been printed.

The ``fetch_urls()`` function (lines 70-85) runs in the worker
threads. It takes one feed URL at a time from the input queue,
retrieves the feed contents from a cache, then adds the feed entries
to the output queue. When the item taken out of the queue is ``None``
instead of a URL string, it is interpreted as a signal that the thread
should break out of its processing loop. Each thread running
``fetch_urls()`` creates a local **Cache** instance using a common
storage back end. Sharing the storage ensures that all of the feed
data is written to the same place, while creating a local **Cache**
instance ensures threads can fetch data in parallel.

The consumer of the queue of entries is ``print_entries()`` (lines
88-99). It takes one entry at a time from the queue and prints the
feed and entry titles. Only one thread runs ``print_entries()``, but a
separate thread is used so that output can be produced as soon as
possible, instead of waiting for all of the ``fetch_urls()`` threads
to complete before printing the feed contents.

Running the program produces output similar to the example in Listing
3:

::

    $ python Listing11.py http://feeds.feedburner.com/FeedcacheReleases
    Saving feed data to /tmp/feedcache_example
    feedcache Releases: feedcache 0.1
    feedcache Releases: feedcache 0.2
    feedcache Releases: feedcache 0.3
    feedcache Releases: feedcache 0.4
    feedcache Releases: feedcache 0.5

The difference is that it takes much less time to run the program in
Listing 11 when multiple feeds are passed on the command line, and
when some of the data has already been cached.

Future Work
-----------

The current version of **feedcache** meets most of the requirements
for **CastSampler**, but there is still room to improve it as a
general purpose tool. It would be nice if it offered finer control
over the length of time data stays in the cache, for example. And,
although **shove** is a completely separate project, **feedcache**
would be more reliable if **shove**'s file storage were used file
locking, to prevent corruption when two threads or processes write to
the same part of the cache at the same time.

Determining how long to hold the data in a cache can be a tricky
problem. With web content such as RSS and Atom feeds, the web server
may offer hints by including explicit expiration dates or caching
instructions. HTTP headers such as ``Expires`` and ``Cache-Control``
can include details beyond the ``Last-Modified`` and ``ETag`` values
already being handled by the **Cache**. If the server uses additional
cache headers, **feedparser** saves the associated values in the
**FeedParserDict**. To support the caching hints, **feedcache** would
need to be enhanced to understand the rules for the ``Cache-Control``
header, and to save the expiration time as well as the time-to-live
for each feed.

Supporting a separate time-to-live value for each feed would let
**feedcache** use a different refresh throttle for different
sites. Data from relatively infrequently updated feeds, such as
Slashdot, would stay in the cache longer than data from more
frequently updated feeds, such as a Twitter feed. Applications that
use **feedcache** in a more traditional way would be able to adjust
the update throttle for each feed separately to balance the freshness
of the data in the cache and the load placed on the server.

Conclusions
-----------

Original sources of RSS and Atom feeds are being created all the time
as new and existing applications expose data for syndication. With the
development of mashup tools such as Yahoo! Pipes and Google's Mashup
Editor, these feeds can be combined, filtered, and expanded in new and
interesting ways, creating even more sources of data. I hope this
article illustrates how building your own applications to read and
manipulate syndication feeds in Python with tools like feedparser and
**feedcache** is easy, even while including features that make your
program cooperate with servers to manage load.

*I would like to offer a special thanks to Mrs. PyMOTW for her help
editing this article.*
