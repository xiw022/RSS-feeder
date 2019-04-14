from flask import Flask, request, send_from_directory, Response,render_template
import urllib
import urllib.request
import urllib.parse
import json
import feedparser
import datetime as dt
from datetime import datetime, timedelta
import pytz
import time
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# default feeds source
url_awesome = 'https://9gag-rss.com/api/rss/get?code=9GAGAwesome&format=2'
cached_awesome = feedparser.parse(url_awesome)


# we want to only request feeds after every 2 minutes
utc = pytz.utc
homeTZ = pytz.timezone('US/Eastern')
prev_time = datetime.now(homeTZ)

# set previous time as ealiest as possible initially
prev_awesome = prev_time.replace(year=1)
prev_comic = prev_time.replace(year=1)

@app.route("/")
def load_page():
    # return home page
    return render_template('index.html', title='9GAG - Awesome Feeder')

# get feeds from 9GAG awesome source
@app.route("/get_awesome/", methods=['POST'])
def get_posts():

    global prev_awesome
    global cached_awesome
    global homeTZ
    global url_awesome

    curr_time = datetime.now(homeTZ)

    # check if it's 2 minutes from last request
    if prev_awesome is not None and cached_awesome is not None and (curr_time - prev_awesome).total_seconds() < 120:
        print("using cache")
        return render_template('front.html', title='Welcome to RSS-Feeder', content=cached_awesome['entries'])

    prev_awesome = datetime.now(homeTZ)
    cached_awesome= feedparser.parse(url_awesome)

    return render_template('front.html', title='Welcome to RSS-Feeder', content=cached_awesome['entries'])

if __name__ == '__main__':
    app.run(port=5000, debug=True)
