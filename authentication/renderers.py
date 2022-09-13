from rest_framework import renderers
import json

"""
Этот рендер рендерит данные запроса в JSONкодировку utf-8.

Стиль рендера всегда должен включать символы Unicode и отображать ответ без лишних пробелов:
"""


class UserRenderer(renderers.JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = ''
        if 'ErrorDetail' in str(data):
            response = json.dumps({'errors': data})
        else:
            response = json.dumps({'data': data})
        return response
