"""Laboratório HTTP/HTTPS: observa bytes TCP antes de o servidor TLS decifrá-los.

Os dois pontos de observação encaminham somente para servidores locais fixados
pelo próprio app. Não são proxies abertos e não capturam tráfego de outros sites.
"""

import hashlib
import ipaddress
import html
import http.client
import json
import secrets
import select
import shutil
import socket
import socketserver
import ssl
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode


LIMITE_FLUXO = 65536
LIMITE_ENVIOS = 100
PORTA_HTTP = 8081
PORTA_HTTPS = 8443


class ErroComparacao(Exception):
    pass


class Observacao:
    def __init__(self, origem, protocolo):
        self.origem = origem
        self.protocolo = protocolo
        self.bytes = bytearray()
        self.truncado = False

    def adicionar(self, dados):
        restante = LIMITE_FLUXO - len(self.bytes)
        self.bytes.extend(dados[:restante])
        self.truncado |= len(dados) > restante


class Ponte(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, endereco, destino, laboratorio, protocolo):
        self.destino = destino
        self.laboratorio = laboratorio
        self.protocolo = protocolo
        self.limite = threading.BoundedSemaphore(24)
        super().__init__(endereco, Encaminhar)


class Encaminhar(socketserver.BaseRequestHandler):
    def handle(self):
        ponte = self.server
        if not ponte.limite.acquire(blocking=False):
            return
        destino = None
        chave = None
        try:
            self.request.settimeout(5)
            destino = socket.create_connection(ponte.destino, timeout=5)
            chave = (ponte.protocolo, destino.getsockname()[1])
            observacao = Observacao(self.client_address[0], ponte.protocolo)
            with ponte.laboratorio.lock:
                ponte.laboratorio.observacoes[chave] = observacao
            # O TLS é negociado entre o cliente e o servidor de destino. A ponte
            # encaminha os registros TLS sem possuir contexto de descriptografia.
            while not ponte.laboratorio.parar.is_set():
                prontos, _, _ = select.select([self.request, destino], [], [], 1)
                if not prontos:
                    continue
                for origem in prontos:
                    dados = origem.recv(16384)
                    if not dados:
                        return
                    if origem is self.request:
                        with ponte.laboratorio.lock:
                            observacao.adicionar(dados)
                        destino.sendall(dados)
                    else:
                        self.request.sendall(dados)
        except (OSError, ValueError):
            pass
        finally:
            if chave:
                with ponte.laboratorio.lock:
                    ponte.laboratorio.observacoes.pop(chave, None)
            if destino:
                destino.close()
            ponte.limite.release()


class ServidorDestino(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, laboratorio, protocolo, contexto=None):
        self.laboratorio = laboratorio
        self.protocolo = protocolo
        self.contexto = contexto
        super().__init__(("127.0.0.1", 0), Receber)

    def get_request(self):
        conexao, origem = super().get_request()
        conexao.settimeout(5)
        if self.contexto:
            conexao = self.contexto.wrap_socket(conexao, server_side=True, do_handshake_on_connect=False)
        return conexao, origem

    def handle_error(self, request, client_address):
        # Uma tentativa HTTPS sem o certificado confiável não é participação.
        # Não criar registros de acesso nem expor cabeçalhos em tracebacks.
        pass


