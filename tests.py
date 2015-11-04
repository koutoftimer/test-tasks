# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from habraproxy import replace


HTML_WITH_DOCTYPE = '''<!DOCTYPE html>
<html lang="en">
 <head>
  <meta charset="utf-8"/>
  <title>
   Title
  </title>
 </head>
 <body>
  <span>
   Content
  </span>
 </body>
</html>'''


HTML_WITH_SCRIPT_TAG = '''<html lang="en">
 <head>
  <script>
   Math.random()
  </script>
 </head>
 <body>
 </body>
</html>'''


HTML_WITH_STYLE_TAG = '''<html lang="en">
 <head>
  <style>
   button { height: 40px; }
  </style>
 </head>
 <body>
 </body>
</html>'''


HTML_WITH_COMMENT_TAG = '''<html lang="en">
 <head>
  <!--[if IE]>
   <link rel="stylesheet" type="text/css" href="all-ie-only.css" />
  <![endif]-->
 </head>
 <body>
 </body>
</html>'''


HTML_WITH_BUTTON_TAG = '''<html lang="en">
 <head>
 </head>
 <body>
  <button>
   Send
  </button>
 </body>
</html>'''


HTML_WITH_NOSCRIPT_TAG = '''<html lang="en">
 <head>
 </head>
 <body>
  <noscript>
   abcdef
  </noscript>
 </body>
</html>'''


class TestReplace(object):
    def test_doctype(self):
        assert replace(HTML_WITH_DOCTYPE) == HTML_WITH_DOCTYPE

    def test_script_tag(self):
        assert replace(HTML_WITH_SCRIPT_TAG) == HTML_WITH_SCRIPT_TAG

    def test_style_tag(self):
        assert replace(HTML_WITH_STYLE_TAG) == HTML_WITH_STYLE_TAG

    def test_comment_tag(self):
        assert replace(HTML_WITH_COMMENT_TAG) == HTML_WITH_COMMENT_TAG

    def test_button_tag(self):
        assert replace(HTML_WITH_BUTTON_TAG) == HTML_WITH_BUTTON_TAG

    def test_noscript_tag(self):
        assert replace(HTML_WITH_NOSCRIPT_TAG) == HTML_WITH_NOSCRIPT_TAG
