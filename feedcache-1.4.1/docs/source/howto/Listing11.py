#!/usr/bin/env python
"""Example use of feedcache.Cache combined with threads.
"""

import Queue
import sys
import shove
import threading

from Listing8 import Cache

MAX_THREADS=5
OUTPUT_DIR='/tmp/feedcache_example'


def main(urls=[]):

    if not urls:
        print 'Specify the URLs to a few RSS or Atom feeds on the command line.'
        return

    # Add the URLs to a queue
    url_queue = Queue.Queue()
    for url in urls:
        url_queue.put(url)

    # Add poison pills to the url queue to cause
    # the worker threads to break out of their loops
    for i in range(MAX_THREADS):
        url_queue.put(None)

    # Track the entries in the feeds being fetched
    entry_queue = Queue.Queue()

    print 'Saving feed data to', OUTPUT_DIR
    storage = shove.Shove('file://' + OUTPUT_DIR)
    try:

        # Start a few worker threads
        worker_threads = []
        for i in range(MAX_THREADS):
            t = threading.Thread(target=fetch_urls, 
                                 args=(storage, url_queue, entry_queue,))
            worker_threads.append(t)
            t.setDaemon(True)
            t.start()

        # Start a thread to print the results
        printer_thread = threading.Thread(target=print_entries, args=(entry_queue,))
        printer_thread.setDaemon(True)
        printer_thread.start()

        # Wait for all of the URLs to be processed
        url_queue.join()

        # Wait for the worker threads to finish
        for t in worker_threads:
            t.join()

        # Poison the print thread and wait for it to exit
        entry_queue.put((None,None))
        entry_queue.join()
        printer_thread.join()        
        
    finally:
        storage.close()
    return


def fetch_urls(storage, input_queue, output_queue):
    """Thread target for fetching feed data.
    """
    c = Cache(storage)

    while True:
        next_url = input_queue.get()
        if next_url is None: # None causes thread to exit
            input_queue.task_done()
            break

        feed_data = c.fetch(next_url)
        for entry in feed_data.entries:
            output_queue.put( (feed_data.feed, entry) )
        input_queue.task_done()
    return


def print_entries(input_queue):
    """Thread target for printing the contents of the feeds.
    """
    while True:
        feed, entry = input_queue.get()
        if feed is None: # None causes thread to exist
            input_queue.task_done()
            break

        print '%s: %s' % (feed.title, entry.title)
        input_queue.task_done()
    return


if __name__ == '__main__':
    main(sys.argv[1:])

