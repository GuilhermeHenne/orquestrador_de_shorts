# Gera roteiro curto (JSON) a partir da Wikipedia pt e de um modelo local (Ollama)
import json, re, sys, urllib.parse, urllib.request
from pathlib import Path

BASE = Path(__file__).parent
MODELO = "qwen2.5:3b"
OLLAMA = "http://localhost:11434/api/generate"
UA = {"User-Agent": "orquestra-uso-pessoal/0.1", "Content-Type": "application/json"}
PALAVRAS_EN = {"the", "and", "you", "your", "is", "are", "of", "that", "they", "with", "this", "what", "will", "believe", "next"}
EXTRAS_BUSCA = ["", "water", "group", "close up", "nature"]


def get_json(url, dados=None, timeout=600):
    req = urllib.request.Request(url, data=dados, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def wikipedia(tema):
    q = urllib.parse.quote(tema)
    busca = get_json(f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={q}&srlimit=1&format=json")
    achados = busca["query"]["search"]
    if not achados:
        return None, "", ""
    titulo = achados[0]["title"]
    t = urllib.parse.quote(titulo)
    d = get_json(f"https://pt.wikipedia.org/w/api.php?action=query&prop=extracts%7Clanglinks&explaintext=1&exintro=1&redirects=1&lllang=en&titles={t}&format=json")
    pagina = next(iter(d["query"]["pages"].values()))
    ll = pagina.get("langlinks") or []
    nome_en = ll[0]["*"] if ll else ""
    return titulo, (pagina.get("extract") or "")[:3000], nome_en


def pedir(titulo, texto):
    prompt = f"""ATENÇÃO: escreva TUDO em PORTUGUÊS DO BRASIL. Não use inglês.

Você é roteirista de vídeos curtos de curiosidades sobre natureza.
Escreva a narração de um vídeo vertical de 30 a 40 segundos sobre "{titulo}", usando APENAS fatos do texto abaixo. Não invente números, datas nem fatos.

Regras:
- Exatamente 5 cenas, cada uma com 1 ou 2 frases curtas.
- Cena 1: um gancho curioso e verdadeiro, em forma de pergunta ou de fato surpreendente.
- Cenas 2 a 4: um fato do texto por cena.
- Cena 5: uma frase de fecho que encerra o assunto e deixa uma pergunta para o público comentar.
- Total entre 70 e 100 palavras. Sem emojis e sem MAIÚSCULAS.

Responda somente com JSON válido, neste formato:
{{"titulo": "título curto e curioso em português", "cenas": [{{"texto": "frase em português"}}]}}

TEXTO BASE:
{texto}

Lembre: título e frases em português do Brasil."""
    corpo = json.dumps({"model": MODELO, "prompt": prompt, "stream": False, "format": "json",
                        "options": {"temperature": 0.3}}).encode()
    return json.loads(get_json(OLLAMA, corpo)["response"])


def em_ingles(txt):
    palavras = re.findall(r"[a-zA-ZÀ-ÿ']+", txt.lower())
    return sum(p in PALAVRAS_EN for p in palavras) >= 2


def valido(r):
    try:
        cenas = r["cenas"]
        textos = [c["texto"].strip() for c in cenas]
        total = sum(len(t.split()) for t in textos)
        tudo = " ".join(textos + [r["titulo"]])
        return (len(cenas) == 5 and 60 <= total <= 120 and all(textos)
                and not em_ingles(tudo) and not tudo.isupper())
    except Exception:
        return False


def montar_buscas(nome_en, cenas):
    base = nome_en or "wildlife"
    for i, c in enumerate(cenas):
        c["busca"] = f"{base} {EXTRAS_BUSCA[i % len(EXTRAS_BUSCA)]}".strip()
        c["busca_fallback"] = base


def main():
    tema = " ".join(sys.argv[1:]).strip()
    if not tema:
        sys.exit('Uso: python roteiro.py "tema"')
    titulo, texto, nome_en = wikipedia(tema)
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
            montar_buscas(nome_en, r["cenas"])
            r["tema"] = titulo
            r["fonte"] = f"https://pt.wikipedia.org/wiki/{urllib.parse.quote(titulo.replace(' ', '_'))}"
            (BASE / "trabalho").mkdir(exist_ok=True)
            (BASE / "trabalho" / "roteiro.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return
        print("Roteiro fora do padrão (idioma, tamanho ou formato). Tentando de novo...")
    sys.exit("Não consegui um roteiro válido em 3 tentativas.")


if __name__ == "__main__":
    main()
