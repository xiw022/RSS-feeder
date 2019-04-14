from flask import Flask, request, send_from_directory, Response,render_template
from flask_cors import CORS, cross_origin
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
CORS(app)

url = 'https://9gag-rss.com/api/rss/get?code=9GAGComic&format=2'
cached_feeds = feedparser.parse(url)


# we want to only request feeds after every 2 minutes
utc = pytz.utc
homeTZ = pytz.timezone('US/Eastern')
prev_time = datetime.now(homeTZ)
prev_time.replace(year=1)

@app.route("/")
def load_page():
    #feeds = get_posts()
    return render_template('front.html', title='9GAG - Awesome Feeder', content=feeds['entries'])

@app.route("/get_posts/", methods=['POST'])
def get_posts():

    global prev_time
    global cached_feeds
    global homeTZ

    print(homeTZ)

    curr_time = datetime.now(homeTZ)

    if prev_time is not None and cached_feeds is not None and (curr_time - prev_time).total_seconds() < 120:
        return cached_feeds

    print("here")
    prev_time = datetime.now(homeTZ)
    cached_feeds = feedparser.parse(url)
    return cached_feeds


if __name__ == '__main__':
    app.run(port=5000, debug=True)
