
 GUIA DOS ARQUIVOS - /home/userapp/appvideos/scripts


CAMINHO DE UM VIDEO
-------------------
auto.py escolhe a URL
   -> extrator.py acha o melhor trecho
   -> orquestrador.sh baixa, legenda (legendar.py) e monta o video
   -> uploader.py publica no YouTube
   -> auto.py registra o resultado em feito.txt


---------------------------------------------------------------------
1) PIPELINE (os scripts que trabalham)
---------------------------------------------------------------------

auto.py
  O maestro. Pega a proxima URL de fontes.txt, confere se a licenca e
  Creative Commons, chama o orquestrador.sh, monta titulo e descricao
  (com credito e hashtags), chama o uploader.py e registra o resultado.
  E ele que o cron executa.
  Uso: python auto.py        (posta 1 video)
       python auto.py 3      (posta ate 3 videos)

extrator.py
  Descobre o melhor trecho de 60 segundos: o pico do grafico de
  retencao ou, quando o video nao tem grafico, o ponto em 30% do video.
  Devolve o inicio e o fim em segundos.

orquestrador.sh
  Sorteia um gameplay (arquivo, ponto de inicio e quem fica em cima),
  baixa o trecho, chama o legendar.py e renderiza o video final em tela
  dividida com a legenda. Gera o video_final.mp4.

legendar.py
  Transcreve a fala com o Whisper e gera o arquivo de legenda
  (legenda.srt), em blocos de ate 3 palavras.

uploader.py
  Envia o video_final.mp4 ao YouTube pela API, com titulo, descricao e
  hashtags.


---------------------------------------------------------------------
2) ALIMENTACAO (o que entra na fila)
---------------------------------------------------------------------

assuntos.txt
  Lista de temas de busca, um por linha.

abastecer.sh
  Busca no YouTube cada assunto (com o filtro de licenca CC) e
  acrescenta ao fontes.txt somente as URLs novas.

fontes.txt
  A fila de videos candidatos, um link por linha.

feito.txt
  Links ja postados ou descartados (sem CC, muito curtos, falhas
  repetidas). Evita repetir videos.

baixar_gameplay.sh
  Baixa gameplays com licenca CC para a pasta gameplays/ e anota o
  credito de cada um.
  Uso: ./baixar_gameplay.sh "termo de busca" quantidade

gameplays/
  Os videos de fundo, mais o creditos.txt com o autor de cada um.


---------------------------------------------------------------------
3) AMBIENTE E RESTOS
---------------------------------------------------------------------

env/
  Ambiente virtual do Python com as bibliotecas (yt-dlp, Whisper,
  Google API). Nao mexa.

__pycache__/
  Cache que o Python cria sozinho. Pode ignorar.

auto.log
  Onde o cron grava o que o auto.py imprime. Serve para ver o que
  aconteceu quando voce nao estava olhando.

gameplay_usado.txt
  Arquivo temporario: guarda qual gameplay entrou no ultimo video, para
  o credito na descricao e para nao repetir o mesmo em seguida.

auto.py.bak
  Backup da versao antiga do auto.py. Pode apagar (rm auto.py.bak).


---------------------------------------------------------------------
ARQUIVOS QUE APARECEM SO DURANTE A EXECUCAO
---------------------------------------------------------------------

corte_bruto.mp4   trecho baixado, antes da montagem
legenda.srt       legenda gerada pelo Whisper
video_final.mp4   video pronto para o upload
falhas.txt        URLs que falharam (aparece quando algo da errado)
