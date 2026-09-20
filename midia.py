# Recolha de mídias (Pexels) e geração de voz (Edge TTS)
import json, urllib.parse, subprocess, sys
from pathlib import Path

BASE = Path(__file__).parent
TRABALHO = BASE / "trabalho"
ENV_FILE = BASE / ".env"

def carregar_env():
    if ENV_FILE.exists():
        for linha in ENV_FILE.read_text().splitlines():
            if linha.startswith("PEXELS_API_KEY="):
                return linha.split("=", 1)[1].strip()
    return None

def descarregar_video_pexels(query, api_key, indice):
    print(f"[{indice}] A pesquisar vídeo na Pexels para: '{query}'...")
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=1"
    
    # Usando curl via subprocess para driblar o bloqueio 1010 do Cloudflare
    cmd_busca = ["curl", "-s", "-H", f"Authorization: {api_key}", url]
    r = subprocess.run(cmd_busca, capture_output=True, text=True)
    
    try:
        dados = json.loads(r.stdout)
    except Exception:
        print(f"[{indice}] Erro ao ler resposta do curl: {r.stdout[:100]}")
        return False

    if "error" in dados:
        print(f"[{indice}] Pexels recusou a busca: {dados['error']}")
        return False
        
    if not dados.get("videos"):
        print(f"[{indice}] Aviso: Nenhum vídeo encontrado para este termo.")
        return False
    
    arquivos = dados["videos"][0]["video_files"]
    hd_files = [f for f in arquivos if f["quality"] == "hd"]
    url_video = hd_files[0]["link"] if hd_files else arquivos[0]["link"]
    
    caminho_video = TRABALHO / f"cena_{indice}.mp4"
    subprocess.run(["curl", "-s", "-o", str(caminho_video), url_video])
    print(f"[{indice}] Vídeo guardado com sucesso.")
    return True

def gerar_audio_tts(texto, indice):
    print(f"[{indice}] A gerar narração em pt-BR...")
    caminho_audio = TRABALHO / f"cena_{indice}.mp3"
    cmd = ["edge-tts", "--voice", "pt-BR-AntonioNeural", "--text", texto, "--write-media", str(caminho_audio)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    api_key = carregar_env()
    if not api_key or api_key == "troque_aqui":
        sys.exit("Erro: Chave da Pexels não está configurada.")

    ficheiro_roteiro = TRABALHO / "roteiro.json"
    if not ficheiro_roteiro.exists():
        sys.exit("Erro: O ficheiro roteiro.json não foi encontrado.")

    roteiro = json.loads(ficheiro_roteiro.read_text(encoding="utf-8"))
    print(f"A iniciar processamento de mídias para: {roteiro['titulo']}")
    
    for i, cena in enumerate(roteiro["cenas"], start=1):
        print(f"\n--- Processando Cena {i} ---")
        gerar_audio_tts(cena["texto"], i)
        descarregar_video_pexels(cena["busca"], api_key, i)

if __name__ == "__main__":
    main()
