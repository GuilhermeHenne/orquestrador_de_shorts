# Coleta de midias (Pexels, Pixabay, Commons) e geracao de voz (Edge TTS)
import json, random, re, subprocess, sys, urllib.parse
from pathlib import Path
from commons import foto_como_clipe, video_commons, duracao
from pixabay import video_pixabay

BASE = Path(__file__).parent
TRABALHO = BASE / "trabalho"
ENV_FILE = BASE / "segredos" / ".env"
VOZ = "pt-BR-AntonioNeural"
FILLER = "nature landscape"


def carregar_env():
    chaves = {}
    if ENV_FILE.exists():
        for linha in ENV_FILE.read_text().splitlines():
            if "=" in linha:
                k, v = linha.split("=", 1)
                chaves[k.strip()] = v.strip()
    return chaves


def baixar_video_pexels(query, api_key, indice, creditos, exato):
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=15"
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: {api_key}", url], capture_output=True, text=True)
    try:
        dados = json.loads(r.stdout)
    except Exception:
        return False
    videos = dados.get("videos") or []
    if exato:
        chaves = [w for w in re.findall(r"[a-z]+", query.lower()) if len(w) > 3]
        videos = [v for v in videos if all(w in v.get("url", "").lower() for w in chaves)]
    if not videos:
        return False
    video = random.choice(videos)
    arquivos = video["video_files"]
    hd = [f for f in arquivos if f.get("quality") == "hd"]
    link = (hd or arquivos)[0]["link"]
    destino = TRABALHO / f"cena_{indice}.mp4"
    subprocess.run(["curl", "-s", "-L", "-o", str(destino), link])
    if not destino.exists() or destino.stat().st_size < 50_000:
        return False
    creditos.append(f"Vídeo: {video.get('user', {}).get('name', 'Pexels')} ({video.get('url', 'pexels.com')})")
    print(f"[{indice}] Pexels: {video.get('url')}")
    return True


def gerar_audio(texto, indice):
    destino = TRABALHO / f"cena_{indice}.mp3"
    subprocess.run(["edge-tts", "--voice", VOZ, "--text", texto, "--write-media", str(destino)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return destino.exists() and destino.stat().st_size > 1000


def obter_midia(termos, indice, creditos, chaves):
    destino = TRABALHO / f"cena_{indice}.mp4"
    for q in termos:
        if not q:
            continue
        if baixar_video_pexels(q, chaves.get("PEXELS_API_KEY", ""), indice, creditos, True):
            return True
    pk = chaves.get("PIXABAY_API_KEY")
    if pk and pk != "troque_aqui":
        for q in termos:
            if q and video_pixabay(q, pk, indice, creditos, destino):
                return True
    for q in termos:
        if q and video_commons([q], destino, indice, creditos):
            return True
    dur = duracao(TRABALHO / f"cena_{indice}.mp3")
    cred = foto_como_clipe(termos, destino, dur)
    if cred:
        creditos.append(cred)
        print(f"[{indice}] Commons (foto): usada como clipe com zoom.")
        return True
    return False


def main():
    chaves = carregar_env()
    if not chaves.get("PEXELS_API_KEY") or chaves["PEXELS_API_KEY"] == "troque_aqui":
        sys.exit("Erro: chave do Pexels nao configurada.")
    arq = TRABALHO / "roteiro.json"
    if not arq.exists():
        sys.exit("Erro: roteiro.json nao encontrado.")
    for f in list(TRABALHO.glob("cena_*")) + [TRABALHO / "lista.txt", TRABALHO / "legenda.srt"]:
        f.unlink(missing_ok=True)
    roteiro = json.loads(arq.read_text(encoding="utf-8"))
    creditos, especificas = [], 0
    for i, cena in enumerate(roteiro["cenas"], start=1):
        if not gerar_audio(cena["texto"], i):
            sys.exit(f"Erro: falhou a narracao da cena {i}.")
        termos = [cena.get("busca"), cena.get("busca_fallback"),
                  cena.get("cientifico") or roteiro.get("cientifico"),
                  cena.get("titulo_item") or roteiro.get("tema")]
        termos = [t for t in dict.fromkeys(termos) if t and t != "wildlife"]
        if obter_midia(termos, i, creditos, chaves):
            especificas += 1
        elif not baixar_video_pexels(FILLER, chaves.get("PEXELS_API_KEY", ""), i, creditos, False):
            sys.exit(f"Erro: sem video para a cena {i}.")
    if especificas < max(3, len(roteiro["cenas"]) - 2):
        print(f"Apenas {especificas}/{len(roteiro['cenas'])} cenas com mídia específica. Tema pulado.")
        sys.exit(3)
    (TRABALHO / "creditos.txt").write_text("; ".join(sorted(set(creditos))), encoding="utf-8")
    print("Midias prontas.")


if __name__ == "__main__":
    main()
