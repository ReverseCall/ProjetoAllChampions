from django.conf.urls.static import static
from django.conf import settings
from . views import Home, status, urls_json, ViewsChapions, api_vote, api_vote_state #, teste
from . import mod_views
from django.urls import path

urlpatterns = [
    path('', Home, name="home"),
    #path('teste', teste, name="test"),
    path('status/', status, name="status"),
    path("urls.json/", urls_json),
    path("vote/<str:name>/", api_vote, name="api_vote"),

    path("vote/<str:name>/state/", api_vote_state, name="api_vote_state"),path("moderacao/",           mod_views.mod_painel, name="mod_painel"),
    path("moderacao/login/", mod_views.mod_login,  name="mod_login"),
    path("moderacao/logout/", mod_views.mod_logout, name="mod_logout"),
    path("moderacao/aprovar/<int:stat_id>/", mod_views.mod_aprovar, name="mod_aprovar"),
    path("moderacao/limpar/<int:stat_id>/", mod_views.mod_limpar,  name="mod_limpar"),
    # API
    path("<str:name>", ViewsChapions, name="bonecos")
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )