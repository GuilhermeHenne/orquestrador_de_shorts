# Gera roteiro curto (JSON) a partir da Wikipedia pt e de um modelo local (Ollama)
import json, random, re, sys, time, urllib.error, urllib.parse, urllib.request
from validacao import fundamentado, corrigir_genero
from pathlib import Path

BASE = Path(__file__).parent
MODELO = "qwen2.5:7b"
OLLAMA = "http://localhost:11434/api/generate"
UA = {"User-Agent": "orquestrador-de-shorts/0.1 (https://github.com/GuilhermeHenne/orquestrador_de_shorts)", "Content-Type": "application/json"}
TITULOS = ["{t}: você sabia disso?", "Curiosidades sobre {t}", "{t}: fatos que impressionam"]
PALAVRAS_EN = {"the", "and", "you", "your", "is", "are", "of", "that", "they", "with", "this", "what", "will", "believe", "next"}
EXTRAS_BUSCA = ["", "water", "group", "close up", "nature"]
CTAS = ["Você já conhecia essa curiosidade? Conta nos comentários.", "Qual animal você quer ver no próximo vídeo? Comenta aí.", "E você, já viu um desses de perto? Conta nos comentários."]


def get_json(url, dados=None, timeout=600):
    for espera in (0, 5, 15, 45):
        time.sleep(espera)
        req = urllib.request.Request(url, data=dados, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
    raise RuntimeError("Wikipedia limitou as requisicoes (429)")


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
- Não comece duas frases seguidas com a mesma palavra; varie o começo das frases.
- Respeite o gênero gramatical do texto base (por exemplo "a capivara") e não compare com outros animais.
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
        if valido(r) and fundamentado(r["cenas"], texto, titulo):
            ultima = r["cenas"][-1]
            if "?" not in ultima["texto"]:
                ultima["texto"] = ultima["texto"].rstrip() + " " + random.choice(CTAS)
            r["titulo"] = random.choice(TITULOS).format(t=titulo)
            corrigir_genero(r["cenas"], texto, titulo)
            montar_buscas(nome_en, r["cenas"])
            r["tema"] = titulo
            m = re.search(r"\(([A-ZÀ-Ý][a-zà-ÿ]+ [a-zà-ÿ]{3,})[,)]", texto)
            r["cientifico"] = m.group(1) if m else ""
            r["fonte"] = f"https://pt.wikipedia.org/wiki/{urllib.parse.quote(titulo.replace(' ', '_'))}"
            (BASE / "trabalho").mkdir(exist_ok=True)
            (BASE / "trabalho" / "roteiro.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return
        print("Roteiro fora do padrão (idioma, tamanho ou formato). Tentando de novo...")
    sys.exit("Não consegui um roteiro válido em 3 tentativas.")


if __name__ == "__main__":
    main()
