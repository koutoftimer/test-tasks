import orjson
from rest_framework.renderers import JSONRenderer


class FastJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        option = None
        indent = self.get_indent(accepted_media_type, renderer_context)
        if indent is not None:
            option = orjson.OPT_INDENT_2
        return orjson.dumps(data, option=option)
