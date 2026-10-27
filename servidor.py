#!/usr/bin/env python3
"""Pagina educativa local para demonstrar dados expostos ao acessar um servidor."""

import argparse
import html
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs


BASE = Path(__file__).resolve().parent


def pagina(mensagem="", comparacao_url=""):
    aviso = f"<p class='resultado'>{html.escape(mensagem)}</p>" if mensagem else ""
    comparacao = (f'<p><a href="{html.escape(comparacao_url, quote=True)}">Participar da comparação HTTP × HTTPS</a></p>'
                  if comparacao_url else "")
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Laboratorio de rede aberta</title>
<style>body{{font:1.1rem system-ui,sans-serif;max-width:42rem;margin:2rem auto;padding:0 1rem;line-height:1.5;color:#18212a}}h1{{line-height:1.2}}form{{padding:1.2rem;background:#edf4fa;border-radius:.8rem}}input[type=text]{{display:block;width:100%;box-sizing:border-box;padding:.65rem;margin:.4rem 0 1rem}}button{{padding:.7rem 1rem;background:#1764a0;color:white;border:0;border-radius:.4rem;cursor:pointer}}.resultado{{padding:1rem;background:#daf3de}}</style>
</head><body><h1>Como funciona uma rede Wi-Fi aberta?</h1>
<p>Esta rede não pede senha e o tráfego HTTP desta página não é criptografado. Evite enviar dados pessoais ou senhas.</p>
<p>Ao abrir esta página, o servidor consegue ver o endereço IP usado pelo aparelho e o navegador pode enviar informações técnicas. O administrador da rede também pode observar o endereço MAC apresentado pelo aparelho, que pode ser aleatório.</p>
<p><strong>Participação:</strong> ao enviar o formulário, serão gravados horário, IP, identificação do navegador e o apelido que você escolher. Os registros ficam apenas neste computador para a demonstração.</p>
{aviso}{comparacao}
<form method="post" action="/registrar">
<label for="apelido">Apelido opcional (não use seu nome real)</label>
<input id="apelido" name="apelido" type="text" maxlength="40" autocomplete="off">
<label><input type="checkbox" name="concordo" value="sim" required> Concordo em registrar esses dados para a atividade.</label><br><br>
<button type="submit">Participar</button>
</form></body></html>"""


class Handler(BaseHTTPRequestHandler):
    log_path = BASE / "registros.jsonl"
    comparacao_url = ""

    def responder(self, status, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self.responder(200, pagina(comparacao_url=self.comparacao_url))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/registrar":
            self.send_error(404)
            return
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return
        if tamanho < 1 or tamanho > 2048:
            self.send_error(413)
            return
        try:
            campos = parse_qs(self.rfile.read(tamanho).decode("utf-8", "strict"))
        except UnicodeDecodeError:
            self.send_error(400)
            return
        if campos.get("concordo") != ["sim"]:
            self.responder(400, pagina("Marque a caixa de concordância para participar.", self.comparacao_url))
            return
        apelido = campos.get("apelido", [""])[0].strip()
        if len(apelido) > 40:
            self.send_error(400)
            return
        registro = {
            "horario_utc": datetime.now(timezone.utc).isoformat(),
            "ip": self.client_address[0],
            "navegador": self.headers.get("User-Agent", "")[:300],
            "apelido": apelido,
        }
        with self.log_path.open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
        self.responder(200, pagina("Participação registrada. Obrigado!", self.comparacao_url))

    def log_message(self, format, *args):
        # Não registrar automaticamente visitas sem participação.
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="10.42.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--log", type=Path, default=BASE / "registros.jsonl")
    args = parser.parse_args()
    Handler.log_path = args.log
    with HTTPServer((args.host, args.port), Handler) as servidor:
        print(f"Pagina em http://{args.host}:{args.port}", flush=True)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
