# ~*~ encoding: utf-8 ~*~
from __future__ import unicode_literals

import aiohttp
import asyncio
import argparse
import bs4
import re

from aiohttp.web import Application
from urllib.parse import urljoin, urlparse


ALLOWED_CONTENT_TYPES = ('text/html', 'text/xml', 'text/xhtml', 'text/plain')
DISALLOWED_TAGS = {'script', 'style', 'noscript'}
DOMAIN = None
HOST = 'http://habrahabr.ru/'
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


def current_host(href):
    return href and href.startswith(HOST)


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
    for link_node in html.find_all('a', href=current_host):
        link_node.attrs['href'] = urljoin(
            '/', link_node.attrs['href'][len(HOST):])
    return html.prettify(formatter='html')


async def home(request):
    headers = {**request.headers, 'Host': DOMAIN}
    url = urljoin(HOST, request.path_qs)
    response = await aiohttp.get(url, headers=headers)
    if (not html_content_type(response.headers['content-type']) or
            response.status >= 300):
        return aiohttp.web.Response(
            body=await response.read(),
            content_type=response.headers['content-type'])
    return aiohttp.web.Response(
        text=replace(await response.text()),
        content_type=response.headers['content-type'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Site host name, including protocol: '
                                       'http://host, https://host')
    args = parser.parse_args()
    if args.host:
        global HOST
        HOST = args.host
    global DOMAIN
    DOMAIN = urlparse(HOST).netloc

    app = Application()
    app.router.add_route('GET', '/{url:[\w\W]*}', home)
    handler = app.make_handler()

    loop = asyncio.get_event_loop()
    f = loop.create_server(handler, '0.0.0.0', 5000)
    srv = loop.run_until_complete(f)
    print('Running at', srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(handler.finish_connections(1.))
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.finish())
        loop.close()
