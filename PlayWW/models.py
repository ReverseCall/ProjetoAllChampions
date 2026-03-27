import uuid
import hashlib
from django.db import models
from django.utils import timezone


class Champion(models.Model):
    name = models.CharField(max_length=100, unique=True)
    vote_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-vote_count']

    def __str__(self):
        return self.name


# Salva algumas informações sobre quem esta usando o site.
class VoterSession(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    ip_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['ip_hash', 'last_seen'])]

    @staticmethod
    def hash_ip(ip: str) -> str:
        return hashlib.sha256(ip.encode()).hexdigest()

    def get_votes_ordered(self):
        # Retorna os votos ordenados por posição (1, 2, 3)
        return self.votes.select_related('champion').order_by('vote_order')
    

# Sistema de registro de votos, {1} max {4}!
class Vote(models.Model):
    session = models.ForeignKey(
        VoterSession, on_delete=models.CASCADE, related_name='votes'
    )
    champion = models.ForeignKey(
        Champion, on_delete=models.CASCADE, related_name='vote_records'
    )
    vote_order = models.PositiveSmallIntegerField()  # 1, 2 ou 3
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Uma sessão não pode ter dois votos
        unique_together = [('session', 'vote_order')]

        # Uma sessão não pode votar duas vezes no mesmo campeão
        unique_together = [('session', 'champion'), ('session', 'vote_order')]
        indexes = [models.Index(fields=['session', 'vote_order'])]


# Sistema de segurança para evitar span de votos falsos (pfv funciona agora DX)
class DailyVoteStat(models.Model):
    date = models.DateField(unique=True)
    vote_count = models.PositiveIntegerField(default=0)
    flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        flag = " [FLAGGED]" if self.flagged else ""
        return f"{self.date}: {self.vote_count} votos{flag}"

    @classmethod
    def increment_today(cls):
        today = timezone.now().date()
        obj, _ = cls.objects.get_or_create(date=today, defaults={'vote_count': 0})
        cls.objects.filter(pk=obj.pk).update(
            vote_count=models.F('vote_count') + 1
        )
        # Verifica anomalia após incrementar
        obj.refresh_from_db()
        cls._check_anomaly(obj)

    @classmethod
    def _check_anomaly(cls, today_stat):
        # Verificação dos ultimos 7 dias, verifica se o total do dia e X5 maior
        from django.db.models import Avg

        if today_stat.flagged:
            return  # Já foi sinalizado, não precisa checar de novo

        # Pega a média dos 7 dias anteriores (exclui o proprio dia)
        week_stats = cls.objects.filter(
            date__lt=today_stat.date
        ).order_by('-date')[:7]

        week_avg = week_stats.aggregate(avg=Avg('vote_count'))['avg']

        # Precisa de pelo menos 3 dias de histórico e um mínimo de 5 votos/dia
        if week_avg is None or week_avg < 5 or week_stats.count() < 3:
            return

        threshold = week_avg * 5
        if today_stat.vote_count >= threshold:
            cls.objects.filter(pk=today_stat.pk).update(
                flagged=True,
                flag_reason=(
                    f"Votos hoje ({today_stat.vote_count}) "
                    f"excedem 5x a média semanal ({week_avg:.1f})"
                )
            )