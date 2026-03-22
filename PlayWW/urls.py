from django.conf.urls.static import static
from django.conf import settings
from . views import Home, status, urls_json, ViewsChapions #, teste
from django.urls import path

urlpatterns = [
    path('', Home, name="home"),
    #path('teste', teste, name="test"),
    path('status/', status, name="status"),
    path("urls.json/", urls_json),
    path("<str:name>/", ViewsChapions, name="bonecos")
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )