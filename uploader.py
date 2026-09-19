# Envia o video ao YouTube pela API v3
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            open("token.json", "w").write(creds.to_json())
        else:
            print("Token inválido. Rode auth.py de novo."); sys.exit(2)
    return build("youtube", "v3", credentials=creds)

def upload(path, titulo, descricao="", privacidade="public"):
    yt = get_service()
    body = {
        "snippet": {"title": titulo[:100], "description": descricao, "categoryId": "20"},
        "status": {"privacyStatus": privacidade, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(path, mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"Enviando... {int(status.progress() * 100)}%")
    print("Publicado: https://youtube.com/shorts/" + resp["id"])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('Uso: python uploader.py <video> "<titulo>" ["<descricao>"]')
    upload(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
