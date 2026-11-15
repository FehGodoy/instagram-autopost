"""
Posta o próximo vídeo da fila (posts.csv) como Reel no Instagram.
Usa a API oficial do Instagram (login do Instagram) — sem Página do Facebook.

Variáveis de ambiente necessárias:
  IG_TOKEN      -> token de acesso de longa duração
  IG_USER_ID    -> ID da sua conta do Instagram
  VIDEO_BASE_URL-> URL pública da pasta de vídeos
                   ex: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/videos/

Uso:
  python postar.py            # posta o próximo vídeo pendente
  python postar.py --renovar  # renova o token (rode a cada ~50 dias)
"""
import csv
import os
import sys
import time
from pathlib import Path

import requests

PASTA = Path(__file__).parent
CSV_POSTS = PASTA / "posts.csv"
LOG_POSTADOS = PASTA / "postados.txt"

TOKEN = os.environ.get("IG_TOKEN", "").strip()
API = ""


def escolher_api():
    """Descobre qual host aceita o token (instagram ou facebook)."""
    global API
    falhas = []
    for host in ("https://graph.instagram.com/v21.0", "https://graph.facebook.com/v21.0"):
        r = requests.get(f"{host}/{USER_ID}", params={"fields": "id,username", "access_token": TOKEN}, timeout=30)
        if r.ok:
            API = host
            print(f"Conta: @{r.json().get('username', '?')} via {host}")
            return
        falhas.append(f"{host}: {r.json().get('error', {}).get('message', r.text)}")
    erro("token não aceito:\n  " + "\n  ".join(falhas))
USER_ID = os.environ.get("IG_USER_ID", "")
BASE_URL = os.environ.get("VIDEO_BASE_URL", "").rstrip("/") + "/"


def erro(msg):
    print(f"ERRO: {msg}")
    sys.exit(1)


def renovar_token():
    if not TOKEN.startswith("IG"):
        erro("renovação automática só vale para tokens IGAA; gere um novo token no painel da Meta")
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": TOKEN},
        timeout=30,
    )
    r.raise_for_status()
    dados = r.json()
    print("Novo token (atualize o secret IG_TOKEN):")
    print(dados["access_token"])
    print(f"Válido por {dados['expires_in'] // 86400} dias.")


def proximo_post():
    postados = set()
    if LOG_POSTADOS.exists():
        postados = {l.strip() for l in LOG_POSTADOS.read_text(encoding="utf-8").splitlines() if l.strip()}
    with open(CSV_POSTS, encoding="utf-8-sig", newline="") as f:
        for linha in csv.DictReader(f):
            video = (linha.get("video") or "").strip()
            if video and video not in postados:
                return video, (linha.get("legenda") or "").strip(), (linha.get("capa") or "").strip()
    return None, None, ""


def postar(video, legenda, capa=""):
    url_video = BASE_URL + video
    print(f"Enviando {url_video}")

    # 1) cria o container do Reel
    dados = {
        "media_type": "REELS",
        "video_url": url_video,
        "caption": legenda,
        "access_token": TOKEN,
    }
    # Capa opcional: número = segundo do vídeo usado como capa; nome de arquivo = imagem em capas/
    if capa:
        try:
            dados["thumb_offset"] = int(float(capa.replace(",", ".")) * 1000)
            print(f"  capa: frame em {capa}s")
        except ValueError:
            dados["cover_url"] = BASE_URL.replace("/videos/", "/capas/") + capa
            print(f"  capa: {dados['cover_url']}")

    r = requests.post(f"{API}/{USER_ID}/media", data=dados, timeout=60)
    if not r.ok:
        erro(f"criar container: {r.text}")
    container_id = r.json()["id"]

    # 2) espera o Instagram processar o vídeo (até ~10 min)
    for _ in range(60):
        s = requests.get(
            f"{API}/{container_id}",
            params={"fields": "status_code,status", "access_token": TOKEN},
            timeout=30,
        ).json()
        status = s.get("status_code")
        print(f"  status: {status}")
        if status == "FINISHED":
            break
        if status == "ERROR":
            erro(f"processamento do vídeo: {s.get('status')}")
        time.sleep(10)
    else:
        erro("tempo esgotado esperando o vídeo processar")

    # 3) publica
    r = requests.post(
        f"{API}/{USER_ID}/media_publish",
        data={"creation_id": container_id, "access_token": TOKEN},
        timeout=60,
    )
    if not r.ok:
        erro(f"publicar: {r.text}")
    print(f"Publicado! ID: {r.json()['id']}")

    with open(LOG_POSTADOS, "a", encoding="utf-8") as f:
        f.write(video + "\n")


if __name__ == "__main__":
    if not TOKEN:
        erro("defina IG_TOKEN")
    if "--renovar" in sys.argv:
        renovar_token()
        sys.exit(0)
    if not USER_ID or BASE_URL == "/":
        erro("defina IG_USER_ID e VIDEO_BASE_URL")

    escolher_api()
    video, legenda, capa = proximo_post()
    if not video:
        print("Fila vazia — nada para postar.")
        sys.exit(0)
    postar(video, legenda, capa)
