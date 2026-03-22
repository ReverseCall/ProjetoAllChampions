from django.http import HttpResponseForbidden, Http404
from django.shortcuts import render
from django.conf import settings

from django.shortcuts import redirect
from django.http import HttpResponse
from django.http import JsonResponse
import json
import os

# Create your views here.

def Home(request):
    #index = "site.html"
    # return render(request, index)
    return redirect("/warwick/")


def ViewsChapions(request, name):
    index = f"{name}.html"
    list_all_campeao = ["aatrox", "zac", "warwick", "yorick"]
    create_page = ["warwick"]

    if name not in list_all_campeao:
        raise Http404()

    if name not in create_page:
        return HttpResponse(f"<h1 style='display: flex; justify-content: center; text-align: center;'>*pagina .html bem fazida*<br>a pagina para o campeão {name} ainda não foi criada :'c</h1>")
    
    return render(request, index)


def teste(request):
    index = "teste.html"

    return render(request, index)

def status(request):
    if request.get_host().split(':')[0] not in ('127.0.0.1', 'localhost', 'loscomedyhub.qzz.io'):
        return HttpResponseForbidden("Acesso negado")
    
    index = "status.html"

    context = {
        'ambiente': 'DEV' if settings.ATUALIZANDO else 'PRODUÇÃO',
        'ambiente_class': 'ok' if settings.ATUALIZANDO else 'warn',
        'atualizando': settings.ATUALIZANDO,
        'debug': settings.DEBUG,
        'whitenoise': any(
            'whitenoise.middleware.WhiteNoiseMiddleware' in m
            for m in settings.MIDDLEWARE
        ),
    }

    return render(request, index, context)


def urls_json(request):
    path = os.path.join(settings.BASE_DIR, "comedyhub", "urls.json")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return JsonResponse(data, safe=False)