# ~*~ encoding: utf-8 ~*~
from __future__ import unicode_literals

import argparse
import bs4
import re
import requests

from six.moves.urllib.parse import urlencode, urljoin, urlparse
from flask import Flask, Response, stream_with_context, request


app = Flask(__name__)
app.HOST = 'http://habrahabr.ru'
app.DOMAIN = None


ALLOWED_CONTENT_TYPES = ('text/html', 'text/xml', 'text/xhtml', 'text/plain')
DISALLOWED_TAGS = {'script', 'style'}
WORD_RE = re.compile(r'(?P<prefix>^|\W)(?P<word>\w{6})(?P<suffix>$|\W)',
                     re.UNICODE)
WORD_REPLACEMENT = r'\g<prefix>\g<word>™\g<suffix>'


def html_content_type(content_type):
    """
    Determine whether `content_type` is subset of xml or plain text.

    :type content_type: six.text_type
    :rtype: bool
    """
    return any(map(content_type.count, ALLOWED_CONTENT_TYPES))


def allowed(text_node):
    """
    Determine whether current node allowed for processing. Javascript and css
    stylesheets should not be processed as well as comments and other
    declarative tags.

    :type text_node: bs4.element.NavigableString
    :rtype: bool
    """
    return (
        not isinstance(text_node, bs4.element.PreformattedString)
        and text_node.name not in DISALLOWED_TAGS
        and not any(map(lambda parent: parent.name in DISALLOWED_TAGS,
                        text_node.parents))
    )


def replace(text):
    """
    Takes markup of html page and return markup with processed text nodes.

    Note: it tries to fix wrong markup using html5lib.

    :type text: six.text_type
    :rtype: six.text_type
    """
    html = bs4.BeautifulSoup(text, 'html5lib')
    for text_node in html.find_all(text=True):
        if allowed(text_node):
            text_node.replace_with(WORD_RE.sub(WORD_REPLACEMENT, text_node))
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
