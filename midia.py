# Coleta de midias (Pexels) e geracao de voz (Edge TTS)
import json, random, subprocess, sys, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent
TRABALHO = BASE / "trabalho"
ENV_FILE = BASE / "segredos" / ".env"
VOZ = "pt-BR-AntonioNeural"


def carregar_env():
    if ENV_FILE.exists():
        for linha in ENV_FILE.read_text().splitlines():
            if linha.startswith("PEXELS_API_KEY="):
                return linha.split("=", 1)[1].strip()
    return None


def baixar_video_pexels(query, api_key, indice, creditos):
    print(f"[{indice}] Pexels: '{query}'")
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=15"
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: {api_key}", url], capture_output=True, text=True)
    try:
        dados = json.loads(r.stdout)
    except Exception:
        print(f"[{indice}] Resposta invalida: {r.stdout[:100]}")
        return False
    if "error" in dados or not dados.get("videos"):
        print(f"[{indice}] Nada encontrado.")
        return False
    video = random.choice(dados["videos"])
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
    creditos = []
    for i, cena in enumerate(roteiro["cenas"], start=1):
        if not gerar_audio(cena["texto"], i):
            sys.exit(f"Erro: falhou a narracao da cena {i}.")
        consultas = [cena.get("busca"), cena.get("busca_fallback"), "wildlife nature"]
        if not any(q and baixar_video_pexels(q, api_key, i, creditos) for q in consultas):
            sys.exit(f"Erro: sem video para a cena {i}.")
    (TRABALHO / "creditos.txt").write_text("; ".join(sorted(set(creditos))), encoding="utf-8")
    print("Midias prontas.")


if __name__ == "__main__":
    main()
