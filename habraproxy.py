# ~*~ encoding: utf-8 ~*~
import argparse
import requests

from bs4 import BeautifulSoup
from flask import Flask, Response, stream_with_context


app = Flask(__name__)
app.HOST = 'http://habrahabr.ru'


def processed(line):
    """
    Recives single text node for processing.
    """
    words = []
    for word in line.split(' '):
        if len(word) == 6:
            word += u'™'
        words.append(word)
    return ' '.join(words)


def replace(text):
    """
    Recives string of raw html code and returns html code with processed text
    nodes.
    """
    html = BeautifulSoup(text, 'html.parser')
    #: Retrive text nodes.
    for line in html.find_all(text=True):
        line.replace_with(processed(line))
    return str(html)


@app.route('/<path:url>')
def home(url):
    #: Downloading all content can be inefficient in case of large binnary
    #: files.
    req = requests.get('%s/%s' % (app.HOST, url), stream=True)
    #: Ommit processign for binary files, etc.
    if 'text/html' not in req.headers['content-type']:
        return Response(stream_with_context(req.iter_content()),
                        content_type=req.headers['content-type'])
    #: Process html page.
    return Response(replace(req.text))


@app.route('/')
def index():
    return home('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Site host name, including protocol: '
                                       'http://host, https://host')
    args = parser.parse_args()
    #: Configure flask app.
    if args.host:
        app.HOST = args.host

    app.run()

