'use strict';
window.ETAPAS = [
  {
    titulo: 'Por que não confiar em Wi-Fi aberto?',
    resumo: 'Apresente a demonstração e explique que participar é voluntário (slide “Demonstração ao vivo” do deck).',
    nota: 'Antes de conectar: a rede pode observar IP e MAC; ao abrir a página, o servidor recebe IP e informações do navegador. O programa só grava a participação após concordância e envio. Quem preferir pode apenas acompanhar.',
    corpo: '<p class="slide-lead">Vamos ver, na prática, o que acontece quando um celular entra em uma rede sem senha.</p><div class="caminho"><div><span class="desenho celular"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="2" width="11" height="20" rx="2.6"/><path d="M10.5 5h3"/><circle cx="12" cy="18.4" r=".8"/><circle class="ponto aviso" cx="17.6" cy="3" r="2.4"/></svg></span><strong>Seu celular</strong></div><span class="ligacao"><i></i><i></i><i></i></span><div><span class="desenho wifi"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="onda o3" d="M2.5 9.5a14 14 0 0 1 19 0"/><path class="onda o2" d="M5.5 13a9.5 9.5 0 0 1 13 0"/><path class="onda o1" d="M8.7 16.4a4.6 4.6 0 0 1 6.6 0"/><circle class="ponto" cx="12" cy="19.7" r="1.3"/></svg></span><strong>Rede Wi-Fi</strong></div><span class="ligacao"><i></i><i></i><i></i></span><div><span class="desenho notebook"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="11.5" rx="1.5"/><path d="M2 19.5h20M4.5 15.5L2.5 19.5M19.5 15.5l2 4"/><path class="linha l1" d="M7 8h10"/><path class="linha l2" d="M7 11.5h6"/></svg></span><strong>Página local</strong></div></div><p class="slide-aviso controle"><b>Ambiente controlado</b>Usamos só equipamentos do grupo e dados de teste. Participar é voluntário: você também pode apenas acompanhar.</p>'
  },
  {
    titulo: 'Entre na rede de teste',
    resumo: 'Mantenha nome da rede e endereço visíveis enquanto o público conecta.',
    nota: 'A rede não exige senha. O celular pode avisar que não há internet: mantenha a conexão. Digite o endereço completo no navegador; a página não abre automaticamente. A dinâmica funciona sem internet. Em ensaio, não há ponto de acesso real.',
    corpo: '<div class="conectar-passos"><div class="passo-conexao"><div class="topo-passo"><span class="num">1</span><p class="instrucao">No celular, abra o Wi-Fi e escolha</p></div><div class="tela-wifi"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="onda o3" d="M2.5 9.5a14 14 0 0 1 19 0"/><path class="onda o2" d="M5.5 13a9.5 9.5 0 0 1 13 0"/><path class="onda o1" d="M8.7 16.4a4.6 4.6 0 0 1 6.6 0"/><circle cx="12" cy="19.7" r="1.3" fill="currentColor" stroke="none"/></svg><div><strong class="nome-rede">EXTENSAO-REDE-ABERTA</strong><span class="chip-aberta"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.5-2"/></svg>Sem senha</span></div></div></div><div class="passo-conexao"><div class="topo-passo"><span class="num">2</span><p class="instrucao">Abra o navegador e digite</p></div><div class="barra-endereco"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/></svg><div><span class="nao-seguro">Não seguro</span><strong class="endereco">http://10.42.0.1:8080<i class="cursor"></i></strong></div></div></div></div><p class="slide-aviso"><b>Apareceu “sem internet”?</b>Está certo! Continue conectado para abrir a página de teste.</p>'
  },
  {
    titulo: 'Leia e escolha participar',
    resumo: 'Explique os campos e espere os envios voluntários.',
    nota: 'O apelido é opcional e pode ser fictício. Oriente a não informar senhas nem nome real. Abrir a página não grava participação. Cada envio válido acrescenta um registro; envios não equivalem a pessoas diferentes. A comunicação desta página usa HTTP, sem criptografia.',
    corpo: '<div class="passos-form"><div><span>1</span><h2>Leia o aviso</h2><p>Ele diz quais dados serão guardados.</p></div><div><span>2</span><h2>Escolha um apelido</h2><p>Inventado, ou deixe em branco.</p></div><div><span>3</span><h2>Concorde e envie</h2><p>Marque a caixa e toque em Participar.</p></div></div><p class="slide-aviso controle"><b>Nunca use seu nome real nem senhas</b>Esta página de teste usa HTTP, sem cadeado.</p>'
  },
  {
    titulo: 'Ver e guardar são coisas diferentes',
    resumo: 'Mostre o que fica disponível em cada momento.',
    nota: 'O IP é o endereço usado na rede local. O MAC pode ser aleatório. User-Agent é uma informação técnica enviada pelo navegador, não comprova identidade. A tabela de vizinhos pode omitir aparelhos; o programa não grava MAC nos registros de participação.',
    corpo: '<div class="linha-tempo"><div><span>Ao entrar na rede</span><h2>IP e MAC</h2><p>O notebook da equipe pode ver o “endereço” do aparelho.</p></div><div><span>Ao abrir a página</span><h2>IP e navegador</h2><p>A página recebe o endereço e o tipo de navegador.</p></div><div><span>Só se você concordar</span><h2>Registro guardado</h2><p>Horário, IP, navegador e apelido opcional.</p></div></div>'
  },
  {
    titulo: 'Um envio, quatro informações',
    resumo: 'Compare o exemplo fictício com os resultados, se desejar.',
    nota: 'Os dados reais ficam ocultos por padrão. Para exibir, use Revelar no telão e confirme. Ao avançar ou voltar, o app os oculta novamente. Horários são armazenados em UTC. A comparação observa fluxos TCP somente dos nossos servidores de teste, antes da descriptografia TLS; não lê outros sites.',
    corpo: '<div class="ficha-exemplo"><span>EXEMPLO FICTÍCIO · O QUE FICA GUARDADO</span><dl><div><dt>Horário</dt><dd>18:30 UTC</dd></div><div><dt>IP local</dt><dd>10.42.0.23</dd></div><div><dt>Navegador</dt><dd>Tipo de celular e aplicativo</dd></div><div><dt>Apelido</dt><dd>Visitante Azul</dd></div></dl></div>'
  },
  {
    titulo: 'O mesmo texto, duas conexões',
    resumo: 'Compare os envios do celular ou faça o envio automático pelo notebook.',
    nota: 'Prepare a comparação no painel. O celular pode abrir o formulário HTTP e, com o certificado de laboratório previamente instalado e conferido, o HTTPS. Enviar pelo notebook transmite o mesmo texto pelas duas conexões com verificação do certificado. A observação mostra bytes TCP reais antes da descriptografia no servidor, não pacotes capturados da rede inteira. O servidor recebe o texto nas duas versões; na entrada HTTPS, o conteúdo da aplicação está criptografado. Use Mostrar comparação no telão para projetar os resultados após confirmar.',
    corpo: '<div class="comparacao-intro"><div><h2>HTTP · sem cadeado</h2><p>O texto digitado aparece legível para quem observa a conexão.</p></div><div class="destaque"><h2>HTTPS · com cadeado</h2><p>O conteúdo viaja embaralhado (criptografado) até o site.</p></div></div><p class="slide-aviso"><b>Mesmo com cadeado,</b>quem observa ainda vê para onde a conexão vai e o tamanho dela.</p>'
  },
  {
    titulo: 'Como se proteger',
    resumo: 'Feche com as três dicas da mensagem do deck, converse com a turma e encerre a rede.',
    nota: 'HTTPS criptografa a comunicação entre navegador e servidor; o destino ainda recebe os dados enviados a ele. Pergunte o que surpreendeu. Oriente a sair da rede e removê-la das conexões salvas. Encerre a dinâmica pelo botão; os registros permanecem até a exclusão explícita.',
    corpo: '<div class="aprendizados"><div><span>1</span><h2>Confira o cadeado</h2><p>Procure o HTTPS na barra do navegador.</p></div><div><span>2</span><h2>Desconfie de Wi-Fi aberto</h2><p>Confirme o nome da rede com o responsável.</p></div><div><span>3</span><h2>Senhas e banco só em rede segura</h2><p>Ou use os dados do próprio celular.</p></div></div><p class="pergunta">Qual informação você não imaginava que apareceria?</p>'
  }
];
