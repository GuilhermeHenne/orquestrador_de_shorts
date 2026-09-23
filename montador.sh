#!/bin/bash
# Prepara, compoe (com overlay/2a midia) e legenda as midias baixadas em trabalho/
cd "$(dirname "$0")"
TRABALHO="trabalho"
PY="/home/userapp/appvideos/scripts/env/bin"
export PATH="$PY:$PATH"

rm -f $TRABALHO/final_*.mp4 $TRABALHO/legenda.srt $TRABALHO/lista.txt video_final.mp4 $TRABALHO/cena_pronta_*.mp4

QTD=$(ls $TRABALHO/cena_*.mp3 2>/dev/null | wc -l)
if [ "$QTD" -eq 0 ]; then echo "Erro Crítico: Nenhuma cena em trabalho/."; exit 1; fi

echo "[1/4] Compondo as $QTD cenas (mídia + narração + overlay)..."
touch $TRABALHO/lista.txt
for i in $(seq 1 $QTD); do
    $PY/python compor_cena.py "$i" || { echo "Erro Crítico: falha ao compor a cena $i."; exit 1; }
    echo "file '$PWD/$TRABALHO/cena_pronta_$i.mp4'" >> $TRABALHO/lista.txt
done

echo "[2/4] Concatenando o vídeo completo..."
ffmpeg -loglevel error -nostats -f concat -safe 0 -i $TRABALHO/lista.txt -c copy -y $TRABALHO/final_sem_legenda.mp4

echo "[3/4] Gerando legendas com Whisper..."
$PY/python legendar.py $TRABALHO/final_sem_legenda.mp4 $TRABALHO/legenda.srt 2>/dev/null

echo "[4/4] Queimando as legendas no vídeo final..."
if [ -s $TRABALHO/legenda.srt ]; then
    FINAL="subtitles=$TRABALHO/legenda.srt:original_size=1080x1920:force_style='Alignment=2,FontSize=10,Bold=1,Outline=1,Shadow=0,MarginV=60'"
else
    echo "Aviso: arquivo SRT vazio ou sem fala."
    FINAL="null"
fi

ffmpeg -loglevel error -nostats -i $TRABALHO/final_sem_legenda.mp4 -vf "$FINAL" \
-c:v libx264 -preset fast -c:a copy -y video_final.mp4

if [ -f "video_final.mp4" ]; then
    bash musica.sh video_final.mp4
    rm -f $TRABALHO/cena_*.mp4 $TRABALHO/cena_*.mp3 $TRABALHO/cena_pronta_*.mp4 $TRABALHO/overlay_*.txt $TRABALHO/final_sem_legenda.mp4
    echo "Sucesso! O arquivo video_final.mp4 está pronto para upload."
fi
