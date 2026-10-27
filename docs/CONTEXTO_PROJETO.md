# Contexto do projeto e encaixe com o deck

Este repositório é a demonstração ao vivo do projeto de intervenção **Inclusão Digital e Segurança da Informação** (Unit · Sistemas de Informação, orientação de Kramer da Silva Rodrigues).

## Parceiro e público

- **Escola:** EMEF Prof. Diomedes Santos Silva, Av. Alexandre Alcino, 950, Santa Maria, Aracaju/SE.
- **Público:** turma da EJA noturna, de jovens a idosos, com pouca familiaridade com computador, celular e internet.
- **Problema de partida:** exposição a golpes digitais (falso parente, falso Pix, links falsos), notícias falsas e uso inseguro de Wi-Fi aberto e senhas.

## Onde a demonstração entra na palestra

O deck tem um slide, **“Demonstração ao vivo — Por que não confiar em Wi-Fi aberto”**, com três ideias: rede aberta no ar, o risco na prática e como se proteger. O telão do app desenvolve essas três ideias em sete etapas.

| Ideia no deck | Etapa no telão | Objetivo para a turma |
| --- | --- | --- |
| 1. Rede aberta no ar | 1. Por que não confiar em Wi-Fi aberto? · 2. Entre na rede de teste | Entender que uma rede sem senha é aberta a qualquer um |
| 2. O risco na prática | 3. Leia e escolha participar · 4. Ver e guardar são coisas diferentes · 5. Um envio, quatro informações · 6. O mesmo texto, duas conexões | Ver o que aparece numa conexão e a diferença entre HTTP (sem cadeado) e HTTPS (com cadeado) |
| 3. Como se proteger | 7. Como se proteger | Conferir o cadeado, desconfiar de Wi-Fi aberto, deixar senhas e banco para redes seguras |

A mensagem do deck é a mesma do slide final do telão: em redes abertas, evite digitar senhas e dados bancários; procure o cadeado (HTTPS) e, para tarefas sensíveis, use os dados do celular ou uma rede de confiança.

## Cuidados com o público

- **Ambiente controlado:** só equipamentos e contas de teste do grupo; nenhum dado da plateia é acessado.
- **Participação voluntária:** quem preferir pode apenas acompanhar. Use apelidos e mensagens fictícias.
- **Consentimento antes de gravar:** o app só grava após a concordância e o envio do formulário; os dados reais ficam ocultos no telão até a equipe confirmar.
- **Linguagem:** o telão usa frases curtas e letras grandes pensando em adultos e idosos; explique termos como IP, MAC e HTTPS com exemplos do dia a dia.

## Cronograma do plano de trabalho (2026)

| Etapa | Atividade | Data |
| --- | --- | --- |
| 01 | Visita técnica para diagnóstico | 17/09 |
| 02 | Desenvolvimento e apresentação do diagnóstico | 18/09 a 09/10 |
| 03 | Visita para apresentar o diagnóstico e o plano de intervenção | 15/10 |
| 04 | Desenvolvimento e intervenção | 16/10 a 28/11 |
| 05 | Visita para a intervenção | 29/11 |

## Identidade visual do telão

Cores e tipografia seguem o deck: azul-marinho `#14254D`, azul `#2453A6`, amarelo `#F2B632`, fundo `#E9EEF7` e cartões `#FDFCF8`, com a fonte Montserrat (se não estiver instalada, o telão usa Trebuchet MS ou Liberation Sans). Os estilos ficam em `interface/telao.css` e os textos das etapas em `interface/conteudo.js`.
