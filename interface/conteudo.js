'use strict';
window.ETAPAS = [
  {
    titulo: 'O que uma conexão revela?',
    resumo: 'Convide o público e explique a participação voluntária.',
    nota: 'Antes de conectar: a rede pode observar IP e MAC; ao abrir a página, o servidor recebe IP e informações do navegador. O programa só grava a participação após concordância e envio. Quem preferir pode apenas acompanhar.',
    corpo: '<p class="slide-lead">Uma experiência com seu celular, uma rede Wi-Fi e uma página local.</p><div class="caminho"><div><span class="desenho celular">▯</span><strong>Seu celular</strong></div><span class="ligacao"></span><div><span class="desenho wifi">⌁</span><strong>Rede Wi-Fi</strong></div><span class="ligacao"></span><div><span class="desenho notebook">▱</span><strong>Página local</strong></div></div><p class="slide-aviso">Participação voluntária. Você também pode apenas acompanhar.</p>'
  },
  {
    titulo: 'Entre na rede da atividade',
    resumo: 'Mantenha nome da rede e endereço visíveis enquanto o público conecta.',
    nota: 'A rede não exige senha. O celular pode avisar que não há internet: mantenha a conexão. Digite o endereço completo no navegador; a página não abre automaticamente. A dinâmica funciona sem internet. Em ensaio, não há ponto de acesso real.',
    corpo: '<div class="conectar"><div><span>1. Nas configurações de Wi-Fi, escolha</span><strong class="nome-rede">EXTENSAO-REDE-ABERTA</strong><p>Sem senha</p></div><div><span>2. No navegador, abra</span><strong class="endereco">http://10.42.0.1:8080</strong></div></div><p class="slide-aviso">Apareceu “sem internet”? Mantenha a conexão para acessar a página local.</p>'
  },
  {
    titulo: 'Leia e escolha participar',
    resumo: 'Explique os campos e espere os envios voluntários.',
    nota: 'O apelido é opcional e pode ser fictício. Oriente a não informar senhas nem nome real. Abrir a página não grava participação. Cada envio válido acrescenta um registro; envios não equivalem a pessoas diferentes. A comunicação desta página usa HTTP, sem criptografia.',
    corpo: '<div class="passos-form"><div><span>1</span><h2>Leia o aviso</h2><p>Saiba quais dados serão gravados.</p></div><div><span>2</span><h2>Escolha um apelido</h2><p>Fictício, ou deixe em branco.</p></div><div><span>3</span><h2>Concorde e envie</h2><p>Marque a caixa e toque em Participar.</p></div></div><p class="slide-aviso">Use apenas dados de demonstração. Esta página usa HTTP.</p>'
  },
  {
    titulo: 'Observar e gravar são etapas diferentes',
    resumo: 'Mostre o que fica disponível em cada momento.',
    nota: 'O IP é o endereço usado na rede local. O MAC pode ser aleatório. User-Agent é uma informação técnica enviada pelo navegador, não comprova identidade. A tabela de vizinhos pode omitir aparelhos; o programa não grava MAC nos registros de participação.',
    corpo: '<div class="linha-tempo"><div><span>Na rede</span><h2>IP e MAC</h2><p>Podem aparecer na tabela de vizinhos do notebook.</p></div><div><span>Ao abrir a página</span><h2>IP e navegador</h2><p>O servidor recebe informações da requisição.</p></div><div><span>Após concordar e enviar</span><h2>Registro local</h2><p>Horário, IP, navegador e apelido opcional.</p></div></div>'
  },
  {
    titulo: 'Um envio, quatro informações',
    resumo: 'Compare o exemplo fictício com os resultados, se desejar.',
    nota: 'Os dados reais ficam ocultos por padrão. Para exibir, use Revelar no telão e confirme. Ao avançar ou voltar, o app os oculta novamente. Horários são armazenados em UTC. A comparação observa fluxos TCP somente dos nossos servidores de teste, antes da descriptografia TLS; não lê outros sites.',
    corpo: '<div class="ficha-exemplo"><span>Exemplo fictício</span><dl><div><dt>Horário</dt><dd>18:30 UTC</dd></div><div><dt>IP local</dt><dd>10.42.0.23</dd></div><div><dt>Navegador</dt><dd>Informações técnicas do aplicativo</dd></div><div><dt>Apelido</dt><dd>Visitante Azul</dd></div></dl></div>'
  },
  {
    titulo: 'O mesmo texto, duas conexões',
    resumo: 'Compare os envios do celular ou faça o envio automático pelo notebook.',
    nota: 'Prepare a comparação no painel. O celular pode abrir o formulário HTTP e, com o certificado de laboratório previamente instalado e conferido, o HTTPS. Enviar pelo notebook transmite o mesmo texto pelas duas conexões com verificação do certificado. A observação mostra bytes TCP reais antes da descriptografia no servidor, não pacotes capturados da rede inteira. O servidor recebe o texto nas duas versões; na entrada HTTPS, o conteúdo da aplicação está criptografado. Use Mostrar comparação no telão para projetar os resultados após confirmar.',
    corpo: '<div class="comparacao-intro"><div><h2>HTTP</h2><p>O texto do formulário aparece nos bytes da conexão.</p></div><div><h2>HTTPS</h2><p>Os registros TLS protegem o conteúdo durante o transporte.</p></div></div><p class="slide-aviso">Envie no celular ou use o botão do notebook. IPs, portas e tamanhos continuam observáveis.</p>'
  },
  {
    titulo: 'O cuidado começa antes do clique',
    resumo: 'Converse sobre o aprendizado e encerre a rede.',
    nota: 'HTTPS criptografa a comunicação entre navegador e servidor; o destino ainda recebe os dados enviados a ele. Pergunte o que surpreendeu. Oriente a sair da rede e removê-la das conexões salvas. Encerre a dinâmica pelo botão; os registros permanecem até a exclusão explícita.',
    corpo: '<div class="aprendizados"><p>Confirme qual é a rede.</p><p>Entenda quais dados você envia.</p><p>Observe o endereço e a proteção da conexão.</p></div><p class="pergunta">Qual informação você não imaginava que apareceria?</p>'
  }
];
