from django.contrib import admin
from django.urls import path, include
from apps.common.file_server import ServeDownloadFileView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/download-file/<str:filename>/', ServeDownloadFileView.as_view(), name='serve_file'),
    path('api/v1/', include('config.api_urls')),
]
