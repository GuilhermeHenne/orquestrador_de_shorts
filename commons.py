# Fotos de especies no Wikimedia Commons (licencas livres) -> clipe vertical com zoom lento
import json, re, subprocess, urllib.parse, urllib.request
from pathlib import Path

UA = {"User-Agent": "orquestrador-de-shorts/0.1 (https://github.com/GuilhermeHenne/orquestrador_de_shorts)"}
LICENCA_OK = re.compile(r"(cc0|public domain|pdm|cc by \d)", re.I)  # exclui BY-SA e NC
USADAS = set()


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def _limpo(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def duracao(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 8.0


def _candidatas(termo):
    q = urllib.parse.quote(f"{termo} filetype:bitmap")
    url = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6"
           f"&gsrsearch={q}&gsrlimit=50&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize%7Cmime"
           "&iiurlwidth=2000&format=json")
    paginas = (_get(url).get("query") or {}).get("pages") or {}
    chaves = [w for w in re.findall(r"[a-zà-ÿ]+", termo.lower()) if len(w) > 3]
    saida = []
    for p in paginas.values():
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        lic = _limpo((meta.get("LicenseShortName") or {}).get("value"))
        if not LICENCA_OK.match(lic) or info.get("mime") != "image/jpeg" or info.get("width", 0) < 1200:
            continue
        texto = (p.get("title", "") + " " + _limpo((meta.get("ImageDescription") or {}).get("value"))).lower()
        if chaves and not all(w in texto for w in chaves):
            continue
        artista = _limpo((meta.get("Artist") or {}).get("value")) or "autor desconhecido"
        pagina = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_"))
        saida.append((p["title"], info.get("thumburl") or info["url"], f"{artista[:60]} / Wikimedia Commons, {lic} ({pagina})"))
    return saida


def foto_como_clipe(termos, saida, dur):
    for termo in termos:
        try:
            cands = [c for c in _candidatas(termo) if c[0] not in USADAS]
        except Exception as e:
            print("Commons: erro na busca:", e)
            continue
        for titulo, url, credito in cands[:6]:
            foto = Path(saida).with_suffix(".jpg")
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                    foto.write_bytes(r.read())
                frames = int((dur + 0.5) * 30)
                vf = ("crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1620:2880,"
                      f"zoompan=z='min(zoom+0.0006,1.25)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30")
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(foto), "-vf", vf,
                                "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                                "-preset", "veryfast", str(saida)], check=True)
                foto.unlink(missing_ok=True)
                USADAS.add(titulo)
                print(f"Commons: {titulo}")
                return credito
            except Exception as e:
                print("Commons: falhou com", titulo, e)
    return None
