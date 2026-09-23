# Busca de video no Pixabay (licenca propria, sem exigencia de credito por clipe)
import json, random, re, subprocess, urllib.parse
from pathlib import Path

PALAVRAS_FRACAS = {"water", "group", "close", "nature", "wildlife", "landscape"}


def buscar(query, api_key, exigir_termos=True):
    q = urllib.parse.quote_plus(query)
    url = f"https://pixabay.com/api/videos/?key={api_key}&q={q}&per_page=20&safesearch=true"
    r = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        hits = json.loads(r.stdout).get("hits", [])
    except Exception:
        return []
    if not exigir_termos:
        return hits
    chaves = [w for w in re.findall(r"[a-z]+", query.lower()) if len(w) > 3 and w not in PALAVRAS_FRACAS]
    return [h for h in hits if all(w in (h.get("tags", "") + " " + str(h.get("id"))).lower() for w in chaves)]


def video_pixabay(query, api_key, indice, creditos, saida):
    hits = buscar(query, api_key)
    if not hits:
        return False
    v = random.choice(hits)
    videos = v.get("videos", {})
    link = (videos.get("large") or videos.get("medium") or {}).get("url")
    if not link:
        return False
    subprocess.run(["curl", "-s", "-L", "-o", str(saida), link])
    if not saida.exists() or saida.stat().st_size < 50_000:
        return False
    creditos.append(f"Vídeo: Pixabay (pixabay.com/videos/id-{v.get('id')})")
    print(f"[{indice}] Pixabay: id {v.get('id')}")
    return True
