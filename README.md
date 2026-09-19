# orquestrador_de_shorts

Automação que transforma vídeos com licença Creative Commons em Shorts e publica no YouTube: corta o melhor trecho, empilha com um gameplay, legenda com Whisper e envia pela API oficial.

> Projeto de uso pessoal. Use apenas material cuja licença permita o reuso e sempre dê os créditos.

## Como funciona

`auto.py` escolhe a URL → `extrator.py` acha o melhor trecho → `orquestrador.sh` baixa, legenda (`legendar.py`) e monta o vídeo → `uploader.py` publica no YouTube → `auto.py` registra o resultado em `feito.txt`.

## Arquivos

### Pipeline

| Arquivo | O que faz |
|---|---|
| `auto.py` | O maestro. Pega a próxima URL de `fontes.txt`, confere se a licença é Creative Commons, chama o `orquestrador.sh`, monta título e descrição (com crédito e hashtags), chama o `uploader.py` e registra o resultado. É ele que o cron executa. |
| `extrator.py` | Descobre o melhor trecho de 60 segundos: o pico do gráfico de retenção ou, sem gráfico, o ponto em 30% do vídeo. |
| `orquestrador.sh` | Sorteia um gameplay (arquivo, ponto de início e quem fica em cima), baixa o trecho, chama o `legendar.py` e renderiza o vídeo final em tela dividida. |
| `legendar.py` | Transcreve a fala com o Whisper e gera a legenda em blocos de até 3 palavras. |
| `uploader.py` | Envia o vídeo ao YouTube pela API v3, com título, descrição e hashtags. |

### Alimentação da fila

| Arquivo | O que faz |
|---|---|
| `assuntos.txt` | Temas de busca, um por linha. |
| `abastecer.sh` | Busca cada assunto no YouTube (filtro CC) e acrescenta a `fontes.txt` só as URLs novas. |
| `baixar_gameplay.sh` | Baixa gameplays CC para `gameplays/` e anota o crédito de cada um. |
| `auth.py` | Autoriza o app no Google e gera o `token.json`. Roda uma vez. |

## Instalação

Requisitos: Python 3.12, `ffmpeg` e uma conta no Google Cloud com a **YouTube Data API v3** ativada.

```bash
python -m venv env
source env/bin/activate
pip install yt-dlp faster-whisper google-api-python-client google-auth-oauthlib
```

1. No Google Cloud, crie um cliente OAuth do tipo **App para computador** e salve o JSON como `client_secret.json` na pasta do projeto.
2. Rode `python auth.py` e autorize no navegador. Isso gera o `token.json`.
3. Crie a pasta `gameplays/` com vídeos de fundo, ou use `./baixar_gameplay.sh "termo de busca" 3`.

## Uso

```bash
./abastecer.sh          # enche a fila fontes.txt a partir de assuntos.txt
python auto.py          # posta 1 vídeo
python auto.py 3        # posta até 3 vídeos
```

Para agendar, chame `python auto.py` no cron.

Enquanto o app do Google Cloud estiver em modo "Testando", o `token.json` expira em 7 dias e é preciso rodar o `auth.py` de novo.

## Fica só na sua máquina (não vai para o Git)

O `.gitignore` bloqueia: `client_secret.json`, `token.json`, `env/`, `gameplays/`, `fontes.txt`, `feito.txt`, `falhas.txt`, `gameplay_usado.txt`, logs e qualquer `.mp4`, `.srt` ou `.png`. **Nunca versione credenciais.**

Durante a execução aparecem arquivos temporários (`corte_bruto.mp4`, `legenda.srt`, `video_final.mp4`) que são apagados no fim.
