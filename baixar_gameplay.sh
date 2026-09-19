#!/bin/bash
cd "$(dirname "$0")"
source env/bin/activate
TERMO="$1"; N="${2:-3}"
mkdir -p gameplays
q=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$TERMO")
baixados=0
while read -r u && [ "$baixados" -lt "$N" ]; do
  antes=$(ls gameplays/*.mp4 2>/dev/null | wc -l)
  yt-dlp -q --no-warnings --no-playlist \
    --match-filter "license*=Creative Commons" \
    -f "bestvideo[ext=mp4][vcodec^=avc][height<=1080]" \
    --download-sections "*0-600" \
    --print-to-file "%(id)s|%(uploader)s|%(webpage_url)s" gameplays/creditos.txt \
    -o "gameplays/%(id)s.%(ext)s" "$u" < /dev/null
  depois=$(ls gameplays/*.mp4 2>/dev/null | wc -l)
  [ "$depois" -gt "$antes" ] && baixados=$((baixados+1))
done < <(yt-dlp --flat-playlist --playlist-end 40 --print url \
  "https://www.youtube.com/results?search_query=${q}&sp=EgIwAQ%253D%253D" 2>/dev/null | grep 'watch?v=')
echo "Baixados: $baixados"
