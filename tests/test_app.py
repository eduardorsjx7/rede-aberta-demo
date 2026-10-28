"""Verificação local sem criar pontos de acesso nem ler dados dos participantes."""

import http.client
import json
import subprocess
import tempfile
import threading
import unittest
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlencode

from app import ServidorApp
from controle import Controle, ErroOperacao, Rede
from servidor import Handler


class RedeFalsa:
    def __init__(self):
        self.chamadas = []
        self.falha = None
        self.uuid_anterior = str(uuid.uuid4())

    def interfaces(self):
        return ['wlan0']

    def verificar(self, interface):
        if interface != 'wlan0':
            raise ErroOperacao('Interface indisponível')

    def anterior(self, interface):
        return self.uuid_anterior

    def criar(self, interface, identificador):
        self.chamadas.append(('criar', identificador))
        if self.falha == 'criar':
            raise ErroOperacao('Criação recusada')

    def ativar(self, interface, identificador):
        self.chamadas.append(('ativar', identificador))
        if self.falha == 'ativar':
            raise ErroOperacao('Ativação recusada')

    def remover(self, identificador):
        self.chamadas.append(('remover', identificador))
        if self.falha == 'remover':
            raise ErroOperacao('Remoção recusada')

    def restaurar(self, interface, identificador):
        self.chamadas.append(('restaurar', identificador))
        if self.falha == 'restaurar':
            raise ErroOperacao('Restauração recusada')

    def vizinhos(self, interface):
        return [{'ip': '10.42.0.12', 'mac': '02:00:00:00:00:12', 'estado': 'REACHABLE'}]


class TestControle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.rede = RedeFalsa()
        self.controle = Controle(self.base, self.rede)
        self.original = self.base / 'registros.jsonl'
        self.original.write_text('preservar\n')

    def tearDown(self):
        self.rede.falha = None
        self.controle.encerrar()
        self.temp.cleanup()

    def iniciar_real(self):
        # Usa um servidor real em porta efêmera e uma rede inteiramente falsa.
        fabrica = lambda endereco, handler: ThreadingHTTPServer(('127.0.0.1', 0), handler)
        with patch('controle.ThreadingHTTPServer', side_effect=fabrica):
            self.controle.iniciar({'modo': 'real', 'interface': 'wlan0', 'confirmar': True})

    def test_ensaio_nao_altera_rede_ou_arquivos(self):
        self.controle.iniciar({'modo': 'ensaio'})
        self.controle._acao('simular_aparelho', {})
        self.controle._acao('simular_envio', {})
        self.assertEqual(self.rede.chamadas, [])
        self.assertEqual(self.controle.estado()['envios'], 1)
        self.assertEqual(self.controle.estado()['observados'], 1)
        self.assertIsNone(self.controle.log_path)
        self.assertEqual(self.original.read_text(), 'preservar\n')

    def test_publico_recebe_detalhes_so_apos_confirmacao(self):
        self.controle.iniciar({'modo': 'ensaio'})
        self.controle._acao('simular_envio', {})
        self.assertNotIn('registros', self.controle.estado(publico=True))
        with self.assertRaises(ErroOperacao):
            self.controle._acao('revelar', {})
        self.controle._acao('revelar', {'confirmar': True})
        self.assertEqual(len(self.controle.estado(publico=True)['registros']), 1)
        self.controle._acao('etapa', {'etapa': 1})
        self.assertNotIn('registros', self.controle.estado(publico=True))

    def test_validacao_de_etapas(self):
        for etapa in (-1, 7, True, '2'):
            with self.assertRaises(ErroOperacao):
                self.controle._acao('etapa', {'etapa': etapa})

    def test_modo_real_exige_confirmacao(self):
        with self.assertRaises(ErroOperacao):
            self.controle.iniciar({'modo': 'real', 'interface': 'wlan0'})
        self.assertEqual(self.rede.chamadas, [])

    def test_sessao_real_preserva_original_e_remove_so_proprio_perfil(self):
        self.iniciar_real()
        perfil = self.controle.perfil
        log = self.controle.log_path
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)
        self.assertTrue(self.controle.estado()['servidor_ativo'])
        self.controle._acao('atualizar', {})
        self.assertEqual(self.controle.estado()['observados'], 1)
        self.controle.encerrar()
        self.assertTrue(log.exists())
        self.assertEqual(self.rede.chamadas[-2:], [('remover', perfil), ('restaurar', self.rede.uuid_anterior)])
        self.assertFalse(self.controle.arquivo_pendente.exists())
        self.assertEqual(self.original.read_text(), 'preservar\n')

    def test_falha_na_ativacao_desfaz_recursos(self):
        self.rede.falha = 'ativar'
        with self.assertRaises(ErroOperacao):
            self.iniciar_real()
        self.assertFalse(self.controle.ativo)
        self.assertIsNone(self.controle.servidor)
        self.assertIsNone(self.controle.perfil)
        self.assertEqual(self.rede.chamadas[-1], ('restaurar', self.rede.uuid_anterior))

    def test_encerramento_preserva_conexao_escolhida_fora_do_app(self):
        self.iniciar_real()
        with patch.object(self.rede, 'anterior', return_value=str(uuid.uuid4())):
            self.controle.encerrar()
        self.assertFalse(any(acao == 'restaurar' for acao, _ in self.rede.chamadas))
        self.assertFalse(self.controle.conexao_anterior)

    def test_porta_ocupada_nao_mexe_na_rede(self):
        with patch('controle.ThreadingHTTPServer', side_effect=OSError('Address in use')):
            with self.assertRaisesRegex(ErroOperacao, '8080'):
                self.controle.iniciar({'modo': 'real', 'interface': 'wlan0', 'confirmar': True})
        self.assertEqual(self.rede.chamadas, [])
        self.assertFalse(self.controle.perfil)

    def test_falha_na_limpeza_permanece_recuperavel(self):
        self.iniciar_real()
        perfil = self.controle.perfil
        self.rede.falha = 'remover'
        with self.assertRaises(ErroOperacao):
            self.controle.encerrar()
        self.assertTrue(self.controle.estado()['limpeza_pendente'])
        recuperado = Controle(self.base, self.rede)
        self.assertEqual(recuperado.perfil, perfil)
        self.assertEqual(recuperado.log_path, self.controle.log_path)
        self.rede.falha = None
        recuperado.encerrar()
        self.assertFalse(recuperado.arquivo_pendente.exists())

    def test_exclusao_exige_encerrar_e_preserva_outros_arquivos(self):
        self.iniciar_real()
        log = self.controle.log_path
        with self.assertRaises(ErroOperacao):
            self.controle._acao('excluir', {'confirmar': True})
        self.controle.encerrar()
        with self.assertRaises(ErroOperacao):
            self.controle._acao('excluir', {})
        self.controle._acao('excluir', {'confirmar': True})
        self.assertFalse(log.exists())
        self.assertEqual(self.original.read_text(), 'preservar\n')

    def test_acao_desconhecida_e_clique_duplicado(self):
        with self.assertRaises(ErroOperacao):
            self.controle.solicitar('shell', {})
        aguardando = threading.Event()
        liberar = threading.Event()
        def tarefa(*args):
            aguardando.set()
            liberar.wait(2)
        with patch.object(self.controle, '_acao', side_effect=tarefa):
            self.controle.solicitar('verificar', {})
            self.assertTrue(aguardando.wait(1))
            try:
                with self.assertRaises(ErroOperacao):
                    self.controle.solicitar('verificar', {})
            finally:
                liberar.set()
                self.controle.worker.join(2)
        self.assertFalse(self.controle.ocupado)

    def test_arquivo_parcial_nao_quebra_consulta(self):
        self.iniciar_real()
        self.controle.log_path.write_text('{"ip":"10.42.0.12"}\n{"ip":')
        self.assertEqual(self.controle.estado()['envios'], 1)

    def test_recuperacao_recusa_arquivo_fora_das_sessoes(self):
        self.controle.arquivo_pendente.parent.mkdir(parents=True, exist_ok=True)
        self.controle.arquivo_pendente.write_text(json.dumps({
            'perfil': str(uuid.uuid4()), 'anterior': None,
            'interface': 'wlan0', 'arquivo': str(self.original),
        }))
        recuperado = Controle(self.base, self.rede)
        self.assertIsNone(recuperado.log_path)
        self.assertIsNone(recuperado.perfil)
        self.assertTrue(recuperado.erro)
        self.assertEqual(self.original.read_text(), 'preservar\n')

    def test_nao_aceita_novas_operacoes_ao_fechar(self):
        self.controle.fechando = True
        with self.assertRaisesRegex(ErroOperacao, 'encerrando'):
            self.controle.solicitar('iniciar', {'modo': 'ensaio'})


class TestHttp(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.controle = Controle(self.temp.name, RedeFalsa())
        self.server = ServidorApp(('127.0.0.1', 0), self.controle)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.cookie = f'rede_sessao={self.server.token}'

    def tearDown(self):
        if self.controle.worker:
            self.controle.worker.join(3)
        self.controle.encerrar()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def request(self, path, dados=None, headers=None, autenticado=True):
        cabecalhos = {'Origin': self.server.origem, 'Content-Type': 'application/json'}
        if autenticado:
            cabecalhos['Cookie'] = self.cookie
        cabecalhos.update(headers or {})
        conn = http.client.HTTPConnection('127.0.0.1', self.server.porta, timeout=3)
        conn.request('POST' if dados is not None else 'GET', path,
                     json.dumps(dados) if dados is not None else None, cabecalhos)
        resposta = conn.getresponse()
        retorno = resposta.status, resposta.read(), dict(resposta.getheaders())
        conn.close()
        return retorno

    def test_autenticacao_e_cookie(self):
        self.assertEqual(self.request('/api/estado', autenticado=False)[0], 401)
        self.assertEqual(self.request('/api/sessao', {'token': 'incorreto'}, autenticado=False)[0], 401)
        status, _, headers = self.request('/api/sessao', {'token': self.server.token}, autenticado=False)
        self.assertEqual(status, 200)
        self.assertIn('HttpOnly; SameSite=Strict', headers['Set-Cookie'])

    def test_recusa_outros_hosts_e_origens(self):
        self.assertEqual(self.request('/api/estado', headers={'Host': 'evil.example'})[0], 403)
        self.assertEqual(self.request('/api/acao', {'acao': 'iniciar'}, headers={'Origin': 'http://evil.example'})[0], 403)
        self.assertEqual(self.request('/api/acao', {'acao': 'iniciar'}, headers={'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.server.server_address[0], '127.0.0.1')

    def test_rejeita_json_invalido_e_acoes_arbitrarias(self):
        self.assertEqual(self.request('/api/acao', ['iniciar'])[0], 400)
        self.assertEqual(self.request('/api/acao', {'acao': 'executar', 'comando': 'touch /tmp/falha'})[0], 409)
        self.assertEqual(self.request('/api/acao', {'acao': []})[0], 409)

    def test_api_publica_oculta_detalhes(self):
        self.controle.iniciar({'modo': 'ensaio'})
        self.controle._acao('simular_envio', {})
        self.assertNotIn('registros', json.loads(self.request('/api/telao')[1]))
        self.assertEqual(len(json.loads(self.request('/api/estado')[1])['registros']), 1)

    def test_arquivos_permitidos_e_cabecalhos(self):
        for path in ('/', '/telao', '/estilo.css', '/app.js', '/conteudo.js', '/icone.svg'):
            status, _, headers = self.request(path)
            self.assertEqual(status, 200)
            self.assertEqual(headers['Cache-Control'], 'no-store')
        for path in ('/registros.jsonl', '/dados/app.json', '/../servidor.py', '/api/desconhecida'):
            self.assertEqual(self.request(path)[0], 404)

    def test_apresentacao_e_telao_embutido(self):
        status, corpo, headers = self.request('/apresentacao')
        self.assertEqual(status, 200)
        self.assertIn(b'telao-vivo', corpo)
        self.assertIn("frame-src 'self'", headers['Content-Security-Policy'])
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        # Só o telão pode ser exibido dentro da apresentação; o painel continua sem moldura.
        self.assertIn("frame-ancestors 'self'", self.request('/telao')[2]['Content-Security-Policy'])
        self.assertIn("frame-ancestors 'none'", self.request('/')[2]['Content-Security-Policy'])
        self.assertNotIn('unsafe-inline', self.request('/telao')[2]['Content-Security-Policy'])


class TestParticipacao(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.log = Path(self.temp.name) / 'envios.jsonl'
        handler = type('HandlerTeste', (Handler,), {'log_path': self.log})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def request(self, path='/', campos=None, corpo=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        if campos is not None:
            corpo = urlencode(campos).encode()
        conn.request('POST' if corpo is not None else 'GET', path, corpo,
                     {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Teste fictício'})
        resposta = conn.getresponse()
        status, data = resposta.status, resposta.read()
        conn.close()
        return status, data

    def test_sem_consentimento_nao_grava(self):
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.request('/registrar', {'apelido': 'Teste'})[0], 400)
        self.assertFalse(self.log.exists())

    def test_envio_valido_e_limites(self):
        self.assertEqual(self.request('/registrar', {'concordo': 'sim', 'apelido': 'Visitante Azul'})[0], 200)
        item = json.loads(self.log.read_text())
        self.assertEqual(set(item), {'horario_utc', 'ip', 'navegador', 'apelido'})
        self.assertEqual(item['apelido'], 'Visitante Azul')
        self.assertEqual(self.request('/registrar', {'concordo': 'sim', 'apelido': 'a' * 41})[0], 400)
        self.assertEqual(self.request('/registrar', corpo=b'x' * 2049)[0], 413)
        self.assertEqual(self.request('/registrar', corpo=b'\xff')[0], 400)
        self.assertEqual(len(self.log.read_text().splitlines()), 1)

    def test_caminhos_desconhecidos(self):
        self.assertEqual(self.request('/api/estado')[0], 404)
        self.assertEqual(self.request('/api/acao', {})[0], 404)


class TestComandos(unittest.TestCase):
    @patch('controle.shutil.which', side_effect=lambda nome: '/usr/bin/' + nome)
    @patch('controle.subprocess.run')
    def test_autorizacao_grafica_sem_shell(self, run, which):
        run.side_effect = [subprocess.CompletedProcess([], 1, '', 'Not authorized'),
                           subprocess.CompletedProcess([], 126, '', '')]
        with self.assertRaisesRegex(ErroOperacao, 'cancelada'):
            Rede().executar(['nmcli', 'connection', 'add'], autorizar=True)
        self.assertEqual(run.call_args_list[1].args[0][:3], ['/usr/bin/pkexec', '--disable-internal-agent', '/usr/bin/nmcli'])
        self.assertNotIn('shell', run.call_args.kwargs)

    @patch('controle.shutil.which', return_value='/usr/bin/nmcli')
    @patch('controle.subprocess.run', side_effect=subprocess.TimeoutExpired(['nmcli'], 40))
    def test_timeout(self, run, which):
        with self.assertRaisesRegex(ErroOperacao, 'demorou'):
            Rede().executar(['nmcli', 'general', 'status'])

    @patch('controle.subprocess.run')
    @patch('controle.sys.platform', 'darwin')
    def test_sem_linux_explica_e_nao_executa_comandos(self, run):
        for operacao in (lambda rede: rede.interfaces(), lambda rede: rede.verificar('wlan0')):
            with self.assertRaisesRegex(ErroOperacao, 'precisa de Linux'):
                operacao(Rede())
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
