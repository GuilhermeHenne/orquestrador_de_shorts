# orquestrador_de_shorts

Automação completa para criação e publicação de vídeos curtos no YouTube Shorts. O projeto possui duas esteiras independentes:
1. **Cortes CC:** Transforma vídeos Creative Commons em Shorts (corta o melhor trecho, empilha com gameplay e legenda).
2. **Originais IA:** Cria vídeos do zero sobre temas específicos da natureza utilizando Wikipédia, Ollama, Pexels e voz sintética.

> Projeto de uso pessoal. Use apenas material cuja licença permita o reuso e sempre dê os créditos.

## Como funciona

**Esteira 1 (Cortes CC):**
`auto.py` escolhe a URL → `extrator.py` acha o melhor trecho → `orquestrador.sh` baixa, legenda (`legendar.py`) e monta o vídeo em tela dividida → `uploader.py` publica no YouTube.

**Esteira 2 (Originais IA):**
`auto_ai.py` lê o próximo tema inédito → `roteiro.py` gera um script narrativo com IA → `midia.py` baixa os vídeos (Pexels) e gera a voz (Edge-TTS) → `montador.sh` sincroniza, concatena e legenda → `uploader.py` publica no YouTube.

## Arquivos

### Pipeline 1: Cortes CC
| Arquivo | O que faz |
|---|---|
| `auto.py` | O maestro. Pega a próxima URL de `fontes.txt`, confere se a licença é CC, chama o orquestrador e publica. |
| `extrator.py` | Descobre o melhor trecho de 60 segundos (pico do gráfico de retenção ou 30% do vídeo). |
| `orquestrador.sh` | Sorteia um gameplay de fundo, baixa o trecho, legenda e renderiza o vídeo final (`vstack`). |
| `baixar_gameplay.sh`| Baixa gameplays CC para a pasta `gameplays/` e anota o crédito de cada um. |
| `abastecer.sh` | Busca cada assunto de `assuntos.txt` no YouTube (filtro CC) e adiciona URLs novas em `fontes.txt`. |

### Pipeline 2: Originais IA
| Arquivo | O que faz |
|---|---|
| `auto_ai.py` | O maestro da inteligência artificial. Lê `temas.txt`, orquestra a geração, edição e publicação. |
| `roteiro.py` | Busca informações na Wikipédia PT e aciona um modelo local (Ollama) para gerar um roteiro curto estruturado em JSON com ganchos de retenção. |
| `midia.py` | Lê o roteiro, faz requisições via `curl` na API do Pexels para baixar vídeos nativos verticais e usa `edge-tts` para gerar a narração localmente. |
| `montador.sh` | Sincroniza o tempo de cada clipe da Pexels com a narração (`-shortest`), concatena as cenas no tempo exato e queima as legendas por cima. |

### Módulos Compartilhados
| Arquivo | O que faz |
|---|---|
| `legendar.py` | Transcreve a fala do arquivo final utilizando o Whisper e gera a legenda em blocos rápidos (SRT). |
| `uploader.py` | Envia o vídeo ao YouTube pela API v3, com título, descrição detalhada e hashtags. |
| `auth.py` | Autoriza o app no Google Cloud e gera o `token.json` local. |

## Instalação

**Requisitos do Sistema:** Python 3.12, `ffmpeg`, `curl` e [Ollama](https://ollama.com/) rodando localmente (com o modelo `qwen2.5:3b` baixado).

```bash
python -m venv env
source env/bin/activate
pip install yt-dlp faster-whisper google-api-python-client google-auth-oauthlib edge-tts
