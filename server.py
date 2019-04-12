from flask import Flask, request, send_from_directory, Response
from flask_cors import CORS, cross_origin
import urllib
import urllib.request
import urllib.parse
import json
import feedparser

app = Flask(__name__)
CORS(app)

url = 'https://9gag-rss.com/api/rss/get?code=9GAGAwesome&format=2'

@app.route("/")
@app.route("/feeds")
def index():
    parsed = feedparser.parse(url)
    print(type(parsed))
    print(len(parsed))
    print(parsed['feed'])
    return 'Hello World'


if __name__ == '__main__':
    app.run(port=5000, debug=True)
