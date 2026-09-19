#!/bin/bash
# Busca videos CC no YouTube e abastece a fila fontes.txt
cd "$(dirname "$0")"
source env/bin/activate
touch fontes.txt feito.txt
rm -f fontes.tmp
while IFS= read -r assunto; do
  [ -z "$assunto" ] && continue
  q=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$assunto")
  yt-dlp --flat-playlist --playlist-end 30 --print url --skip-download \
    "https://www.youtube.com/results?search_query=${q}&sp=EgIwAQ%253D%253D" 2>/dev/null \
    | grep 'watch?v=' >> fontes.tmp
done < assuntos.txt
sort -u fontes.tmp | grep -vxFf fontes.txt | grep -vxFf feito.txt >> fontes.txt
rm -f fontes.tmp
wc -l fontes.txt
