import uuid
import hashlib
from django.db import models
from django.utils import timezone
from .utils import slugify_champion




# Seletor de personagem em destaque (vai que algume bane WW né?)
class SiteConfig(models.Model):
    featured_champion = models.ForeignKey(
        'Champion',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Campeão em destaque (redirect de /)",
    )
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = "Configuração do site"
 
    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
 
    def __str__(self):
        name = self.featured_champion.name if self.featured_champion else "nenhum"
        return f"Config do site — destaque: {name}"


class Champion(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    vote_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-vote_count']

    def save(self, *args, **kwargs):
        # Garante que o slug sempre está sincronizado com o name
        if not self.slug:
            self.slug = slugify_champion(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.slug})"


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
        return self.votes.select_related('champion').order_by('vote_order')


class Vote(models.Model):
    session = models.ForeignKey(VoterSession, on_delete=models.CASCADE, related_name='votes')
    champion = models.ForeignKey(Champion, on_delete=models.CASCADE, related_name='vote_records')
    vote_order = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('session', 'champion'), ('session', 'vote_order')]
        indexes = [models.Index(fields=['session', 'vote_order'])]


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
        cls.objects.filter(pk=obj.pk).update(vote_count=models.F('vote_count') + 1)
        obj.refresh_from_db()
        cls._check_anomaly(obj)

    @classmethod
    def _check_anomaly(cls, today_stat):
        from django.db.models import Avg
        if today_stat.flagged:
            return
        week_stats = cls.objects.filter(date__lt=today_stat.date).order_by('-date')[:7]
        week_avg = week_stats.aggregate(avg=Avg('vote_count'))['avg']
        if week_avg is None or week_avg < 5 or week_stats.count() < 3:
            return
        if today_stat.vote_count >= week_avg * 5:
            cls.objects.filter(pk=today_stat.pk).update(
                flagged=True,
                flag_reason=(
                    f"Votos hoje ({today_stat.vote_count}) "
                    f"excedem 5x a média semanal ({week_avg:.1f})"
                )
            )