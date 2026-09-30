import os
from django.http import FileResponse, Http404
from django.views import View

ALLOWED_FILES = {
    'installer-correctif-pdf.bat': '/home/user/NEXORA/installer-correctif-pdf.bat',
    'update_windows.bat': '/home/user/NEXORA/update_windows.bat',
    'NEXORA-PATCH-PDF-FIX.zip': '/home/user/NEXORA/NEXORA-PATCH-PDF-FIX.zip',
    'NEXORA-UPDATE-v1.3.9.zip': '/home/user/NEXORA/NEXORA-UPDATE-v1.3.9.zip',
}

class ServeDownloadFileView(View):
    def get(self, request, filename, *args, **kwargs):
        if filename not in ALLOWED_FILES:
            raise Http404("Fichier non autorise.")
        
        path = ALLOWED_FILES[filename]
        if not os.path.exists(path):
            raise Http404("Fichier introuvable sur le disque.")
            
        content_type = 'application/x-bat' if filename.endswith('.bat') else 'application/zip'
        response = FileResponse(open(path, 'rb'), content_type=content_type, as_attachment=True, filename=filename)
        response['Content-Length'] = os.path.getsize(path)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Access-Control-Allow-Origin'] = '*'
        return response
