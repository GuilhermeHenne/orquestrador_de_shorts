# Confere quantos videos relevantes o Pexels tem para cada tema de dados/temas.txt
import json, re, subprocess, sys, time, urllib.parse
from pathlib import Path
from midia import carregar_env, PALAVRAS_FRACAS
from roteiro import wikipedia

BASE = Path(__file__).parent
MIN_OK = 5


def contar(query, api_key):
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=15"
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: {api_key}", url], capture_output=True, text=True)
    try:
        videos = json.loads(r.stdout).get("videos") or []
    except Exception:
        return 0
    chaves = [w for w in re.findall(r"[a-z]+", query.lower()) if len(w) > 3 and w not in PALAVRAS_FRACAS]
    return sum(all(w in v.get("url", "").lower() for w in chaves) for v in videos)


def main():
    api_key = carregar_env()
    arq = BASE / "dados" / "temas.txt"
    temas = [l.strip() for l in arq.read_text().splitlines() if l.strip()]
    sem = []
    print(f"{'tema':22} {'artigo':22} {'nome em inglês':24} {'espécie':>7} {'grupo':>5}")
    for t in temas:
        try:
            titulo, _, nome_en = wikipedia(t)
        except Exception as e:
            print(f"{t:26} erro na Wikipédia: {e}")
            continue
        if not nome_en:
            print(f"{t:26} (sem nome em inglês)   -> SEM MÍDIA")
            sem.append(t)
            continue
        esp = contar(nome_en, api_key)
        grp = contar(nome_en.split()[-1], api_key)
        ok = esp >= MIN_OK
        print(f"{t:22} {titulo[:22]:22} {nome_en:24} {esp:>7} {grp:>5}   {'ok' if ok else '-> SEM MÍDIA'}")
        if not ok:
            sem.append(t)
        time.sleep(3)
    if "--limpar" in sys.argv and sem:
        ok_list = [t for t in temas if t not in sem]
        arq.write_text("\n".join(ok_list) + "\n")
        with open(BASE / "dados" / "temas_sem_midia.txt", "a") as f:
            f.write("\n".join(sem) + "\n")
        print(f"\nMovidos {len(sem)} tema(s) para dados/temas_sem_midia.txt")


main()
