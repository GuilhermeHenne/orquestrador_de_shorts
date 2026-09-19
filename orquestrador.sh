#!/bin/bash
# Baixa o corte e renderiza o video em tela dividida
cd "$(dirname "$0")"
rm -f corte_bruto.mp4 video_final.mp4 legenda.srt
URL="$1"
PY=/home/userapp/appvideos/scripts/env/bin

GAMEPLAY=$(ls gameplays/*.mp4 2>/dev/null | shuf -n1)
if [ -z "$GAMEPLAY" ]; then echo "Erro Crítico: pasta gameplays/ vazia."; exit 1; fi
basename "$GAMEPLAY" .mp4 > gameplay_usado.txt
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$GAMEPLAY" | cut -d. -f1)
if [ "$DUR" -gt 70 ]; then OFFSET=$(( RANDOM % (DUR - 70) )); else OFFSET=0; fi
if [ $((RANDOM % 2)) -eq 0 ]; then ORDEM="[vtop][vbot]"; else ORDEM="[vbot][vtop]"; fi

echo "[1/4] Minerando o gráfico de retenção..."
TEMPOS=$($PY/python extrator.py "$URL" 2>/dev/null)
INICIO=$(echo $TEMPOS | awk '{print $1}')
FIM=$(echo $TEMPOS | awk '{print $2}')
if [ -z "$INICIO" ] || [ -z "$FIM" ]; then
    echo "Erro Crítico: Não foi possível calcular o tempo."
    exit 1
fi

echo "[2/4] Trecho ${INICIO}s - ${FIM}s. Gameplay: $GAMEPLAY (offset ${OFFSET}s)"
$PY/yt-dlp -q --no-warnings -S "ext" -f "bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best" --download-sections "*${INICIO}-${FIM}" -o "corte_bruto.mp4" "$URL"
if [ ! -f "corte_bruto.mp4" ]; then
    echo "Erro Crítico: Falha no download do vídeo."
    exit 1
fi

echo "[3/4] Gerando legendas com Whisper..."
$PY/python legendar.py corte_bruto.mp4 legenda.srt 2>/dev/null
if [ -s legenda.srt ]; then
  FINAL="[vs]subtitles=legenda.srt:original_size=1080x1920:force_style='Alignment=10,FontSize=10,Bold=1,Outline=1,Shadow=0,MarginV=0'[vout]"
else
  echo "Aviso: sem fala detectada, seguindo sem legenda."
  FINAL="[vs]null[vout]"
fi

echo "[4/4] Renderizando Split-Screen..."
ffmpeg -loglevel error -nostats -i corte_bruto.mp4 -stream_loop -1 -ss "$OFFSET" -i "$GAMEPLAY" -filter_complex \
"[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[vtop]; \
 [1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[vbot]; \
 ${ORDEM}vstack[vs]; ${FINAL}" \
-map "[vout]" -map 0:a -c:v libx264 -preset veryfast -r 30 -c:a aac -shortest -y video_final.mp4

if [ -f "video_final.mp4" ]; then
    rm -f corte_bruto.mp4 legenda.srt
    echo "Sucesso! O arquivo video_final.mp4 está pronto para upload."
fi
