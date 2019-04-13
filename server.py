from flask import Flask, request, send_from_directory, Response,render_template
from flask_cors import CORS, cross_origin
import urllib
import urllib.request
import urllib.parse
import json
import feedparser
from datetime import datetime, timedelta
import pytz
import time
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

url = 'https://9gag-rss.com/api/rss/get?code=9GAGAwesome&format=2'
cached_feeds = [];


# we want to only show feeds from today
utc = pytz.utc
homeTZ = pytz.timezone('US/Eastern')
curr_time = datetime.now(homeTZ)
earliest = curr_time.replace(hour=0, minute=0, second=0, microsecond=0)
start = earliest.astimezone(utc)

@app.route("/")
def load_page():
    feeds = get_posts()
    print(type(feeds['entries']))
    print(feeds['entries'][0])
    return render_template('front.html', title='9gag RSS Feeds Today', content=feeds['entries'])

@app.route("/get_posts")
def get_posts():
    res = []
    feeds = feedparser.parse(url)
    #print(type(feeds))
    #print(len(feeds))
    #print(feeds['entries'][0])
    #print(ress)
    return feeds


if __name__ == '__main__':
    app.run(port=5000, debug=True)
