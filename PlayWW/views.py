import os
import json
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
from .utils import slugify_champion
from django.shortcuts import redirect
from django.db import transaction, models
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseForbidden, Http404
from .models import Champion, Vote, VoterSession, DailyVoteStat
from django.views.decorators.http import require_GET, require_POST


SESSION_COOKIE_NAME = "voter_uuid"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
MAX_VOTES = 3
MAX_TOTAL_VOTES = 9999  # Limite global de votos


# Pega o IP real considerando proxies
def get_client_ip(request) -> str:
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


# Def par arecuperar a sessão do usuario
def get_or_create_session(request) -> VoterSession:
    voter_uuid = request.COOKIES.get(SESSION_COOKIE_NAME)
    ip = get_client_ip(request)
    ip_hash = VoterSession.hash_ip(ip)
 
    # 1. Tenta pelo cookie
    if voter_uuid:
        try:
            session = VoterSession.objects.get(uuid=voter_uuid)
            VoterSession.objects.filter(pk=session.pk).update(last_seen=timezone.now())
            return session
        except (VoterSession.DoesNotExist, ValueError):
            pass
 
    # 2. Tenta pelo IP
    cutoff = timezone.now() - timedelta(days=7)
    ip_sessions = VoterSession.objects.filter(
        ip_hash=ip_hash, last_seen__gte=cutoff
    )
    if ip_sessions.count() == 1:
        session = ip_sessions.first()
        VoterSession.objects.filter(pk=session.pk).update(last_seen=timezone.now())
        return session
 
    # 3. Cria nova sessão
    return VoterSession.objects.create(ip_hash=ip_hash)


# Define o cookie UUID na resposta
def set_session_cookie(response, session: VoterSession) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        str(session.uuid),
        max_age=SESSION_COOKIE_AGE,
        httponly=True,
        samesite="Lax",
        secure=not settings.DEBUG,
    )
 
 
# Serializa os votos da sessão para
def serialize_votes(session: VoterSession) -> list:
    return [
        {"vote_order": v.vote_order, "champion": v.champion.name}
        for v in session.get_votes_ordered()
    ]


def Home(request):
    #index = "site.html"
    # return render(request, index)
    return redirect("/warwick")


def ViewsChapions(request, name):
    # Paginas HTMls
    PaginaGuia = "guiaDeContribuicao.html"
    canonical_slug = slugify_champion(name)
    create_page = ["warwick"] # lista com paginas criadas.
 
    # Se a URL não está no formato esperado, redireciona
    if name != canonical_slug:
        return redirect("champion", name=canonical_slug, permanent=True)
 
    # Busca pelo slug
    try:
        champion = Champion.objects.get(slug=canonical_slug)
    except Champion.DoesNotExist:
        raise Http404()
 
    if champion.slug not in create_page:
        session = get_or_create_session(request)
        current_votes = serialize_votes(session)
 
        context = {
            "nome": champion.name,   # nome de exibição do campeão
            "slug": champion.slug,   # nome que aparece na URL
            "total_votos": champion.vote_count,
            "meus_votos_json": json.dumps(current_votes),
        }
        response = render(request, PaginaGuia, context=context)
        set_session_cookie(response, session)
        return response
 
    return render(request, f"{champion.slug}.html")


# URl de testes para novas paginas e projetos.
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


# === API CORE ===

@require_POST
@csrf_protect
# Registra um voto para o campeão
def api_vote(request, name):
    try:
        champion = Champion.objects.get(name=name)
    except Champion.DoesNotExist:
        return JsonResponse({"error": "Campeão não encontrado"}, status=404)
 
    # Verifica limite global
    if champion.vote_count >= MAX_TOTAL_VOTES:
        return JsonResponse(
            {"error": "Este campeão atingiu o limite máximo de votos"}, status=400
        )
 
    session = get_or_create_session(request)
 
    with transaction.atomic():
        current_votes = list(session.get_votes_ordered())
 
        # Verifica se já votou neste campeão
        voted_champions = [v.champion_id for v in current_votes]
        if champion.id in voted_champions:
            return JsonResponse(
                {"error": "Você já votou neste campeão", "already_voted": True},
                status=400
            )
 
        if len(current_votes) < MAX_VOTES:
            # Ainda tem espaço — só adiciona
            new_order = len(current_votes) + 1
            Vote.objects.create(
                session=session, champion=champion, vote_order=new_order
            )
            Champion.objects.filter(pk=champion.pk).update(
                vote_count=models.F("vote_count") + 1
            )
        else:
            # 3 votos. remove o mais antigo (order=1), sobe os demais
            oldest = current_votes[0]  # vote_order=1
            Champion.objects.filter(pk=oldest.champion_id).update(
                vote_count=models.F("vote_count") - 1
            )
            oldest.delete()
 
            # Sobe a ordem: 2→1, 3→2
            for vote in current_votes[1:]:
                Vote.objects.filter(pk=vote.pk).update(
                    vote_order=vote.vote_order - 1
                )
 
            # Adiciona novo na posição 3
            Vote.objects.create(
                session=session, champion=champion, vote_order=MAX_VOTES
            )
            Champion.objects.filter(pk=champion.pk).update(
                vote_count=models.F("vote_count") + 1
            )
 
        # Atualiza estatísticas diárias e verifica anomalia
        DailyVoteStat.increment_today()
 
    # Monta resposta com estado atualizado
    champion.refresh_from_db()
    updated_votes = serialize_votes(session)
 
    response = JsonResponse({
        "success": True,
        "total_votos": champion.vote_count,
        "meus_votos": updated_votes,
    })
    set_session_cookie(response, session)
    return response
 
 
@require_GET
# Retorna o estado atual dos votos para sincronizar o frontend.
def api_vote_state(request, name):
    try:
        champion = Champion.objects.get(name=name)
    except Champion.DoesNotExist:
        return JsonResponse({"error": "Campeão não encontrado"}, status=404)
 
    session = get_or_create_session(request)
    current_votes = serialize_votes(session)
 
    response = JsonResponse({
        "total_votos": champion.vote_count,
        "meus_votos": current_votes,
    })
    set_session_cookie(response, session)
    return response