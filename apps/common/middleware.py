from django.middleware.clickjacking import XFrameOptionsMiddleware


class FrameOptionsMiddleware(XFrameOptionsMiddleware):
    """
    Subclasses Django's XFrameOptionsMiddleware.
    Keeps standard SAMEORIGIN clickjacking protection for standard web pages,
    while removing X-Frame-Options or setting it permissive for PDF export
    endpoints and binary documents to ensure they preview seamlessly in embedded
    viewers and webviews.
    """
    def process_response(self, request, response):
        content_type = response.get('Content-Type', '')
        if (
            'pdf' in request.path
            or 'export' in request.path
            or 'application/pdf' in content_type
            or 'octet-stream' in content_type
        ):
            # Exempt PDF endpoints from framing restrictions
            if 'X-Frame-Options' in response:
                del response['X-Frame-Options']
            return response

        return super().process_response(request, response)
