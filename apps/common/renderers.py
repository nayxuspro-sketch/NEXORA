from rest_framework.renderers import BaseRenderer


class PassthroughBinaryRenderer(BaseRenderer):
    """
    Renderer that accepts application/pdf, binary octet-streams and wildcard */* without error.
    """
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
