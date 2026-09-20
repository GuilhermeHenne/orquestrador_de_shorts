# Maestro para vídeos originais (IA): Roteiro -> Mídias -> Montagem -> Upload
import os as _os
_os.environ["PATH"] = "/home/userapp/appvideos/scripts/env/bin:" + _os.environ.get("PATH", "")
import subprocess, sys, json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
PY = BASE / "env/bin/python"
TRABALHO = BASE / "trabalho"
HASHTAGS = "#shorts #natureza #animais #curiosidades #biologia #educação"

def log(*a):
    print(f"[{datetime.now():%d/%m %H:%M:%S}]", *a, flush=True)

def ler_temas():
    p = BASE / "dados/temas.txt"
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text().splitlines() if l.strip()]

def marcar_como_feito(tema):
    with open(BASE / "dados/temas_feitos.txt", "a") as f:
        f.write(tema + "\n")

def temas_ja_feitos():
    p = BASE / "dados/temas_feitos.txt"
    if not p.exists():
        return set()
    return set(l.strip() for l in p.read_text().splitlines() if l.strip())

def main():
    temas = ler_temas()
    feitos = temas_ja_feitos()
    
    tema_atual = None
    for t in temas:
        if t not in feitos:
            tema_atual = t
            break
            
    if not tema_atual:
        log("Nenhum tema novo encontrado em temas.txt.")
        sys.exit(0)
        
    log(f"Iniciando produção do vídeo sobre: {tema_atual}")
    
    # 1. Gerar Roteiro
    log("A gerar roteiro...")
    r = subprocess.run([str(PY), "roteiro.py", tema_atual], cwd=BASE)
    if r.returncode != 0:
        log("Falha ao gerar roteiro. Abortando.")
        sys.exit(1)
        
    # 2. Descarregar Mídias e Gerar Áudio TTS
    log("A recolher mídias (Pexels) e a gerar áudio (TTS)...")
    r = subprocess.run([str(PY), "midia.py"], cwd=BASE)
    if r.returncode == 3:
        log(f"Sem mídia relevante suficiente para '{tema_atual}'. Tema pulado.")
        marcar_como_feito(tema_atual)
        sys.exit(0)
    if r.returncode != 0:
        log("Falha ao processar mídias. Abortando.")
        sys.exit(1)
        
    # 3. Montagem
    log("A montar o vídeo final...")
    r = subprocess.run(["bash", "montador.sh"], cwd=BASE)
    if r.returncode != 0:
        log("Falha na montagem. Abortando.")
        sys.exit(1)

    subprocess.run(["bash", "musica.sh", "video_final.mp4"], cwd=BASE)
    cm = ""
    mu = BASE / "dados" / "musica_usada.txt"
    cr = BASE / "musicas" / "creditos.txt"
    if mu.exists() and cr.exists():
        usada = mu.read_text().strip()
        for linha in cr.read_text(encoding="utf-8").splitlines():
            arq, _, txt = linha.partition("|")
            if arq.rsplit(".", 1)[0] == usada:
                cm = txt
    
    # 4. Upload para o YouTube
    roteiro_json = json.loads((TRABALHO / "roteiro.json").read_text(encoding="utf-8"))
    titulo = f"{roteiro_json['titulo']} #shorts"
    cf = TRABALHO / "creditos.txt"
    creditos = cf.read_text(encoding="utf-8") if cf.exists() else "Pexels"
    descricao = (
        f"Descubra as curiosidades sobre: {tema_atual}!\n\n"
        f"Fonte da pesquisa: {roteiro_json['fonte']}\n"
        f"Vídeos: Pexels - {creditos}\n"
        "Narração: IA Sintética (Edge TTS)\n"
        f"{cm}\n\n"
        f"{HASHTAGS}"
    )
    
    video_final = BASE / "video_final.mp4"
    if not video_final.exists():
        log("Erro Crítico: video_final.mp4 não foi encontrado após a montagem.")
        sys.exit(1)
    
    log("A enviar para o YouTube...")
    r = subprocess.run([str(PY), "uploader.py", str(video_final), titulo, descricao], cwd=BASE)
    
    if r.returncode == 2:
        log("Token inválido/expirado. Rode auth.py de novo.")
        sys.exit(2)
    if r.returncode != 0:
        log("Falha no upload do vídeo.")
        sys.exit(1)
        
    marcar_como_feito(tema_atual)
    video_final.unlink(missing_ok=True)
    log(f"Sucesso! Vídeo sobre '{tema_atual}' publicado e registado.")

if __name__ == "__main__":
    main()
