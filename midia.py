# Coleta de midias (Pexels) e geracao de voz (Edge TTS)
import json, random, re, subprocess, sys, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent
TRABALHO = BASE / "trabalho"
ENV_FILE = BASE / "segredos" / ".env"
VOZ = "pt-BR-AntonioNeural"
FILLER = "nature landscape"
USADOS = set()
PALAVRAS_FRACAS = {"water", "group", "close", "nature", "wildlife", "landscape"}


def carregar_env():
    if ENV_FILE.exists():
        for linha in ENV_FILE.read_text().splitlines():
            if linha.startswith("PEXELS_API_KEY="):
                return linha.split("=", 1)[1].strip()
    return None


def baixar_video_pexels(query, api_key, indice, creditos, exato):
    print(f"[{indice}] Pexels: '{query}' ({'especifico' if exato else 'paisagem'})")
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=15"
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: {api_key}", url], capture_output=True, text=True)
    try:
        dados = json.loads(r.stdout)
    except Exception:
        print(f"[{indice}] Resposta invalida: {r.stdout[:100]}")
        return False
    videos = dados.get("videos") or []
    if exato:
        chaves = [w for w in re.findall(r"[a-z]+", query.lower()) if len(w) > 3 and w not in PALAVRAS_FRACAS]
        videos = [v for v in videos if all(w in v.get("url", "").lower() for w in chaves)]
    if not videos:
        print(f"[{indice}] Nenhum resultado relevante.")
        return False
    videos = [v for v in videos if v.get("url") not in USADOS] or videos
    video = random.choice(videos)
    USADOS.add(video.get("url"))
    print(f"[{indice}] usando: {video.get('url')}")
    arquivos = video["video_files"]
    hd = [f for f in arquivos if f.get("quality") == "hd"]
    link = (hd or arquivos)[0]["link"]
    destino = TRABALHO / f"cena_{indice}.mp4"
    subprocess.run(["curl", "-s", "-L", "-o", str(destino), link])
    if not destino.exists() or destino.stat().st_size < 50_000:
        return False
    creditos.append(f"{video.get('user', {}).get('name', 'Pexels')} ({video.get('url', 'pexels.com')})")
    return True


def gerar_audio(texto, indice):
    destino = TRABALHO / f"cena_{indice}.mp3"
    subprocess.run(["edge-tts", "--voice", VOZ, "--text", texto, "--write-media", str(destino)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return destino.exists() and destino.stat().st_size > 1000


def main():
    api_key = carregar_env()
    if not api_key or api_key == "troque_aqui":
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
        achou = any(q and baixar_video_pexels(q, api_key, i, creditos, True)
                    for q in (cena.get("busca"), cena.get("busca_fallback")))
        if achou:
            especificas += 1
        elif not baixar_video_pexels(FILLER, api_key, i, creditos, False):
            sys.exit(f"Erro: sem video para a cena {i}.")
    if especificas < 3:
        print(f"Apenas {especificas}/5 cenas com imagens da especie. Tema pulado.")
        sys.exit(3)
    (TRABALHO / "creditos.txt").write_text("; ".join(sorted(set(creditos))), encoding="utf-8")
    print("Midias prontas.")


if __name__ == "__main__":
    main()
