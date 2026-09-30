import os
from django.http import FileResponse, Http404, HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class DirectZipDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Chercher en priorité l'archive certifiée la plus récente
        candidates = [
            "/home/user/NEXORA/NEXORA-CERTIFIED-RELEASE-LATEST.zip",
            "/home/user/NEXORA/nexora-latest.zip"
        ]
        zip_path = None
        for p in candidates:
            if os.path.exists(p):
                zip_path = p
                break

        if not zip_path:
            raise Http404("Le fichier ZIP d'installation n'est pas disponible.")

        filename = os.path.basename(zip_path)
        response = FileResponse(
            open(zip_path, 'rb'),
            as_attachment=True,
            filename=filename,
            content_type='application/zip'
        )
        response['Content-Length'] = os.path.getsize(zip_path)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

class CertificationManifestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        manifest_path = "/home/user/NEXORA/CERTIFICATION_MANIFEST.txt"
        if not os.path.exists(manifest_path):
            raise Http404("Manifeste introuvable.")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain; charset=utf-8')
