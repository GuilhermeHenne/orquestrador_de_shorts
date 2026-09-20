# Gera roteiro curto (JSON) a partir da Wikipedia pt e de um modelo local (Ollama)
import json, sys, urllib.parse, urllib.request
from pathlib import Path

BASE = Path(__file__).parent
MODELO = "qwen2.5:3b"
OLLAMA = "http://localhost:11434/api/generate"
UA = {"User-Agent": "orquestra-uso-pessoal/0.1", "Content-Type": "application/json"}


def get_json(url, dados=None, timeout=600):
    req = urllib.request.Request(url, data=dados, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def wikipedia(tema):
    q = urllib.parse.quote(tema)
    busca = get_json(f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={q}&srlimit=1&format=json")
    achados = busca["query"]["search"]
    if not achados:
        return None, ""
    titulo = achados[0]["title"]
    t = urllib.parse.quote(titulo)
    d = get_json(f"https://pt.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&exintro=1&redirects=1&titles={t}&format=json")
    pagina = next(iter(d["query"]["pages"].values()))
    return titulo, (pagina.get("extract") or "")[:3000]


def pedir(titulo, texto):
    prompt = f"""Você é um roteirista viral de YouTube Shorts, especialista em retenção de público e gatilhos mentais.
Escreva o roteiro de um vídeo vertical MUITO CHAMATIVO sobre "{titulo}", baseado APENAS no texto fornecido.

REGRAS OBRIGATÓRIAS:
1. GANCHO (Cena 1): Comece com uma frase de choque absurda ou um mistério instigante (ex: "Você não vai acreditar...", "O segredo assustador...", "A ciência tentou esconder...").
2. TOM: Ágil, focado em curiosidades bizarras ou chocantes. Use linguagem de suspense.
3. FINAL (Cena 5): O vídeo OBRIGATORIAMENTE deve terminar no meio de um raciocínio com um suspense gigante, dizendo algo como: "Mas o mais assustador acontece quando... Curta e siga para a Parte 2!".
4. CENAS: Exatamente 5 cenas. Textos rápidos (1 a 2 frases curtas por cena).
5. BUSCA (CRÍTICO): O sistema de imagens só aceita INGLÊS BÁSICO. No campo "busca", use APENAS 1 ou 2 palavras EXTREMAMENTE GENÉRICAS em inglês. (Exemplos perfeitos: "forest", "wild cat", "river", "nature", "animal"). É PROIBIDO usar palavras em português ou frases complexas nesse campo.

Responda APENAS com JSON válido neste formato exato:
{{"titulo": "TÍTULO CLICKBAIT EM MAIÚSCULAS", "cenas": [{{"texto": "sua frase de impacto aqui", "busca": "GENERIC ENGLISH WORD"}}]}}

TEXTO BASE:
{texto}
"""
    corpo = json.dumps({"model": MODELO, "prompt": prompt, "stream": False, "format": "json",
                        "options": {"temperature": 0.5}}).encode()
    return json.loads(get_json(OLLAMA, corpo)["response"])


def valido(r):
    try:
        cenas = r["cenas"]
        return 4 <= len(cenas) <= 7 and all(c.get("busca") and c.get("texto") for c in cenas)
    except Exception:
        return False


def main():
    tema = " ".join(sys.argv[1:]).strip()
    if not tema:
        sys.exit('Uso: python roteiro.py "tema"')
    titulo, texto = wikipedia(tema)
    if not texto:
        sys.exit("Não achei esse tema na Wikipédia.")
    for tentativa in range(1, 4):
        print(f"Gerando roteiro (tentativa {tentativa}/3) sobre: {titulo}", flush=True)
        try:
            r = pedir(titulo, texto)
        except Exception as e:
            print("Erro:", e)
            continue
        if valido(r):
            r["tema"], r["fonte"] = titulo, f"https://pt.wikipedia.org/wiki/{urllib.parse.quote(titulo.replace(' ', '_'))}"
            Path(BASE / "trabalho").mkdir(exist_ok=True)
            (BASE / "trabalho" / "roteiro.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return
        
        print(f"Roteiro fora do padrão. Resposta: {json.dumps(r, ensure_ascii=False)}")
        print("Tentando de novo...")
        
    sys.exit("Não consegui um roteiro válido em 3 tentativas.")

if __name__ == "__main__":
    main()
