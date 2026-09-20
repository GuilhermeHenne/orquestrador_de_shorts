# Checagens automaticas de fatos e genero do roteiro
import re

AFIRMACOES = ["dobro", "triplo", "metade", "vezes", "mais pesado", "mais rápido", "mais perigoso", "único", "única"]


def fundamentado(cenas, fonte, nome):
    t = " ".join(c["texto"] for c in cenas).lower().replace("às vezes", "")
    f = fonte.lower()
    for num in set(re.findall(r"\d+(?:[.,]\d+)?", t)):
        if num not in f:
            print("Reprovado: número sem base na fonte:", num)
            return False
    for w in ["dois", "duas", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "cem", "mil", "milhão", "milhões"]:
        if re.search(rf"\b{w}\b", t) and not re.search(rf"\b{w}\b", f):
            print("Reprovado: número por extenso sem base na fonte:", w)
            return False
    for termo in AFIRMACOES:
        if termo in t and termo not in f:
            print("Reprovado: afirmação sem base na fonte:", termo)
            return False
    n = re.escape(nome.lower())
    fem = len(re.findall(rf"\b(a|da|na|pela|uma) {n}\b", f))
    mas = len(re.findall(rf"\b(o|do|no|pelo|um) {n}\b", f))
    if fem != mas:
        errado = "o|do|no|pelo|um" if fem > mas else "a|da|na|pela|uma"
        if re.search(rf"\b({errado}) {n}\b", t):
            print("Reprovado: gênero errado para", nome)
            return False
    return True
