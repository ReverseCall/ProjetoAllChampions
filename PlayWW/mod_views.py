import json
from datetime import timedelta

from django.conf import settings
from django.db import transaction, models
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET

from .models import Champion, Vote, VoterSession, DailyVoteStat

# ──────────────────────────────────────────────────────────────
# Senha de acesso — defina no seu settings.py:
#   MODERATION_PASSWORD = "sua_senha_aqui"
# ──────────────────────────────────────────────────────────────
MODERATION_SESSION_KEY = "mod_autenticado"


def _is_authenticated(request) -> bool:
    return request.session.get(MODERATION_SESSION_KEY) is True


# ──────────────────────────────────────────────────────────────
# Login / Logout
# ──────────────────────────────────────────────────────────────

@csrf_protect
def mod_login(request):
    if _is_authenticated(request):
        return redirect("mod_painel")

    erro = None
    if request.method == "POST":
        senha = request.POST.get("senha", "")
        senha_correta = getattr(settings, "MODERATION_PASSWORD", None)

        if not senha_correta:
            erro = "MODERATION_PASSWORD não definida no settings.py."
        elif senha == senha_correta:
            request.session[MODERATION_SESSION_KEY] = True
            request.session.set_expiry(60 * 60 * 4)  # 4 horas
            return redirect("mod_painel")
        else:
            erro = "Senha incorreta."

    return render(request, "moderacao/login.html", {"erro": erro})


def mod_logout(request):
    request.session.flush()
    return redirect("mod_login")


# ──────────────────────────────────────────────────────────────
# Painel principal
# ──────────────────────────────────────────────────────────────

@require_GET
def mod_painel(request):
    if not _is_authenticated(request):
        return redirect("mod_login")

    # Dias com votos suspeitos
    flags = DailyVoteStat.objects.filter(flagged=True).order_by("-date")

    # Resumo geral
    total_flags = flags.count()
    ultimos_7 = DailyVoteStat.objects.filter(
        date__gte=timezone.now().date() - timedelta(days=7)
    ).order_by("-date")

    # Votos por campeão (top 10)
    campeoes = Champion.objects.order_by("-vote_count")[:10]

    context = {
        "flags": flags,
        "total_flags": total_flags,
        "ultimos_7": ultimos_7,
        "campeoes": campeoes,
        "hoje": timezone.now().date(),
    }
    return render(request, "moderacao/painel.html", context)


# ──────────────────────────────────────────────────────────────
# Ações sobre um dia suspeito
# ──────────────────────────────────────────────────────────────

@require_POST
@csrf_protect
def mod_aprovar(request, stat_id):
    """Marca o dia como revisado e mantém os votos."""
    if not _is_authenticated(request):
        return JsonResponse({"error": "Não autorizado"}, status=403)

    try:
        stat = DailyVoteStat.objects.get(pk=stat_id, flagged=True)
    except DailyVoteStat.DoesNotExist:
        return JsonResponse({"error": "Registro não encontrado"}, status=404)

    DailyVoteStat.objects.filter(pk=stat_id).update(
        flagged=False,
        flag_reason="✓ Revisado manualmente — votos mantidos."
    )
    return JsonResponse({"success": True, "acao": "aprovado", "data": str(stat.date)})


@require_POST
@csrf_protect
def mod_limpar(request, stat_id):
    """
    Remove todos os votos do dia suspeito e recalcula os contadores.
    Operação destrutiva — pede confirmação no frontend.
    """
    if not _is_authenticated(request):
        return JsonResponse({"error": "Não autorizado"}, status=403)

    try:
        stat = DailyVoteStat.objects.get(pk=stat_id, flagged=True)
    except DailyVoteStat.DoesNotExist:
        return JsonResponse({"error": "Registro não encontrado"}, status=404)

    # Início e fim do dia em UTC
    dia_inicio = timezone.make_aware(
        timezone.datetime.combine(stat.date, timezone.datetime.min.time())
    )
    dia_fim = dia_inicio + timedelta(days=1)

    with transaction.atomic():
        # Pega os votos do dia e conta por campeão para decrementar
        votos_do_dia = Vote.objects.filter(
            created_at__gte=dia_inicio,
            created_at__lt=dia_fim,
        ).select_related("champion")

        contagem = {}
        for voto in votos_do_dia:
            contagem[voto.champion_id] = contagem.get(voto.champion_id, 0) + 1

        # Decrementa contadores dos campeões
        for champion_id, qtd in contagem.items():
            Champion.objects.filter(pk=champion_id).update(
                vote_count=models.F("vote_count") - qtd
            )
            # Garante que não fique negativo
            Champion.objects.filter(pk=champion_id, vote_count__lt=0).update(
                vote_count=0
            )

        total_removidos = votos_do_dia.count()
        votos_do_dia.delete()

        # Atualiza o registro do dia
        DailyVoteStat.objects.filter(pk=stat_id).update(
            flagged=False,
            vote_count=0,
            flag_reason=f"✗ {total_removidos} votos removidos manualmente."
        )

    return JsonResponse({
        "success": True,
        "acao": "limpo",
        "removidos": total_removidos,
        "data": str(stat.date),
    })