class Receber(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(5)
        super().setup()

    def log_message(self, format, *args):
        pass

    def responder(self, status, conteudo, tipo="text/html; charset=utf-8", anexo=None):
        dados = conteudo.encode("utf-8") if isinstance(conteudo, str) else conteudo
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        if anexo:
            self.send_header("Content-Disposition", f'attachment; filename="{anexo}"')
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        lab = self.server.laboratorio
        if self.path == "/certificado.crt":
            self.responder(200, lab.certificado_publico, "application/x-x509-ca-cert", "Rede-Aberta-Laboratorio.crt")
        elif self.path == "/":
            self.responder(200, lab.pagina(self.server.protocolo))
        else:
            self.responder(404, "Página não encontrada.")

    def do_POST(self):
        if self.path != "/enviar":
            self.responder(404, "Página não encontrada.")
            return
        lab = self.server.laboratorio
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if not 0 < tamanho <= 2048:
                self.responder(413, "Envio acima do limite.")
                return
            campos = parse_qs(self.rfile.read(tamanho).decode("utf-8", "strict"), max_num_fields=8)
        except (ValueError, UnicodeDecodeError):
            self.responder(400, "Formulário inválido.")
            return
        if campos.get("concordo") != ["sim"]:
            self.responder(400, lab.pagina(self.server.protocolo, "Marque a concordância antes de enviar."))
            return
        if campos.get("sessao") != [lab.token]:
            self.responder(400, "A comparação foi reiniciada. Abra novamente a página.")
            return
        mensagens = campos.get("mensagem", [])
        if len(mensagens) != 1 or not 1 <= len(mensagens[0].strip()) <= 80:
            self.responder(400, "Use uma mensagem fictícia de 1 a 80 caracteres.")
            return
        chave = (self.server.protocolo, self.client_address[1])
        try:
            tls = self.connection.version() if isinstance(self.connection, ssl.SSLSocket) else ""
            lab.registrar(chave, mensagens[0], tls)
        except ErroComparacao as erro:
            self.responder(429, str(erro))
            return
        self.responder(200, lab.pagina(self.server.protocolo, "Envio recebido. Volte à outra versão para comparar o mesmo texto."))


class Comparacao:
    def __init__(self, diretorio):
        self.base = Path(diretorio)
        self.lock = threading.RLock()
        self.parar = threading.Event()
        self.ativa = False
        self.servidores = []
        self.threads = []
        self.observacoes = {}
        self.envios = []
        self.pasta = None
        self.token = ""
        self.certificado_publico = b""
        self.fingerprint = ""
        self.host = "127.0.0.1"
        self.portas = {}
        self.telao = False

    def _openssl(self, *argumentos):
        executavel = shutil.which("openssl")
        if not executavel:
            raise ErroComparacao("OpenSSL não encontrado. Instale openssl para preparar o HTTPS local.")
        try:
            resultado = subprocess.run([executavel, *argumentos], cwd=self.pasta, capture_output=True,
                                       text=True, timeout=20, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired) as erro:
            raise ErroComparacao("Não foi possível gerar o certificado de laboratório.") from erro
        if resultado.returncode:
            raise ErroComparacao("OpenSSL não conseguiu gerar o certificado de laboratório.")

    def preparar(self, rede_real=False, portas=None, host="10.42.0.1"):
        if self.ativa:
            raise ErroComparacao("A comparação já está preparada. Encerre-a antes de preparar outra.")
        self.pasta = self.base / "dados" / "comparacoes" / str(uuid.uuid4())
        self.pasta.mkdir(parents=True, mode=0o700)
        self.envios = []
        self.token = secrets.token_urlsafe(24)
        self.telao = False
        self.host = str(ipaddress.IPv4Address(host)) if rede_real else "127.0.0.1"
        self.parar.clear()
        # A chave nunca é publicada e os certificados valem somente dois dias.
        self._openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-sha256", "-days", "2",
                      "-keyout", "ca.key", "-out", "ca.crt", "-subj", "/CN=Rede Aberta Laboratorio",
                      "-addext", "basicConstraints=critical,CA:TRUE,pathlen:0",
                      "-addext", "keyUsage=critical,keyCertSign,cRLSign",
                      "-addext", "subjectKeyIdentifier=hash")
        self._openssl("req", "-new", "-newkey", "rsa:2048", "-nodes", "-keyout", "servidor.key",
                      "-out", "servidor.csr", "-subj", "/CN=Rede Aberta Demonstracao")
        (self.pasta / "extensoes.cnf").write_text(
            "basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\n"
            f"extendedKeyUsage=serverAuth\nsubjectAltName={','.join('IP:' + ip for ip in dict.fromkeys(('127.0.0.1', '10.42.0.1', self.host)))},DNS:localhost\n"
            # Python 3.13+ verifica em modo estrito e exige os identificadores de chave.
            "subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\n", encoding="utf-8")
        self._openssl("x509", "-req", "-in", "servidor.csr", "-CA", "ca.crt", "-CAkey", "ca.key",
                      "-CAcreateserial", "-out", "servidor.crt", "-days", "2", "-sha256", "-extfile", "extensoes.cnf")
        for arquivo in self.pasta.iterdir():
            arquivo.chmod(0o600)
        self.certificado_publico = (self.pasta / "ca.crt").read_bytes()
        der = ssl.PEM_cert_to_DER_cert(self.certificado_publico.decode("ascii"))
        self.fingerprint = hashlib.sha256(der).hexdigest().upper()
        contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contexto.minimum_version = ssl.TLSVersion.TLSv1_2
        contexto.load_cert_chain(self.pasta / "servidor.crt", self.pasta / "servidor.key")
        portas = portas or {"http": PORTA_HTTP, "https": PORTA_HTTPS}
        try:
            for protocolo in ("http", "https"):
                destino = ServidorDestino(self, protocolo, contexto if protocolo == "https" else None)
                self.servidores.append(destino)
                ponte = Ponte(("0.0.0.0" if rede_real else "127.0.0.1", portas[protocolo]),
                              destino.server_address, self, protocolo)
                self.servidores.append(ponte)
                self.portas[protocolo] = ponte.server_address[1]
            for servidor in self.servidores:
                thread = threading.Thread(target=servidor.serve_forever, daemon=True)
                thread.start()
                self.threads.append(thread)
            self.ativa = True
        except Exception as erro:
            self.encerrar()
            raise ErroComparacao("As portas da comparação estão indisponíveis. Libere 8081 e 8443 e tente novamente.") from erro

    def pagina(self, protocolo, aviso=""):
        # O painel usa cookie em 127.0.0.1. O formulário local usa localhost
        # para que esse cookie não entre nos bytes observados do laboratório.
        host = "localhost" if self.host == "127.0.0.1" else self.host
        url_http = f"http://{host}:{self.portas.get('http', PORTA_HTTP)}"
        url_https = f"https://{host}:{self.portas.get('https', PORTA_HTTPS)}"
        # Ao ensaiar no mesmo computador, as duas URLs usam o loopback.
        mensagem = f'<p role="status">{html.escape(aviso)}</p>' if aviso else ""
        return f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Comparação {protocolo.upper()} — Rede aberta</title><style>body{{font:1.1rem sans-serif;max-width:44rem;margin:2rem auto;padding:0 1rem;color:#142e61;line-height:1.6}}a{{color:#154ac2}}nav{{display:flex;gap:1.5rem;flex-wrap:wrap}}form{{background:#edf4ff;padding:1.2rem;border-radius:1rem}}input[type=text]{{display:block;padding:.7rem;width:100%;box-sizing:border-box;margin:.7rem 0}}button{{padding:.8rem 1.2rem;background:#154ac2;color:white;border:0;border-radius:.5rem;font:inherit}}code{{overflow-wrap:anywhere}}.fingerprint{{font-size:.8rem}}</style>
<h1>Envie por {protocolo.upper()}</h1><p>Compare o mesmo texto fictício em HTTP e HTTPS. O laboratório observa os bytes TCP na entrada, antes da descriptografia HTTPS. IP, horário, mensagem e um trecho desses bytes serão guardados no notebook após concordância e envio, podendo ser projetados pela equipe.</p>
<nav><a href="{url_http}/">Versão HTTP</a><a href="{url_https}/">Versão HTTPS</a><a href="/certificado.crt">Baixar certificado do laboratório</a></nav>
<details><summary>Preparar o HTTPS no celular</summary><p>O HTTPS local usa um certificado de laboratório, válido por dois dias. No aparelho de demonstração, instale o certificado público como autoridade confiável antes de abrir a versão HTTPS. Confira a impressão SHA-256 com a equipe e remova esse certificado após a atividade. Não é necessário instalar nada para participar somente por HTTP.</p><p class="fingerprint">SHA-256: <code>{self.fingerprint}</code></p><p>Android: procure instalação de certificado de CA nas configurações de credenciais. No iPhone, instale o perfil e ative a confiança em Ajustes → Geral → Sobre → Confiança em Certificados. Os menus variam por versão.</p></details>
{mensagem}<form method="post" action="/enviar"><input type="hidden" name="sessao" value="{self.token}"><label for="mensagem">Mensagem fictícia (até 80 caracteres)</label><input id="mensagem" name="mensagem" type="text" value="OLA_TURMA" maxlength="80" required autocomplete="off"><label><input type="checkbox" name="concordo" value="sim" required> Concordo com o registro e a demonstração desses dados.</label><p>Use somente texto fictício. O HTTP permite ler o conteúdo na conexão; o HTTPS protege o conteúdo durante o transporte.</p><button>Enviar por {protocolo.upper()}</button></form></html>'''

    def registrar(self, chave, mensagem, tls):
        with self.lock:
            if len(self.envios) >= LIMITE_ENVIOS:
                raise ErroComparacao("Limite de 100 envios desta comparação atingido. Prepare outra sessão.")
            observacao = self.observacoes.get(chave)
            if observacao is None:
                raise ErroComparacao("Não foi possível associar o envio ao fluxo observado. Reabra a página.")
            fluxo = bytes(observacao.bytes)
            protocolo = observacao.protocolo
            procurado = urlencode({"mensagem": mensagem}).encode("ascii")
            legivel = procurado in fluxo
            amostra = fluxo
            if protocolo == "https":
                # Exibe o último registro TLS application_data, sem decifrá-lo.
                offset = 0
                while offset + 5 <= len(fluxo):
                    tipo = fluxo[offset]
                    tamanho = int.from_bytes(fluxo[offset + 3:offset + 5], "big")
                    if offset + 5 + tamanho > len(fluxo):
                        break
                    if tipo == 23:
                        amostra = fluxo[offset:offset + 5 + tamanho]
                    offset += 5 + tamanho
            elif b"\r\n\r\n" in fluxo:
                amostra = fluxo.split(b"\r\n\r\n", 1)[1]
            origem = "notebook" if observacao.origem == "127.0.0.1" else "participante"
            item = {"id": str(uuid.uuid4()), "protocolo": protocolo, "origem": origem,
                    "ip": observacao.origem, "horario_utc": datetime.now(timezone.utc).isoformat(),
                    "recebido": mensagem, "tls": tls, "legivel": legivel,
                    "total_bytes": len(fluxo), "truncado": observacao.truncado,
                    "hex": amostra[:192].hex(" "),
                    "texto": amostra[:240].decode("ascii", errors="replace") if protocolo == "http" else "Conteúdo de aplicação protegido por TLS.",
                    "arquivo": f"{len(self.envios) + 1:03d}-{protocolo}.bin"}
            with (self.pasta / item["arquivo"]).open("xb") as arquivo:
                arquivo.write(fluxo)
            (self.pasta / item["arquivo"]).chmod(0o600)
            with (self.pasta / "envios.jsonl").open("a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps(item, ensure_ascii=False) + "\n")
            (self.pasta / "envios.jsonl").chmod(0o600)
            self.envios.append(item)

    def enviar_notebook(self, mensagem="OLA_TURMA"):
        if not self.ativa:
            raise ErroComparacao("Prepare a comparação antes de enviar pelo notebook.")
        if not isinstance(mensagem, str) or not 1 <= len(mensagem.strip()) <= 80:
            raise ErroComparacao("Use texto fictício de 1 a 80 caracteres.")
        contexto = ssl.create_default_context(cafile=str(self.pasta / "ca.crt"))
        # Ignora SSLKEYLOGFILE do ambiente: o ponto de observação não recebe segredos TLS.
        contexto.keylog_filename = None
        campos = urlencode({"sessao": self.token, "mensagem": mensagem, "concordo": "sim"})
        for protocolo in ("http", "https"):
            if protocolo == "https":
                conexao = http.client.HTTPSConnection("127.0.0.1", self.portas[protocolo], context=contexto, timeout=8)
            else:
                conexao = http.client.HTTPConnection("127.0.0.1", self.portas[protocolo], timeout=8)
            try:
                conexao.request("POST", "/enviar", campos, {"Content-Type": "application/x-www-form-urlencoded"})
                resposta = conexao.getresponse()
                resposta.read()
                if resposta.status != 200:
                    raise ErroComparacao(f"O envio {protocolo.upper()} foi recusado pelo servidor.")
            except (OSError, http.client.HTTPException) as erro:
                raise ErroComparacao(f"Falha no envio {protocolo.upper()}: {erro}") from erro
            finally:
                conexao.close()

    def estado(self, detalhes=True):
        with self.lock:
            estado = {"ativa": self.ativa, "host": self.host, "portas": dict(self.portas),
                      "total": len(self.envios), "telao": self.telao,
                      "fingerprint": self.fingerprint, "metodo": "Fluxo TCP observado antes da descriptografia TLS"}
            if detalhes:
                estado["envios"] = [dict(item) for item in self.envios[-10:]]
            return estado

    def encerrar(self):
        self.parar.set()
        self.ativa = False
        self.telao = False
        for i, servidor in enumerate(self.servidores):
            if i < len(self.threads) and self.threads[i].is_alive():
                servidor.shutdown()
            servidor.server_close()
        for thread in self.threads:
            thread.join(timeout=3)
        self.servidores = []
        self.threads = []
        with self.lock:
            self.observacoes.clear()

    def excluir(self):
        if self.ativa:
            raise ErroComparacao("Encerre a comparação antes de excluir seus dados.")
        if self.pasta and self.pasta.parent == self.base / "dados" / "comparacoes":
            shutil.rmtree(self.pasta)
        self.pasta = None
        self.envios = []
        self.fingerprint = ""
        self.certificado_publico = b""
