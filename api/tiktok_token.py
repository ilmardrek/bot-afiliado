import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
REDIRECT_URI = "http://127.0.0.1:3455/callback/"


def responder(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.end_headers()

    handler.wfile.write(body)


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        responder(self, 204, {})
        return

    def do_POST(self):
        client_key = os.environ.get("TIKTOK_CLIENT_KEY", "").strip()
        client_secret = os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()

        if not client_key:
            responder(self, 500, {
                "ok": False,
                "error": "TIKTOK_CLIENT_KEY não configurada"
            })
            return

        if not client_secret:
            responder(self, 500, {
                "ok": False,
                "error": "TIKTOK_CLIENT_SECRET não configurada"
            })
            return

        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(tamanho)

            try:
                dados = json.loads(raw_body.decode("utf-8"))
            except Exception:
                dados = parse_qs(raw_body.decode("utf-8"))

            def pegar(nome):
                valor = dados.get(nome)

                if isinstance(valor, list):
                    return (valor[0] if valor else "").strip()

                return str(valor or "").strip()

            code = pegar("code")
            code_verifier = pegar("code_verifier")

            if not code:
                responder(self, 400, {
                    "ok": False,
                    "error": "code não informado"
                })
                return

            if not code_verifier:
                responder(self, 400, {
                    "ok": False,
                    "error": "code_verifier não informado"
                })
                return

            formulario = {
                "client_key": client_key,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "code_verifier": code_verifier,
            }

            corpo = "&".join(
                f"{chave}={_urlencode_valor(valor)}"
                for chave, valor in formulario.items()
            ).encode("utf-8")

            requisicao = Request(
                TIKTOK_TOKEN_URL,
                data=corpo,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cache-Control": "no-cache",
                    "Accept": "application/json",
                },
                method="POST",
            )

            try:
                with urlopen(requisicao, timeout=30) as resposta:
                    status = resposta.status
                    conteudo = resposta.read().decode("utf-8", errors="replace")

            except HTTPError as erro:
                status = erro.code
                conteudo = erro.read().decode("utf-8", errors="replace")

            except URLError as erro:
                responder(self, 502, {
                    "ok": False,
                    "error": "Falha ao conectar ao TikTok",
                    "details": str(erro)
                })
                return

            try:
                retorno = json.loads(conteudo)
            except Exception:
                responder(self, status, {
                    "ok": False,
                    "status_tiktok": status,
                    "error": "TikTok retornou resposta não-JSON",
                    "raw": conteudo[:4000]
                })
                return

            if "access_token" in retorno:
                responder(self, 200, {
                    "ok": True,
                    "status_tiktok": status,
                    "data": retorno
                })
            else:
                responder(self, status, {
                    "ok": False,
                    "status_tiktok": status,
                    "data": retorno
                })

        except Exception as erro:
            responder(self, 500, {
                "ok": False,
                "error": "Erro interno no backend",
                "details": str(erro)
            })


def _urlencode_valor(valor):
    from urllib.parse import quote_plus
    return quote_plus(str(valor))
