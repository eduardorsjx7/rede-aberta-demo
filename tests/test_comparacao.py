"""Testes de HTTP/TLS reais em portas locais efêmeras, sem captura privilegiada."""

import http.client
import json
import socket
import ssl
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import urlencode

from comparacao import Comparacao, ErroComparacao, LIMITE_FLUXO, Observacao
from controle import Controle, ErroOperacao


class TestComparacao(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.lab = Comparacao(self.base)
        self.lab.preparar(portas={'http': 0, 'https': 0})

    def tearDown(self):
        self.lab.encerrar()
        self.temp.cleanup()

    def request(self, protocolo='http', caminho='/', campos=None, confiavel=True):
        if protocolo == 'https':
            contexto = ssl.create_default_context(cafile=str(self.lab.pasta / 'ca.crt')) if confiavel else ssl.create_default_context()
            conexao = http.client.HTTPSConnection('127.0.0.1', self.lab.portas[protocolo], context=contexto, timeout=5)
        else:
            conexao = http.client.HTTPConnection('127.0.0.1', self.lab.portas[protocolo], timeout=5)
        try:
            conexao.request('POST' if campos is not None else 'GET', caminho,
                            urlencode(campos) if campos is not None else None,
                            {'Content-Type': 'application/x-www-form-urlencoded'})
            resposta = conexao.getresponse()
            return resposta.status, resposta.read()
        finally:
            conexao.close()

    def test_envios_notebook_mostram_http_legivel_e_tls_real(self):
        self.lab.enviar_notebook('OLA_TURMA_COMPARACAO')
        http, https = self.lab.estado()['envios']
        self.assertEqual([http['protocolo'], https['protocolo']], ['http', 'https'])
        self.assertTrue(http['legivel'])
        self.assertFalse(https['legivel'])
        self.assertIn(https['tls'], ('TLSv1.2', 'TLSv1.3'))
        self.assertEqual(http['recebido'], https['recebido'])
        self.assertIn(b'mensagem=OLA_TURMA_COMPARACAO', (self.lab.pasta / http['arquivo']).read_bytes())
        self.assertNotIn(b'OLA_TURMA_COMPARACAO', (self.lab.pasta / https['arquivo']).read_bytes())
        for item in (http, https):
            self.assertEqual((self.lab.pasta / item['arquivo']).stat().st_mode & 0o777, 0o600)
        self.assertEqual(len((self.lab.pasta / 'envios.jsonl').read_text().splitlines()), 2)

    def test_formulario_do_usuario_em_http_e_https(self):
        for protocolo in ('http', 'https'):
            status, pagina = self.request(protocolo)
            self.assertEqual(status, 200)
            self.assertIn(b'name="concordo"', pagina)
            self.assertIn(b'/certificado.crt', pagina)
            status, _ = self.request(protocolo, '/enviar', {
                'sessao': self.lab.token, 'mensagem': 'Visitante & <teste>', 'concordo': 'sim',
            })
            self.assertEqual(status, 200)
        envios = self.lab.estado()['envios']
        self.assertEqual(len(envios), 2)
        self.assertEqual(envios[1]['recebido'], 'Visitante & <teste>')
        self.assertTrue(envios[0]['legivel'])
        self.assertFalse(envios[1]['legivel'])

    def test_visita_e_envio_sem_concordancia_nao_sao_gravados(self):
        self.assertEqual(self.request()[0], 200)
        for protocolo in ('http', 'https'):
            status, _ = self.request(protocolo, '/enviar', {'sessao': self.lab.token, 'mensagem': 'Teste'})
            self.assertEqual(status, 400)
        self.assertEqual(self.lab.estado()['total'], 0)
        self.assertEqual(list(self.lab.pasta.glob('*.bin')), [])
        self.assertFalse((self.lab.pasta / 'envios.jsonl').exists())

    def test_sessao_invalida_mensagem_grande_e_campos_duplicados(self):
        for campos in (
            {'sessao': 'outra', 'mensagem': 'teste', 'concordo': 'sim'},
            {'sessao': self.lab.token, 'mensagem': 'a' * 81, 'concordo': 'sim'},
            {'sessao': self.lab.token, 'mensagem': ' ', 'concordo': 'sim'},
        ):
            self.assertEqual(self.request('http', '/enviar', campos)[0], 400)
        self.assertEqual(self.lab.estado()['total'], 0)

    def test_cliente_exige_certificado_confiavel(self):
        with self.assertRaises(ssl.SSLCertVerificationError):
            self.request('https', confiavel=False)
        self.assertEqual(self.request('https')[0], 200)
        self.assertEqual(len(self.lab.fingerprint), 64)
        self.assertEqual(self.lab.estado()['total'], 0)

    def test_publica_apenas_certificado_publico(self):
        status, certificado = self.request(caminho='/certificado.crt')
        self.assertEqual(status, 200)
        self.assertIn(b'BEGIN CERTIFICATE', certificado)
        for caminho in ('/ca.key', '/servidor.key', '/envios.jsonl', '/api/estado'):
            self.assertEqual(self.request(caminho=caminho)[0], 404)
        self.assertEqual((self.lab.pasta / 'ca.key').stat().st_mode & 0o777, 0o600)

    def test_encerramento_libera_portas_e_exclusao_preserva_outros_dados(self):
        original = self.base / 'registros.jsonl'
        original.write_text('preservar')
        self.lab.enviar_notebook()
        pasta = self.lab.pasta
        with self.assertRaises(ErroComparacao):
            self.lab.excluir()
        portas = list(self.lab.portas.values())
        self.lab.encerrar()
        self.assertTrue(pasta.exists())
        for porta in portas:
            with socket.socket() as teste:
                self.assertNotEqual(teste.connect_ex(('127.0.0.1', porta)), 0)
        self.lab.excluir()
        self.assertFalse(pasta.exists())
        self.assertEqual(original.read_text(), 'preservar')

    def test_mensagem_unicode_e_limites_do_cliente(self):
        for valor in ('', 'a' * 81, None):
            with self.assertRaises(ErroComparacao):
                self.lab.enviar_notebook(valor)
        self.lab.enviar_notebook('olá turma & demonstração')
        self.assertTrue(self.lab.envios[0]['legivel'])
        self.assertEqual(self.lab.envios[0]['recebido'], 'olá turma & demonstração')

    def test_controle_oculta_detalhes_ate_confirmar_e_ao_trocar_etapa(self):
        controle = Controle(self.base)
        controle.comparacao = self.lab
        with self.assertRaises(ErroOperacao):
            controle._acao('enviar_notebook', {})
        controle._acao('enviar_notebook', {'confirmar': True, 'mensagem': 'Texto ficticio'})
        self.assertNotIn('envios', controle.estado(publico=True)['comparacao'])
        with self.assertRaises(ErroOperacao):
            controle._acao('mostrar_comparacao', {})
        controle._acao('mostrar_comparacao', {'confirmar': True})
        self.assertEqual(len(controle.estado(publico=True)['comparacao']['envios']), 2)
        controle._acao('etapa', {'etapa': 6})
        self.assertNotIn('envios', controle.estado(publico=True)['comparacao'])
        self.assertTrue(controle.estado()['comparacao']['ativa'])


class TestFalhas(unittest.TestCase):
    def test_limite_de_bytes_por_fluxo(self):
        observacao = Observacao('127.0.0.1', 'http')
        observacao.adicionar(b'x' * (LIMITE_FLUXO + 300))
        self.assertEqual(len(observacao.bytes), LIMITE_FLUXO)
        self.assertTrue(observacao.truncado)

    def test_porta_ocupada_desfaz_servidores_parciais(self):
        with tempfile.TemporaryDirectory() as pasta, socket.socket() as ocupado:
            ocupado.bind(('127.0.0.1', 0))
            ocupado.listen()
            lab = Comparacao(pasta)
            with self.assertRaises(ErroComparacao):
                lab.preparar(portas={'http': 0, 'https': ocupado.getsockname()[1]})
            self.assertFalse(lab.ativa)
            self.assertEqual(lab.servidores, [])
            self.assertEqual(lab.threads, [])


if __name__ == '__main__':
    unittest.main()
