from django.urls import path
from . import views

app_name = 'downloads'

urlpatterns = [
    path('', views.downloads_page, name='index'),
    path('api/download/', views.download_video, name='download_api'),
    path('api/funny-messages/', views.get_funny_messages, name='funny_messages_api'),
    path('serve/<str:filename>/', views.serve_download, name='serve_download'),
]
