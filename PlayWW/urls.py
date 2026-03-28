from . import mod_views
from django.conf import settings
from django.urls import path, re_path
from django.conf.urls.static import static
from . views import Home, status, urls_json, ViewsChapions, api_vote, api_vote_state #, teste

urlpatterns = [
    path('', Home, name="home"),
    #path('teste', teste, name="test"),
    path('status/', status, name="status"),
    path("urls.json/", urls_json),
    path("vote/<str:name>/", api_vote, name="api_vote"),
    path("vote/<str:name>/state/", api_vote_state, name="api_vote_state"),
    path("adm", mod_views.mod_painel, name="mod_painel"),
    path("adm/login", mod_views.mod_login,  name="mod_login"),
    path("adm/logout/", mod_views.mod_logout, name="mod_logout"),
    path("adm/aprovar/<int:stat_id>/", mod_views.mod_aprovar, name="mod_aprovar"),
    path("adm/limpar/<int:stat_id>/", mod_views.mod_limpar,  name="mod_limpar"),

    # API
    path("<str:name>", ViewsChapions, name="bonecos"),

    # Formatação de URLs a prova de idiotas
    re_path(r"^(?P<name>[^/]+)$", ViewsChapions, name="champion"),
    re_path(r"^vote/(?P<name>[^/]+)$", api_vote, name="api_vote"),
    re_path(r"^vote/(?P<name>[^/]+)/state$", api_vote_state, name="api_vote_state"),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )