"""Operações da demonstração, sem privilégios no servidor HTTP de controle."""

import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path

from servidor import Handler
from comparacao import Comparacao, ErroComparacao


SSID = "EXTENSAO-REDE-ABERTA"
URL_PARTICIPANTES = "http://10.42.0.1:8080"
TOTAL_ETAPAS = 7


class ErroOperacao(Exception):
    pass


MENSAGEM_SEM_LINUX = ("A demonstração real (rede Wi-Fi aberta) precisa de Linux com NetworkManager e um adaptador "
                      "com modo AP. Neste computador, use o Ensaio com dados fictícios e a comparação HTTP × HTTPS "
                      "pelo notebook.")
MENSAGEM_MAC_SEM_REDE = ("Ligue o Compartilhamento de Internet: Ajustes do Sistema › Geral › Compartilhamento › ⓘ ao lado "
                         "de Compartilhamento de Internet. Em “Compartilhar sua conexão de”, troque Wi-Fi por USB do "
                         "iPhone, Ponte Thunderbolt ou um Adaptador Ethernet: com Wi-Fi ali, a opção Wi-Fi não aparece "
                         "embaixo. Em “Para dispositivos que usam”, ative Wi-Fi, ajuste as Opções de Wi-Fi e ative o "
                         "Compartilhamento de Internet no topo. Depois clique em Verificar equipamento de novo.")


