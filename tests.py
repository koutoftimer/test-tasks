# -*- encoding: utf-8 -*-
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


class TestReplace(object):
    def test_doctype(self):
        assert replace(HTML_WITH_DOCTYPE) == HTML_WITH_DOCTYPE
