# management/commands/populate_champions.py
# Execute: python manage.py populate_champions

from django.core.management.base import BaseCommand
from PlayWW.models import Champion
from PlayWW.utils import slugify_champion


class Command(BaseCommand):
    help = "Popula o banco com os campeões e seus slugs canônicos"

    # name = como aparece na UI | slug é gerado automaticamente
    CAMPEOES = ["aatrox", "ahri", "akali", "akshan", "alistar", "ambessa", "amumu", "anivia", "annie", "aphelios", "ashe", "aurelion sol", "aurora", "azir", "bard", "bel'veth", "blitzcrank", "brand", "braum", "briar", "caitlyn", "camille", "cassiopeia", "cho'gath", "corki", "darius", "diana", "dr. mundo", "draven", "ekko", "elise", "evelynn", "ezreal", "fiddlesticks", "fiora", "fizz", "galio", "gangplank", "garen", "gnar", "gragas", "graves", "gwen", "hecarim", "heimerdinger", "hwei", "illaoi", "irelia", "ivern", "janna", "jarvan iv", "jax", "jayce", "jhin", "jinx", "k'sante", "kai'sa", "kalista", "karma", "karthus", "kassadin", "katarina", "kayle", "kayn", "kennen", "kha'zix", "kindred", "kled", "kog'maw", "leblanc", "lee sin", "leona", "lillia", "lissandra", "lucian", "lulu", "lux", "malphite", "malzahar", "maokai", "master yi", "mel", "milio", "miss fortune", "mordekaiser", "morgana", "naafiri", "nami", "nasus", "nautilus", "neeko", "nidalee", "nilah", "nocturne", "nunu & willump", "olaf", "orianna", "ornn", "pantheon", "poppy", "pyke", "qiyana", "quinn", "rakan", "rammus", "rek'sai", "rell", "renata glasc", "renekton", "rengar", "riven", "rumble", "ryze", "samira", "sejuani", "senna", "seraphine", "sett", "shaco", "shen", "shyvana", "singed", "sion", "sivir", "skarner", "smolder", "sona", "soraka", "swain", "sylas", "syndra", "tahm kench", "taliyah", "talon", "taric", "teemo", "thresh", "tristana", "trundle", "tryndamere", "twisted fate", "twitch", "udyr", "urgot", "varus", "vayne", "veigar", "vel'koz", "vex", "vi", "viego", "viktor", "vladimir", "volibear", "warwick", "wukong", "xayah", "xerath", "xin zhao", "yasuo", "yone", "yorick", "yuumi", "yunara", "zaahen", "zac", "zed", "zeri", "ziggs", "zilean", "zoe", "zyra"]

    def handle(self, *args, **options):
        for name in self.CAMPEOES:
            slug = slugify_champion(name)
            obj, created = Champion.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )
            status = "criado" if created else "já existe"
            self.stdout.write(f"  {status}: {name!r} → /{slug}/")

        self.stdout.write(self.style.SUCCESS("\nConcluído."))