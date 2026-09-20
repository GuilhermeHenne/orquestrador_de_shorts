# Checagens automaticas de fatos e correcao de genero do roteiro
import re

AFIRMACOES = ["dobro", "triplo", "metade", "vezes", "mais pesado", "mais rápido", "mais perigoso",
              "único", "única", "qualquer outra", "qualquer outro", "mais do que",
              "muito menor", "muito maior", "nenhum", "nenhuma"]
NUMEROS = ["dois", "duas", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez",
           "cem", "mil", "milhão", "milhões"]
TROCA_F = {"o": "a", "do": "da", "no": "na", "pelo": "pela", "um": "uma"}
TROCA_M = {v: k for k, v in TROCA_F.items()}


def fundamentado(cenas, fonte, nome):
    t = " ".join(c["texto"] for c in cenas).lower().replace("às vezes", "")
    f = fonte.lower()
    for num in set(re.findall(r"\d+(?:[.,]\d+)?", t)):
        if num not in f:
            print("Reprovado: número sem base na fonte:", num)
            return False
    for w in NUMEROS:
        if re.search(rf"\b{w}\b", t) and not re.search(rf"\b{w}\b", f):
            print("Reprovado: número por extenso sem base na fonte:", w)
            return False
    for termo in AFIRMACOES:
        if termo in t and termo not in f:
            print("Reprovado: afirmação sem base na fonte:", termo)
            return False
    return True


def genero(fonte, nome):
    f = fonte.lower()
    n = nome.lower()
    for alvo in (re.escape(n), re.escape(n.split("-")[0].split()[0])):
        fem = len(re.findall(rf"\b(a|da|na|pela|uma) {alvo}\b", f))
        mas = len(re.findall(rf"\b(o|do|no|pelo|um) {alvo}\b", f))
        if fem != mas:
            return "f" if fem > mas else "m"
    primeira = n.split("-")[0].split()[0]
    return "f" if primeira.endswith("a") else "m"


def corrigir_genero(cenas, fonte, nome):
    troca = TROCA_F if genero(fonte, nome) == "f" else TROCA_M
    padrao = re.compile(rf"\b({'|'.join(troca)}) ({re.escape(nome)})\b", re.I)

    def sub(m):
        novo = troca[m.group(1).lower()]
        if m.group(1)[0].isupper():
            novo = novo.capitalize()
        return f"{novo} {m.group(2)}"

    for c in cenas:
        c["texto"] = padrao.sub(sub, c["texto"])
