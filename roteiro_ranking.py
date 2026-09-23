# Gera roteiro de ranking (5 itens) com base na Wikipedia + Ollama
import json, random, re, sys
from pathlib import Path
from roteiro import wikipedia, get_json, em_ingles, OLLAMA, MODELO
from validacao import fundamentado, corrigir_genero

BASE = Path(__file__).parent


def pedir_item(titulo, texto, posicao):
    prompt = f"""ATENÇÃO: responda em PORTUGUÊS DO BRASIL.
Escreva UMA frase curta (12 a 18 palavras) e curiosa sobre "{titulo}", usando APENAS o texto abaixo. Não mencione números de posição ou ranking. Não invente fatos. Sem emojis, sem maiúsculas.
Responda somente JSON: {{"texto": "frase"}}

TEXTO:
{texto}"""
    corpo = json.dumps({"model": MODELO, "prompt": prompt, "stream": False, "format": "json",
                        "options": {"temperature": 0.4}}).encode()
    return json.loads(get_json(OLLAMA, corpo)["response"])["texto"].strip()


def gerar_item(nome, posicao):
    titulo, texto, nome_en = wikipedia(nome)
    if not texto:
        return None
    for _ in range(3):
        try:
            frase = pedir_item(titulo, texto, posicao)
        except Exception as e:
            print(f"  erro ao gerar item ({nome}): {e}")
            continue
        if frase and not em_ingles(frase) and 6 <= len(frase.split()) <= 25 and fundamentado([{"texto": frase}], texto, titulo):
            corrigir_genero([{"texto": frase}], texto, titulo)
            m = re.search(r"\(([A-ZÀ-Ý][a-zà-ÿ]+ [a-zà-ÿ]{3,})[,)]", texto)
            return {"posicao": posicao, "titulo_item": titulo, "texto": f"Número {posicao}: {titulo}. {frase}",
                    "busca": nome_en or titulo, "busca_fallback": nome_en or titulo,
                    "cientifico": m.group(1) if m else ""}
    return None


def main():
    linhas = [l for l in (BASE / "dados" / "rankings.txt").read_text().splitlines() if l.strip()]
    feitos = set((BASE / "dados" / "rankings_feitos.txt").read_text().splitlines()) if (BASE / "dados" / "rankings_feitos.txt").exists() else set()
    escolha = next((l for l in linhas if l.split("|")[0] not in feitos), None)
    if not escolha:
        sys.exit("Nenhum ranking novo em dados/rankings.txt.")
    titulo_ranking, animais = escolha.split("|")
    animais = [a.strip() for a in animais.split(",")]
    if len(animais) != 5:
        sys.exit("O ranking precisa ter exatamente 5 animais, do 5º ao 1º lugar.")

    cenas = [{"texto": f"Você conhece {titulo_ranking.lower()}? Fica até o fim para ver o número 1!",
              "busca": "wildlife nature", "busca_fallback": "wildlife nature", "posicao": 0}]
    for pos, animal in zip([5, 4, 3, 2, 1], animais):
        print(f"Gerando item {pos}: {animal}...", flush=True)
        item = gerar_item(animal, pos)
        if not item:
            sys.exit(f"Não consegui um fato confiável sobre '{animal}'. Ajuste dados/rankings.txt.")
        cenas.append(item)
    cenas.append({"texto": "Qual desses você não sabia? Comenta aqui embaixo!",
                  "busca": "wildlife nature", "busca_fallback": "wildlife nature", "posicao": 0})

    roteiro = {"titulo": titulo_ranking, "cenas": cenas, "tema": titulo_ranking,
               "fonte": "Wikipédia (várias páginas, uma por item)", "ranking": True}
    (BASE / "trabalho").mkdir(exist_ok=True)
    (BASE / "trabalho" / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=2))
    print(json.dumps(roteiro, ensure_ascii=False, indent=2))
    with open(BASE / "dados" / "rankings_feitos.txt", "a") as f:
        f.write(titulo_ranking + "\n")


if __name__ == "__main__":
    main()
