import yt_dlp
import sys

def extrair_melhor_corte(url_video):
    ydl_opts = {'quiet': True, 'dump_single_json': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_video, download=False)
    
    duracao = info.get('duration', 0)
    heatmap = info.get('heatmap')
    
    if not heatmap:
        inicio = int(duracao * 0.3)
        return inicio, int(min(inicio + 60, duracao))

    pico = max(heatmap, key=lambda x: x['value'])
    tempo_pico = pico['start_time']
    
    inicio = max(0, tempo_pico - 15)
    fim = min(inicio + 60, duracao)
    
    return int(inicio), int(fim)

if __name__ == "__main__":
    url = sys.argv[1]
    inicio, fim = extrair_melhor_corte(url)
    print(f"{inicio} {fim}")
