# Gera legendas com Whisper (faster-whisper); sai com codigo 5 se o audio nao for portugues
import sys
from faster_whisper import WhisperModel

entrada, saida = sys.argv[1], sys.argv[2]
model = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = model.transcribe(entrada, language=None, word_timestamps=True, vad_filter=True)

if info.language != "pt" or info.language_probability < 0.6:
    print(f"IDIOMA: {info.language} ({info.language_probability:.2f})")
    sys.exit(5)

def ts(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), int(t % 60)
    return f"{h:02}:{m:02}:{s:02},{int((t - int(t)) * 1000):03}"

palavras = [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or []) if w.word.strip()]

blocos, atual = [], []
for w in palavras:
    atual.append(w)
    if len(atual) >= 3 or w[2].endswith((".", "?", "!", ",")):
        blocos.append(atual)
        atual = []
if atual:
    blocos.append(atual)

with open(saida, "w") as f:
    for n, b in enumerate(blocos, 1):
        ini, fim = b[0][0], b[-1][1]
        f.write(f"{n}\n{ts(ini)} --> {ts(max(fim, ini + 0.3))}\n{' '.join(x[2] for x in b).upper()}\n\n")
