# Monta uma cena: 1 ou 2 midias + narracao + overlay opcional (numero/nome do ranking)
import json, subprocess, sys
from pathlib import Path

BASE = Path(__file__).parent
TRABALHO = BASE / "trabalho"


def duracao(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 5.0


def main():
    i = int(sys.argv[1])
    aud = TRABALHO / f"cena_{i}.mp3"
    v1 = TRABALHO / f"cena_{i}.mp4"
    v2 = TRABALHO / f"cena_{i}_b.mp4"
    out = TRABALHO / f"cena_pronta_{i}.mp4"
    dur = duracao(aud)

    roteiro = json.loads((TRABALHO / "roteiro.json").read_text(encoding="utf-8"))
    cena = roteiro["cenas"][i - 1]
    posicao = cena.get("posicao", 0)

    crop = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    if posicao:
        texto = f"N\u00ba{posicao}\n{cena.get('titulo_item', '').upper()}"
        txt_file = TRABALHO / f"overlay_{i}.txt"
        txt_file.write_text(texto, encoding="utf-8")
        overlay = (",drawtext=textfile='" + str(txt_file) + "':fontsize=90:fontcolor=white:borderw=6:bordercolor=black@0.8"
                   ":box=1:boxcolor=black@0.35:boxborderw=25:x=(w-text_w)/2:y=140:line_spacing=10")
    else:
        overlay = ""
    vf = crop + overlay

    if v2.exists():
        meio = max(dur / 2, 0.5)
        p1, p2 = TRABALHO / f"_p1_{i}.mp4", TRABALHO / f"_p2_{i}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", str(v1), "-t", str(meio),
                        "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", str(p1)], check=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", str(v2), "-t", str(dur - meio),
                        "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-r", "30", str(p2)], check=True)
        lst = TRABALHO / f"_lst_{i}.txt"
        lst.write_text(f"file '{p1.resolve()}'\nfile '{p2.resolve()}'\n")
        muda = TRABALHO / f"_muda_{i}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(muda)], check=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(muda), "-i", str(aud),
                        "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)], check=True)
        for f in (p1, p2, lst, muda):
            f.unlink(missing_ok=True)
    else:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", str(v1), "-i", str(aud),
                        "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-c:a", "aac",
                        "-shortest", str(out)], check=True)


if __name__ == "__main__":
    main()
