import json
import os
import re
import subprocess
import requests
import threading
import time
from pathlib import Path
from django.http import JsonResponse, FileResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# URL para buscar novas definições de link
REMOTE_CONFIG_URL = "https://loscomedyhub.qzz.io/urls.json"

def get_templates_path():
    """Retorna o caminho do arquivo JSON local de URLs"""
    config_dir = Path(settings.BASE_DIR) / "comedyhub"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "url_templates.json"

def carregar_templates_urls():
    """Carrega a lista de templates de URL."""
    templates_padrao = [
        "https://comedyhub.b-cdn.net/memes/{post_id}/playlist.m3u8",
        "https://comedyhub.b-cdn.net/memes/{post_id}/{post_id}.m3u8",
        "https://cdn.thecomedyhub.com.br/cdn/memes/{post_id}/playlist.m3u8",
        "https://cdn.thecomedyhub.com.br/cdn/memes/{post_id}/{post_id}.m3u8",
        "https://comedyhub-api.b-cdn.net/memes/{post_id}/playlist.m3u8",
        "https://comedyhub-dev.b-cdn.net/memes/{post_id}/playlist.m3u8",
        "https://comedyhub-dev.b-cdn.net/memes/{post_id}/{post_id}.m3u8",
    ]

    arquivo_local = get_templates_path()
    if arquivo_local.exists():
        try:
            with open(arquivo_local, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if "urls" in dados and isinstance(dados["urls"], list):
                    return dados["urls"]
        except Exception:
            pass
    return templates_padrao

def atualizar_templates_remotos():
    """Baixa o JSON do servidor e salva localmente"""
    try:
        response = requests.get(REMOTE_CONFIG_URL, timeout=5)
        if response.status_code == 200:
            dados = response.json()
            if "urls" in dados and isinstance(dados["urls"], list):
                with open(get_templates_path(), 'w', encoding='utf-8') as f:
                    json.dump(dados, f, indent=4)
                return True
    except Exception:
        pass
    return False

def tentar_urls_possiveis(post_id):
    """Tenta encontrar URL válida"""
    templates = carregar_templates_urls()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for template in templates:
        try:
            url = template.replace("{post_id}", post_id)
            if requests.head(url, headers=headers, timeout=5, allow_redirects=True).status_code == 200:
                return url
        except Exception:
            continue

    if atualizar_templates_remotos():
        templates = carregar_templates_urls()
        for template in templates:
            try:
                url = template.replace("{post_id}", post_id)
                if requests.head(url, headers=headers, timeout=5, allow_redirects=True).status_code == 200:
                    return url
            except Exception:
                continue
    return None

def extrair_m3u8(link):
    """Extrai o ID da URL"""
    match = re.search(r'meme/([a-f0-9-]+)', link)
    if match:
        return match.group(1), None
    match_id = re.search(r'([a-f0-9-]{10,})', link)
    if match_id:
        return match_id.group(1), None
    return None, None

def agendar_limpeza(file_path, delay=300):
    """Agenda a exclusão de um arquivo após X segundos (padrão 5 min)"""
    def remover():
        time.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
    threading.Thread(target=remover, daemon=True).start()

@require_http_methods(["GET"])
@csrf_exempt
def downloads_page(request):
    return render(request, 'downloads/index.html')

@require_http_methods(["GET"])
def get_funny_messages(request):
    """Serve o arquivo JSON de mensagens divertidas da pasta comedyhub"""
    json_path = Path(settings.BASE_DIR) / "comedyhub" / "funny_messages.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return JsonResponse(data)
    return JsonResponse({"messages": []})

@csrf_exempt
def download_video(request):
    try:
        data = json.loads(request.body)
        video_url = data.get('url', '').strip()
        
        if not video_url:
            return JsonResponse({'error': 'URL não fornecida'}, status=400)
        
        post_id, _ = extrair_m3u8(video_url)
        if not post_id:
            return JsonResponse({'error': 'URL inválida'}, status=400)
        
        m3u8_url = tentar_urls_possiveis(post_id)
        if not m3u8_url:
            return JsonResponse({'error': 'Não foi possível encontrar o vídeo'}, status=404)
        
        downloads_dir = Path(settings.MEDIA_ROOT) / 'downloads'
        downloads_dir.mkdir(parents=True, exist_ok=True)
        
        # Caminho da logo (prioriza a pasta static/img/ do projeto)
        # Em produção (após collectstatic), o arquivo estará em STATIC_ROOT
        # Em desenvolvimento, o arquivo estará em static/img/
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'rodape.png')
        
        if not os.path.exists(logo_path):
            # Tenta no STATIC_ROOT se não estiver na pasta de desenvolvimento
            logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'rodape.png')
        
        output_filename = f"video_{post_id}.mp4"
        output_path = downloads_dir / output_filename
        
        # Filtro de Rodapé de 7% (Versão Robusta)
        if os.path.exists(logo_path):
            filtro = (
                f"[0:v]drawbox=y=ih-ih*0.07:h=ih*0.07:t=fill:c=black@1[bg];"
                f"[1:v]scale=-1:ih*0.055[logo];"
                f"[bg][logo]overlay=x=W-w-10:y=H-h-H*0.0075[v]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36\r\n",
                "-i", m3u8_url,
                "-i", logo_path,
                "-filter_complex", filtro,
                "-map", "[v]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "128k",
                str(output_path)
            ]
        else:
            # Sem logo se não encontrar o arquivo
            cmd = ["ffmpeg", "-y", "-i", m3u8_url, "-c:v", "libx264", "-c:a", "aac", str(output_path)]
        
        subprocess.run(cmd, check=True, capture_output=True, timeout=3600)
        
        if not output_path.exists():
            return JsonResponse({'error': 'Falha na criação do arquivo'}, status=500)
        
        # Agenda limpeza para 10 minutos após criação (garante que o usuário consiga baixar)
        agendar_limpeza(str(output_path), delay=600)
        
        download_url = f"/downloads/serve/{output_filename}/"
        return JsonResponse({
            'success': True,
            'download_url': download_url,
            'filename': output_filename
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def serve_download(request, filename):
    try:
        file_path = Path(settings.MEDIA_ROOT) / 'downloads' / filename
        if not file_path.exists():
            return JsonResponse({'error': 'Arquivo expirou ou não existe'}, status=404)
        
        response = FileResponse(open(file_path, 'rb'), content_type='video/mp4')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Tenta apagar logo após o envio (opcional, mas agendamento acima é mais seguro)
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
