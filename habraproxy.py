# ~*~ encoding: utf-8 ~*~
import argparse
import bs4
import re
import requests

from urllib import urlencode
from urlparse import urljoin, urlparse

from flask import Flask, Response, stream_with_context, request


app = Flask(__name__)
app.HOST = 'http://habrahabr.ru'
app.DOMAIN = None


ALLOWED_CONTENT_TYPES = ('text/html', 'text/xml', 'text/xhtml', 'text/plain')
WORD_RE = re.compile(r'(?P<prefix>^|\W)(?P<word>\w{6})(?P<suffix>$|\W)',
                     re.UNICODE)
WORD_REPLACEMENT = u'\g<prefix>\g<word>™\g<suffix>'


def html_content_type(content_type):
    """
    Determine whether `content_type` is subset of xml or plain text.

    :type content_type: str
    :rtype: bool
    """
    return any(map(content_type.count, ALLOWED_CONTENT_TYPES))


def replace(text):
    html = bs4.BeautifulSoup(text, 'html5lib')
    for line in html.find_all(text=True):
        if not isinstance(line, bs4.element.PreformattedString):
            line.replace_with(WORD_RE.sub(WORD_REPLACEMENT, line))
    return html.prettify(formatter='html')


@app.route('/<path:url>')
def home(url):
    headers = {k: v for k, v in request.headers if v}
    headers.update({'Host': app.DOMAIN})
    url = ''.join([urljoin(app.HOST, url), urlencode(request.args)])
    response = requests.get(
        url, stream=True, headers=headers, cookies=request.cookies)

    if not html_content_type(response.headers['content-type']) or \
            response.status_code >= 300:
        return Response(stream_with_context(response.iter_content()),
                        content_type=response.headers['content-type'])
    return replace(response.text)


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

    app.DOMAIN = urlparse(app.HOST).netloc
    app.run()

