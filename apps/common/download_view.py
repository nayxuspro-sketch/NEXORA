import os
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class DirectZipDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        zip_path = "/home/user/NEXORA/nexora-latest.zip"
        if not os.path.exists(zip_path):
            raise Http404("Le fichier ZIP n'existe pas.")

        response = FileResponse(
            open(zip_path, 'rb'),
            as_attachment=True,
            filename='nexora-latest.zip',
            content_type='application/zip'
        )
        response['Content-Length'] = os.path.getsize(zip_path)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