class Rede:
    @staticmethod
    def exigir_linux():
        if not sys.platform.startswith("linux"):
            raise ErroOperacao(MENSAGEM_SEM_LINUX)

    def executar(self, argumentos, autorizar=False):
        programa = shutil.which(argumentos[0])
        if not programa:
            raise ErroOperacao(f"Programa não encontrado: {argumentos[0]}.")
        comando = [programa, *argumentos[1:]]
        ambiente = {**os.environ, "LC_ALL": "C"}
        try:
            resultado = subprocess.run(comando, capture_output=True, text=True,
                                       timeout=40, env=ambiente, stdin=subprocess.DEVNULL)
            if resultado.returncode and autorizar and re.search(
                    r"not authorized|permission|not permitted|insufficient", resultado.stderr, re.I):
                pkexec = shutil.which("pkexec")
                if not pkexec:
                    raise ErroOperacao("É necessária autorização do sistema, mas pkexec não está instalado.")
                resultado = subprocess.run(
                    [pkexec, "--disable-internal-agent", *comando], capture_output=True,
                    text=True, timeout=120, env=ambiente, stdin=subprocess.DEVNULL)
                if resultado.returncode in (126, 127):
                    raise ErroOperacao("Autorização cancelada ou recusada. Tente novamente e autorize na janela do sistema.")
            if resultado.returncode:
                raise ErroOperacao((resultado.stderr.strip() or "O comando não foi concluído.")[:700])
            return resultado.stdout.strip()
        except subprocess.TimeoutExpired as erro:
            raise ErroOperacao("O sistema demorou a responder. Verifique a rede e tente novamente.") from erro
        except OSError as erro:
            raise ErroOperacao(f"Não foi possível executar {argumentos[0]}: {erro}") from erro

    def interfaces(self):
        self.exigir_linux()
        saida = self.executar(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"])
        return [linha.split(":", 2)[0] for linha in saida.splitlines()
                if len(linha.split(":", 2)) == 3 and linha.split(":", 2)[1] == "wifi"]

    def verificar(self, interface):
        self.exigir_linux()
        if interface not in self.interfaces():
            raise ErroOperacao("Selecione uma interface Wi-Fi disponível.")
        suporte = self.executar(["nmcli", "-g", "WIFI-PROPERTIES.AP", "device", "show", interface])
        if suporte != "yes":
            raise ErroOperacao("Este adaptador não informa suporte ao modo ponto de acesso (AP).")
        if not shutil.which("ip"):
            raise ErroOperacao("Instale iproute2 para consultar os aparelhos observados.")

    def anterior(self, interface):
        valor = self.executar(["nmcli", "-g", "GENERAL.CON-UUID", "device", "show", interface])
        return valor if re.fullmatch(r"[a-fA-F0-9-]{36}", valor) else None

    def criar(self, interface, identificador):
        self.executar([
            "nmcli", "connection", "add", "type", "wifi", "ifname", interface,
            "con-name", f"Extensao-App-{identificador[:8]}", "connection.uuid", identificador,
            "autoconnect", "no", "ssid", SSID, "802-11-wireless.mode", "ap",
            "802-11-wireless.band", "bg", "802-11-wireless.ap-isolation", "yes",
            "ipv4.method", "shared", "ipv4.addresses", "10.42.0.1/24", "ipv6.method", "disabled",
        ], autorizar=True)

    def ativar(self, interface, identificador):
        self.executar(["nmcli", "--wait", "25", "connection", "up", "uuid", identificador,
                       "ifname", interface], autorizar=True)

    def remover(self, identificador):
        # Apagar pelo UUID também desativa uma conexão que esteja em uso.
        existentes = self.executar(["nmcli", "-g", "UUID", "connection", "show"]).splitlines()
        if identificador in existentes:
            self.executar(["nmcli", "--wait", "25", "connection", "delete", "uuid", identificador], autorizar=True)

    def restaurar(self, interface, identificador):
        self.ativar(interface, identificador)

    def vizinhos(self, interface):
        saida = self.executar(["ip", "-j", "neigh", "show", "dev", interface])
        return [{"ip": item.get("dst", ""), "mac": item.get("lladdr", "—"),
                 "estado": ", ".join(item.get("state", []))} for item in json.loads(saida)]

    def endereco(self, interface):
        return "10.42.0.1"

    def nome_rede(self, interface):
        return SSID


class RedeMac(Rede):
    """Modo real no macOS: usa a rede Wi-Fi do Compartilhamento de Internet, ligada pela equipe nos Ajustes.

    O app não altera ajustes do sistema. Só aceita as interfaces bridge do compartilhamento, para observar
    apenas aparelhos que entraram na rede da demonstração.
    """

    def enderecos(self):
        atual, enderecos = None, {}
        for linha in self.executar(["ifconfig"]).splitlines():
            nome = re.match(r"^([a-z0-9]+): flags=", linha)
            if nome:
                atual = nome.group(1)
                continue
            ipv4 = re.match(r"\s+inet (\d+\.\d+\.\d+\.\d+) ", linha)
            if atual and ipv4 and atual not in enderecos:
                enderecos[atual] = ipv4.group(1)
        return enderecos

    def interfaces(self):
        return sorted(nome for nome in self.enderecos() if nome.startswith("bridge") and nome != "bridge0")

    def verificar(self, interface):
        if interface not in self.interfaces():
            raise ErroOperacao(MENSAGEM_MAC_SEM_REDE)
        if not shutil.which("arp"):
            raise ErroOperacao("O comando arp não foi encontrado para consultar os aparelhos observados.")

    def anterior(self, interface):
        return None

    # A rede é do Compartilhamento de Internet: o app não cria, ativa nem remove conexões no macOS.
    def criar(self, interface, identificador):
        pass

    def ativar(self, interface, identificador):
        pass

    def remover(self, identificador):
        pass

    def restaurar(self, interface, identificador):
        pass

    def vizinhos(self, interface):
        proprio = self.endereco(interface)
        aparelhos = []
        for linha in self.executar(["arp", "-an", "-i", interface]).splitlines():
            item = re.match(r"\? \((\d+\.\d+\.\d+\.\d+)\) at (\S+)", linha)
            if not item or item.group(1) == proprio:
                continue
            ip, mac = item.groups()
            # Ignora endereços de grupo (multicast/broadcast), que não são aparelhos.
            if mac.startswith(("1:0:5e", "ff:ff")) or ip.endswith(".255") or ipaddress.ip_address(ip).is_multicast:
                continue
            completo = mac != "(incomplete)"
            aparelhos.append({"ip": ip, "mac": mac if completo else "—", "estado": "OBSERVADO" if completo else "INCOMPLETO"})
        return aparelhos

    def endereco(self, interface):
        return self.enderecos().get(interface)

    def nome_rede(self, interface):
        try:
            saida = self.executar(["defaults", "read", "/Library/Preferences/SystemConfiguration/com.apple.nat", "NAT"])
        except ErroOperacao:
            return None
        nome = re.search(r'NetworkName = "?([^";\n]+)"?;', saida)
        return nome.group(1).strip() if nome else None


class Controle:
    def __init__(self, diretorio, rede=None):
        # Caminho real: no macOS, /var aponta para /private/var e as comparações de pasta precisam bater.
        self.diretorio = Path(diretorio).resolve()
        self.rede = rede or (RedeMac() if sys.platform == "darwin" else Rede())
        self.ssid = SSID
        self.host_rede = "10.42.0.1"
        self.lock = threading.RLock()
        self.ocupado = False
        self.fechando = False
        self.modo = "ensaio"
        self.ativo = False
        self.etapa = 0
        self.revelado = False
        self.interfaces = []
        self.interface = ""
        self.vizinhos = []
        self.ficticios = []
        self.log_path = None
        self.perfil = None
        self.conexao_anterior = None
        self.servidor = None
        self.thread_servidor = None
        self.mensagem = "Comece verificando o equipamento ou inicie um ensaio."
        self.erro = ""
        self.eventos = []
        self.worker = None
        self.comparacao = Comparacao(self.diretorio)
        self.recuperar_pendente()

    @property
    def arquivo_pendente(self):
        return self.diretorio / "dados" / "atividade.json"

    def salvar_pendente(self):
        caminho = self.arquivo_pendente
        caminho.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self.perfil and not self.conexao_anterior:
            caminho.unlink(missing_ok=True)
            return
        dados = {"perfil": self.perfil, "anterior": self.conexao_anterior,
                 "interface": self.interface, "arquivo": str(self.log_path) if self.log_path else None}
        temporario = caminho.with_suffix(".tmp")
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo)
        temporario.chmod(0o600)
        temporario.replace(caminho)

    def recuperar_pendente(self):
        try:
            dados = json.loads(self.arquivo_pendente.read_text(encoding="utf-8"))
            for campo in ("perfil", "anterior"):
                valor = dados.get(campo)
                if valor is not None and not re.fullmatch(r"[a-fA-F0-9-]{36}", str(valor)):
                    raise ValueError("UUID inválido")
            interface = dados["interface"]
            if not isinstance(interface, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", interface):
                raise ValueError("Interface inválida")
            arquivo = None
            if dados.get("arquivo"):
                arquivo = Path(dados["arquivo"]).resolve()
                if arquivo.parent != (self.diretorio / "dados" / "sessoes").resolve():
                    raise ValueError("Arquivo fora da pasta de sessões")
            self.perfil = dados.get("perfil")
            self.conexao_anterior = dados.get("anterior")
            self.interface = interface
            self.log_path = arquivo
            self.modo = "real"
            self.mensagem = "Há uma atividade interrompida. Clique em Encerrar dinâmica para limpar a rede e restaurar a conexão."
        except FileNotFoundError:
            pass
        except (OSError, ValueError, KeyError, TypeError):
            self.erro = "Não foi possível recuperar o estado da atividade anterior. Verifique dados/atividade.json."

    def registrar_evento(self, texto):
        with self.lock:
            self.eventos = ([{"hora": datetime.now().strftime("%H:%M:%S"), "texto": texto}]
                            + self.eventos)[:15]

    def registros(self):
        if self.modo == "ensaio":
            return list(self.ficticios)
        if not self.log_path or not self.log_path.exists():
            return []
        resultado = []
        with self.log_path.open(encoding="utf-8") as arquivo:
            for linha in arquivo:
                try:
                    item = json.loads(linha)
                    if isinstance(item, dict):
                        resultado.append({campo: str(item.get(campo, "")) for campo in
                                          ("horario_utc", "ip", "navegador", "apelido")})
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
        return resultado

    def estado(self, publico=False):
        with self.lock:
            registros = self.registros()
            dados = {
                "modo": self.modo, "ativo": self.ativo, "ocupado": self.ocupado,
                "etapa": self.etapa, "revelado": self.revelado,
                "total_etapas": TOTAL_ETAPAS,
                "ssid": self.ssid, "url": f"http://{self.host_rede}:8080",
                "plataforma": "macos" if isinstance(self.rede, RedeMac) else "linux",
                "envios": len(registros), "observados": len(self.vizinhos),
                "servidor_ativo": bool(self.thread_servidor and self.thread_servidor.is_alive()),
                "comparacao": self.comparacao.estado(detalhes=not publico or self.comparacao.telao),
            }
            if not publico or self.revelado:
                dados.update(vizinhos=list(self.vizinhos), registros=registros[-100:])
            if not publico:
                dados.update(interfaces=list(self.interfaces), interface=self.interface,
                             mensagem=self.mensagem, erro=self.erro, eventos=list(self.eventos),
                             arquivo=str(self.log_path) if self.log_path else "",
                             limpeza_pendente=bool(self.perfil or self.conexao_anterior))
            return dados

    def solicitar(self, acao, dados):
        permitidas = {"verificar", "iniciar", "encerrar", "atualizar", "etapa", "revelar",
                      "ocultar", "simular_aparelho", "simular_envio", "excluir",
                      "preparar_comparacao", "enviar_notebook", "encerrar_comparacao",
                      "mostrar_comparacao", "ocultar_comparacao", "excluir_comparacao"}
        if acao not in permitidas:
            raise ErroOperacao("Ação desconhecida.")
        with self.lock:
            if self.fechando:
                raise ErroOperacao("O aplicativo está encerrando. Aguarde e reabra pelo atalho.")
            if self.ocupado:
                raise ErroOperacao("Aguarde a operação em andamento.")
            self.ocupado = True
            self.erro = ""
        self.worker = threading.Thread(target=self._trabalhar, args=(acao, dados), daemon=True)
        self.worker.start()

    def _trabalhar(self, acao, dados):
        try:
            self._acao(acao, dados)
        except Exception as erro:
            with self.lock:
                self.erro = str(erro) if isinstance(erro, (ErroOperacao, ErroComparacao, OSError)) else "Falha inesperada ao executar a operação."
                self.mensagem = "A operação não foi concluída."
            self.registrar_evento(self.erro)
        finally:
            with self.lock:
                self.ocupado = False

    def _acao(self, acao, dados):
        if acao == "verificar":
            interfaces = self.rede.interfaces()
            with self.lock:
                self.interfaces = interfaces
            selecionada = dados.get("interface") or (interfaces[0] if interfaces else "")
            self.rede.verificar(selecionada)
            self.definir_rede(selecionada)
            with self.lock:
                self.interface = selecionada
                if isinstance(self.rede, RedeMac):
                    self.mensagem = (f"Rede pronta: “{self.ssid}” pelo Compartilhamento de Internet, página em "
                                     f"http://{self.host_rede}:8080. O app não muda ajustes do Mac.")
                else:
                    self.mensagem = "Equipamento pronto: adaptador com suporte AP. A rede atual foi preservada."
        elif acao == "iniciar":
            self.iniciar(dados)
        elif acao == "encerrar":
            self.encerrar()
        elif acao == "atualizar":
            if self.ativo and self.modo == "real":
                vizinhos = self.rede.vizinhos(self.interface)
                with self.lock:
                    self.vizinhos = vizinhos
                    self.mensagem = "Tabela de vizinhos atualizada."
        elif acao == "etapa":
            etapa = dados.get("etapa")
            if type(etapa) is not int or not 0 <= etapa < TOTAL_ETAPAS:
                raise ErroOperacao("Etapa inválida.")
            with self.lock:
                self.etapa = etapa
                self.revelado = False
                self.comparacao.telao = False
        elif acao in ("revelar", "ocultar"):
            if acao == "revelar" and dados.get("confirmar") is not True:
                raise ErroOperacao("Confirme a exibição dos dados no telão.")
            with self.lock:
                self.revelado = acao == "revelar"
                if self.revelado:
                    self.comparacao.telao = False
        elif acao in ("simular_aparelho", "simular_envio"):
            if self.modo != "ensaio" or not self.ativo:
                raise ErroOperacao("Inicie um ensaio para usar dados fictícios.")
            with self.lock:
                if acao == "simular_aparelho":
                    numero = len(self.vizinhos) + 1
                    self.vizinhos.append({"ip": f"10.42.0.{numero + 10}", "mac": f"02:00:00:00:{numero // 256:02x}:{numero % 256:02x}", "estado": "SIMULADO"})
                else:
                    self.ficticios.append({"horario_utc": datetime.now(timezone.utc).isoformat(),
                                           "ip": "10.42.0.11", "navegador": "Navegador de exemplo (fictício)",
                                           "apelido": f"Visitante {len(self.ficticios) + 1}"})
                self.mensagem = "Exemplo fictício adicionado ao ensaio."
        elif acao == "excluir":
            if self.ativo or self.perfil or self.conexao_anterior or dados.get("confirmar") is not True:
                raise ErroOperacao("Encerre a dinâmica e confirme a exclusão dos dados da sessão.")
            with self.lock:
                if self.log_path and self.log_path.exists():
                    self.log_path.unlink()
                self.ficticios = []
                self.log_path = None
                self.vizinhos = []
                self.revelado = False
                self.mensagem = "Dados desta sessão excluídos."
        elif acao == "preparar_comparacao":
            self.comparacao.preparar(rede_real=self.ativo and self.modo == "real", host=self.host_rede)
            if self.servidor:
                self.servidor.RequestHandlerClass.comparacao_url = f"http://{self.host_rede}:8081/"
            self.mensagem = "Comparação HTTP/HTTPS pronta. Use o formulário no celular ou envie pelo notebook."
        elif acao == "enviar_notebook":
            if dados.get("confirmar") is not True:
                raise ErroOperacao("Confirme o registro da mensagem fictícia e dos bytes observados.")
            self.comparacao.enviar_notebook(dados.get("mensagem", "OLA_TURMA"))
            self.mensagem = "O notebook enviou o mesmo texto por HTTP e HTTPS. Compare os bytes observados."
        elif acao == "encerrar_comparacao":
            self.comparacao.encerrar()
            if self.servidor:
                self.servidor.RequestHandlerClass.comparacao_url = ""
            self.mensagem = "Comparação encerrada. Os dados foram preservados."
        elif acao == "excluir_comparacao":
            if dados.get("confirmar") is not True:
                raise ErroOperacao("Confirme a exclusão dos dados desta comparação.")
            self.comparacao.excluir()
            self.mensagem = "Dados e certificados desta comparação excluídos."
        elif acao in ("mostrar_comparacao", "ocultar_comparacao"):
            if acao == "mostrar_comparacao" and dados.get("confirmar") is not True:
                raise ErroOperacao("Confirme a exibição dos envios da comparação no telão.")
            self.comparacao.telao = acao == "mostrar_comparacao"
            self.revelado = False
        self.registrar_evento(f"{acao.capitalize()}: operação concluída.")

    def definir_rede(self, interface):
        """Guarda o nome da rede e o endereço que os participantes usam (variam no macOS)."""
        endereco = getattr(self.rede, "endereco", lambda _: None)(interface) or "10.42.0.1"
        try:
            ipaddress.IPv4Address(endereco)
        except ValueError:
            endereco = "10.42.0.1"
        nome = getattr(self.rede, "nome_rede", lambda _: None)(interface) or SSID
        with self.lock:
            self.host_rede = endereco
            self.ssid = nome[:64]

    def iniciar(self, dados):
        modo = dados.get("modo", "ensaio")
        if modo not in ("ensaio", "real"):
            raise ErroOperacao("Modo inválido.")
        if self.ativo or self.perfil or self.conexao_anterior:
            raise ErroOperacao("Encerre a atividade anterior antes de iniciar outra.")
        if modo == "real" and dados.get("confirmar") is not True:
            raise ErroOperacao("Confirme a troca da conexão Wi-Fi antes de iniciar.")
        if modo == "real":
            interface = dados.get("interface", "")
            self.rede.verificar(interface)
            anterior = self.rede.anterior(interface)
            self.definir_rede(interface)
        self.comparacao.encerrar()
        with self.lock:
            self.modo = modo
            self.etapa = 0
            self.revelado = False
            self.vizinhos = []
            self.ficticios = []
            self.log_path = None
        if modo == "ensaio":
            with self.lock:
                self.ativo = True
                self.mensagem = "Ensaio iniciado. Nenhuma configuração de rede foi alterada."
            return
        pasta = self.diretorio / "dados" / "sessoes"
        pasta.mkdir(parents=True, exist_ok=True, mode=0o700)
        identificador = str(uuid.uuid4())
        log_path = pasta / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{identificador[:8]}.jsonl"
        with log_path.open("x", encoding="utf-8"):
            pass
        log_path.chmod(0o600)

        class HandlerSessao(Handler):
            def setup(self):
                super().setup()
                self.connection.settimeout(5)

        HandlerSessao.log_path = log_path
        try:
            # Reserva a porta antes de trocar a rede. O bind em todas as interfaces
            # atende também o acesso local, mas nunca expõe o painel de controle.
            servidor = ThreadingHTTPServer(("0.0.0.0", 8080), HandlerSessao)
            servidor.daemon_threads = True
        except OSError as erro:
            log_path.unlink(missing_ok=True)
            raise ErroOperacao("A porta 8080 está ocupada ou indisponível. Encerre o outro servidor e tente novamente.") from erro
        with self.lock:
            self.interface = interface
            self.log_path = log_path
            self.conexao_anterior = anterior
            self.perfil = identificador
            self.servidor = servidor
        try:
            self.salvar_pendente()
            self.rede.criar(interface, identificador)
            self.rede.ativar(interface, identificador)
            thread = threading.Thread(target=servidor.serve_forever, daemon=True)
            thread.start()
            with self.lock:
                self.thread_servidor = thread
                self.ativo = True
                self.mensagem = "Rede e página prontas. Abra o telão para conduzir a dinâmica."
        except Exception as erro:
            try:
                self.encerrar()
            except Exception as limpeza:
                raise ErroOperacao(f"Falha ao iniciar: {erro}. Limpeza pendente: {limpeza}. Clique em Encerrar novamente.") from erro
            raise ErroOperacao(f"Não foi possível iniciar: {erro}. Os recursos criados foram desfeitos.") from erro

    def encerrar(self):
        self.comparacao.encerrar()
        with self.lock:
            self.revelado = False
            self.ativo = False
            servidor, thread = self.servidor, self.thread_servidor
            self.servidor = None
            self.thread_servidor = None
        if servidor:
            if thread and thread.is_alive():
                servidor.shutdown()
            servidor.server_close()
            if thread:
                thread.join(timeout=3)
        atual = self.rede.anterior(self.interface) if self.conexao_anterior else None
        preservar_atual = bool(atual and atual not in (self.perfil, self.conexao_anterior))
        if self.perfil:
            self.rede.remover(self.perfil)
            with self.lock:
                self.perfil = None
            self.salvar_pendente()
        if self.conexao_anterior:
            if not preservar_atual:
                self.rede.restaurar(self.interface, self.conexao_anterior)
            with self.lock:
                self.conexao_anterior = None
            self.salvar_pendente()
        self.salvar_pendente()
        with self.lock:
            self.mensagem = ("Dinâmica encerrada. A conexão Wi-Fi selecionada por você foi preservada."
                             if preservar_atual else "Dinâmica encerrada. Os registros foram preservados.")
