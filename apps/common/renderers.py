import json
from rest_framework.renderers import BaseRenderer


class PassthroughBinaryRenderer(BaseRenderer):
    """
    Renderer that accepts application/pdf, binary octet-streams and wildcard */* without error.
    Handles binary PDF streams as well as error dicts gracefully.
    """
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b''
        if isinstance(data, (bytes, bytearray, memoryview)):
            return bytes(data)
        if isinstance(data, str):
            return data.encode('utf-8')
        if isinstance(data, dict):
            # When an API exception occurs (e.g. 400, 401, 404, 500), data is a dict
            # If rendered as a raw generator without JSON encoding, Django's HttpResponse
            # iterates over dict keys ('status', 'code', 'message', 'details') resulting
            # in the string 'statuscodemessagedetails'!
            # We serialize to clean JSON bytes and adjust media_type in context if available.
            if renderer_context and 'response' in renderer_context:
                renderer_context['response']['Content-Type'] = 'application/json; charset=utf-8'
            return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        return str(data).encode('utf-8')

