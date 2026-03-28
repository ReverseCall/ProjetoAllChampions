import re

# Converte qualquer variação do nome de um campeão para o slug
def slugify_champion(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[''`]", "", s)
    s = s.replace("&", "-")
    s = s.replace(".", "")
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-{2,}", "-", s)
    s = s.strip("-")

    return s