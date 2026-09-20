#!/bin/bash
# Mistura musica de fundo (lo-fi) no video, com volume baixo e ducking sob a narracao
cd "$(dirname "$0")"
VIDEO="${1:-video_final.mp4}"
VOL=0.30   # volume da musica (0.2 mais baixo, 0.4 mais alto)
MUSICA=$(ls musicas/*.mp3 musicas/*.wav musicas/*.m4a 2>/dev/null | shuf -n1)
if [ -z "$MUSICA" ]; then echo "Aviso: pasta musicas/ vazia, seguindo sem musica."; exit 0; fi
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO" | cut -d. -f1)
TD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MUSICA" | cut -d. -f1)
if [ "$TD" -gt $((DUR + 10)) ]; then OFFSET=$(( RANDOM % (TD - DUR - 5) )); else OFFSET=0; fi
FADE=$((DUR - 2)); [ "$FADE" -lt 1 ] && FADE=1
echo "Musica: $MUSICA (inicio ${OFFSET}s)"
ffmpeg -loglevel error -y -i "$VIDEO" -stream_loop -1 -ss "$OFFSET" -i "$MUSICA" -filter_complex \
"[0:a]asplit=2[voz1][voz2]; \
 [1:a]volume=${VOL},afade=t=in:st=0:d=1.5,afade=t=out:st=${FADE}:d=2[m]; \
 [m][voz1]sidechaincompress=threshold=0.04:ratio=8:attack=20:release=400[duck]; \
 [voz2][duck]amix=inputs=2:duration=first:normalize=0[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -t "$DUR" trabalho/com_musica.mp4 \
&& mv trabalho/com_musica.mp4 "$VIDEO" \
&& basename "$MUSICA" > dados/musica_usada.txt
