# Autoriza o app no Google e gera o token.json
import os
SEG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "segredos")
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
flow = InstalledAppFlow.from_client_secrets_file(os.path.join(SEG, "client_secret.json"), SCOPES)
creds = flow.run_local_server(
    port=8080, open_browser=False,
    access_type="offline", prompt="consent",
)
open(os.path.join(SEG, "token.json"), "w").write(creds.to_json())
print("token.json salvo.")
