#!/bin/bash
# Busca videos CC no YouTube e abastece a fila dados/fontes.txt
cd "$(dirname "$0")"
source env/bin/activate
touch dados/fontes.txt dados/feito.txt dados/assuntos.txt
: > fontes.tmp

TOTAL_ASSUNTOS=$(grep -vc '^\s*$' dados/assuntos.txt)
ATUAL=0
FALHAS=0

while IFS= read -r assunto; do
  [ -z "$assunto" ] && continue
  ATUAL=$((ATUAL + 1))
  echo "[$ATUAL/$TOTAL_ASSUNTOS] Buscando: $assunto"
  q=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$assunto")
  ANTES=$(wc -l < fontes.tmp)
  yt-dlp --flat-playlist --playlist-end 30 --print url --skip-download \
    --sleep-requests 1 \
    "https://www.youtube.com/results?search_query=${q}&sp=EgIwAQ%253D%253D" 2>>logs/abastecer_erros.log \
    | grep 'watch?v=' >> fontes.tmp
  DEPOIS=$(wc -l < fontes.tmp)
  if [ "$DEPOIS" -eq "$ANTES" ]; then
    echo "  aviso: nenhum resultado (pode ser bloqueio ou termo sem retorno CC)"
    FALHAS=$((FALHAS + 1))
  fi
  sleep 8
done < dados/assuntos.txt

if [ ! -s fontes.tmp ]; then
  echo "Erro: nenhuma URL encontrada em nenhum assunto. Veja logs/abastecer_erros.log."
  rm -f fontes.tmp
  exit 1
fi

ANTES_FILA=$(wc -l < dados/fontes.txt)
sort -u fontes.tmp | grep -vxFf dados/fontes.txt | grep -vxFf dados/feito.txt >> dados/fontes.txt
DEPOIS_FILA=$(wc -l < dados/fontes.txt)
rm -f fontes.tmp

echo "Novas URLs adicionadas: $((DEPOIS_FILA - ANTES_FILA))"
echo "Total na fila: $DEPOIS_FILA"
if [ "$FALHAS" -gt 0 ]; then
  echo "Assuntos sem retorno: $FALHAS de $TOTAL_ASSUNTOS"
fi
