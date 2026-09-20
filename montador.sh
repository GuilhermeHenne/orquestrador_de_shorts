#!/bin/bash
# Prepara, concatena e legenda as mídias baixadas na pasta trabalho/
cd "$(dirname "$0")"
TRABALHO="trabalho"
PY="/home/userapp/appvideos/scripts/env/bin"
export PATH="$PY:$PATH"

rm -f $TRABALHO/final_*.mp4 $TRABALHO/legenda.srt $TRABALHO/lista.txt video_final.mp4

# Conta quantas mídias foram geradas
QTD=$(ls $TRABALHO/cena_*.mp4 2>/dev/null | wc -l)
if [ "$QTD" -eq 0 ]; then echo "Erro Crítico: Nenhum vídeo na pasta trabalho/."; exit 1; fi

echo "[1/4] Ajustando e sincronizando as $QTD cenas..."
touch $TRABALHO/lista.txt

for i in $(seq 1 $QTD); do
    VID="$TRABALHO/cena_$i.mp4"
    AUD="$TRABALHO/cena_$i.mp3"
    OUT="$TRABALHO/cena_pronta_$i.mp4"
    
    # Faz loop infinito do vídeo (-stream_loop -1), corta para 1080x1920
    # e encerra o arquivo exatamente quando o áudio da narração acaba (-shortest)
    ffmpeg -loglevel error -nostats -stream_loop -1 -i "$VID" -i "$AUD" \
    -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" \
    -c:v libx264 -preset veryfast -r 30 -c:a aac -shortest -y "$OUT"
    
    # Registra o caminho absoluto na lista de concatenação
    echo "file '$PWD/$OUT'" >> $TRABALHO/lista.txt
done

echo "[2/4] Concatenando o vídeo completo..."
ffmpeg -loglevel error -nostats -f concat -safe 0 -i $TRABALHO/lista.txt -c copy -y $TRABALHO/final_sem_legenda.mp4

echo "[3/4] Gerando legendas com Whisper..."
# Seu legendar.py aceita o mp4 e devolve o SRT perfeitamente aqui
$PY/python legendar.py $TRABALHO/final_sem_legenda.mp4 $TRABALHO/legenda.srt 2>/dev/null

echo "[4/4] Queimando as legendas no vídeo final..."
if [ -s $TRABALHO/legenda.srt ]; then
    # Mesma estilização do seu orquestrador original
    FINAL="subtitles=$TRABALHO/legenda.srt:original_size=1080x1920:force_style='Alignment=10,FontSize=10,Bold=1,Outline=1,Shadow=0,MarginV=0'"
else
    echo "Aviso: arquivo SRT vazio ou sem fala."
    FINAL="null"
fi

ffmpeg -loglevel error -nostats -i $TRABALHO/final_sem_legenda.mp4 -vf "$FINAL" \
-c:v libx264 -preset fast -c:a copy -y video_final.mp4

if [ -f "video_final.mp4" ]; then
    # Limpa os arquivos temporários pesados gerados no processo
    rm -f $TRABALHO/cena_*.mp4 $TRABALHO/cena_*.mp3 $TRABALHO/final_sem_legenda.mp4
    echo "Sucesso! O arquivo video_final.mp4 está pronto para upload."
fi
