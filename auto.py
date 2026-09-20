import os as _os
_os.environ["PATH"] = "/home/userapp/appvideos/scripts/env/bin:" + _os.environ.get("PATH", "")
# Maestro: escolhe a URL, processa e publica o Short
import subprocess, sys
from datetime import datetime
from pathlib import Path
import yt_dlp

BASE = Path(__file__).parent
PY = BASE / "env/bin/python"
HASHTAGS = "#shorts #curiosidades #Animais #Plantas #interessnte #Biologia #feed #Animaisinteressantes"
MAX_FALHAS = 2      # tentativas por URL antes de descartar
DURACAO_MIN = 90    # ignora vídeos mais curtos que isso (segundos)


def log(*a):
    print(f"[{datetime.now():%d/%m %H:%M:%S}]", *a, flush=True)


def lista(nome):
    p = BASE / nome
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text().splitlines() if l.strip()]


def anexar(nome, linha):
    with open(BASE / nome, "a") as f:
        f.write(linha + "\n")


def registrar(url):
    anexar("dados/feito.txt", url)


def falha(url, motivo):
    anexar("dados/falhas.txt", url)
    n = lista("dados/falhas.txt").count(url)
    log(f"Falha {n}/{MAX_FALHAS} ({motivo}): {url}")
    if n >= MAX_FALHAS:
        log("Descartando URL após falhas repetidas.")
        registrar(url)


def info(url):
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "cookiefile": str(BASE / "segredos" / "cookies.txt")}
    with yt_dlp.YoutubeDL(opts) as y:
        return y.extract_info(url, download=False)


def limpar_titulo(t):
    return t.replace("<", "").replace(">", "").strip()[:80]


def credito_gameplay():
    gf = BASE / "dados/gameplay_usado.txt"
    if not gf.exists():
        return ""
    gid = gf.read_text().strip()
    if not gid:
        return ""
    for l in lista("gameplays/creditos.txt"):
        if l.startswith(gid + "|"):
            _, canal, link = (l.split("|", 2) + ["", ""])[:3]
            return f"Gameplay: {canal} ({link})\n"
    return ""


def main():
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    postados = 0
    feitos = set(lista("dados/feito.txt"))
    video = BASE / "video_final.mp4"

    for url in lista("dados/fontes.txt"):
        if postados >= limite:
            break
        if url in feitos:
            continue

        try:
            i = info(url)
        except Exception as e:
            falha(url, f"não consegui ler: {str(e)[:80]}")
            continue

        if i.get("is_live") or i.get("live_status") in ("is_live", "is_upcoming"):
            log("Ignorado (ao vivo):", url)
            registrar(url)
            continue
        if (i.get("duration") or 0) < DURACAO_MIN:
            log("Ignorado (muito curto):", url)
            registrar(url)
            continue
        if "creative commons" not in (i.get("license") or "").lower():
            log("Ignorado (sem licença CC):", url)
            registrar(url)
            continue

        idioma = (i.get("language") or "").lower()
        orig = [k.lower() for k in (i.get("automatic_captions") or {}) if k.endswith("-orig")]
        fala = idioma or (orig[0] if orig else "")
        if fala and not fala.startswith("pt"):
            log(f"Ignorado (idioma {fala}):", url)
            registrar(url)
            continue

        log("Processando:", i.get("title"))
        r = subprocess.run(["bash", str(BASE / "orquestrador.sh"), url], cwd=BASE)
        if r.returncode == 5:
            log("Ignorado (áudio não está em português):", url)
            registrar(url)
            continue
        if r.returncode != 0 or not video.exists():
            falha(url, "processamento")
            continue

        titulo = f"{limpar_titulo(i['title'])} #shorts #podcast"
        desc = (
            f"Fonte: {i['title']} - {i.get('uploader', '')} ({url})\n"
            f"{credito_gameplay()}"
            "Licença: Creative Commons (reuso permitido).\n\n" + HASHTAGS
        )

        r = subprocess.run([str(PY), "uploader.py", str(video), titulo, desc], cwd=BASE)
        if r.returncode == 2:
            log("Token inválido/expirado. Rode auth.py de novo (com o túnel SSH).")
            sys.exit(2)
        if r.returncode != 0:
            log("Falha no upload (a URL não foi descartada):", url)
            sys.exit(1)

        registrar(url)
        video.unlink(missing_ok=True)
        postados += 1
        log("OK:", url)

    log(f"{postados} vídeo(s) postado(s) nesta execução." if postados else "Nada postado nesta execução.")


main()
