#!/usr/bin/env python
"""Print contents of feeds specified on the command line.
"""

import feedparser
import sys

for url in sys.argv[1:]:
    data = feedparser.parse(url)
    for entry in data.entries:
        print '%s: %s' % (data.feed.title, entry.title)
