# GolGuess — correções e validação, 23/09/2026

Alterações locais, sem publicação e sem promessa de aprovação. A avaliação de 22/09 não é uma descrição exata deste checkout: o arquivo já era dinâmico, mas o início era estático, não havia retrospectiva e as margens eram 20 px no jogo e 26 px no ranking. As solicitações publicitárias eram incondicionais. O novo início é renderizado em Python, usando o calendário dos jogos; o arquivo ganha navegação por data, todas as pistas, idade histórica, Top 10 completo e contexto original com fontes oficiais para os jogadores das 12 rodadas encerradas entre 11 e 22/09, além de CF Montréal. Notas são escritas individualmente e vinculadas à entidade: o fechamento futuro publica dados automaticamente, mas não inventa novos textos nem alegações de revisão. A ampliação editorial depende de pesquisa específica.

## Políticas, recomendações e decisões do projeto

- **Políticas:** evitar cliques acidentais, disfarces, incentivos e sobreposições indevidas. Conteúdo sem valor, telas sem conteúdo editorial e páginas usadas só para navegação não devem monetizar. Não há anúncios no arquivo, páginas institucionais, erros ou diálogos; ranking vazio/falho é suprimido como precaução do projeto. Uma partida encerrada mantém conteúdo útil e não é automaticamente excluída.
- **Recomendação do Google:** pelo menos 150 px entre jogo e anúncio. Implementação: 160 px antes e depois da unidade, formato horizontal de altura reservada. Sugestões inferiores do Top 10 abrem para cima. Uma unidade por página; sem refresh de anúncios. A altura do jogo é preservada após solicitar publicidade para impedir que, ao trocar Top 10 por um modo menor, o anúncio suba para o lugar dos controles anteriores.
- **Melhorias editoriais:** retrospectiva coerente, filtros, respostas completas, notas originais com fontes e explicações de critérios. Não representam requisitos de número mínimo de páginas, artigos ou palavras.
- **Consentimento:** o projeto adota bloqueio global conservador até consentimento afirmativo. A recomendação técnica não substitui avaliação jurídica nem uma CMP certificada. EEE, Reino Unido e Suíça precisam da integração certificada pertinente. `gdprApplies=false` não é tratado como autorização. EUA/GPP e Brasil ainda requerem configuração regional real; não há consentimento presumido.

## Evidência local

- Suíte Python: 32 testes aprovados de regras, seis/cinco tentativas, Top 10, pontuação calculada no servidor, retomada, concorrência, cookies, isolamento de respostas e ranking, além dos novos testes de HTML e arquivo na virada de 02:59:59 para 03:00:00 UTC (meia-noite em São Paulo).
- Navegador Edge sem janela, SQLite temporário e todo tráfego externo bloqueado: três vitórias, reload/retomada, inscrição local e total de 294 pontos (94 Jogadores, 100 Times, 100 Top 10). Nenhum registro enviado ao ranking público.
- Virada simulada de 23 para 24/09: rodada #013 → #014, retrospectiva atualizada, novo jogo e ranking vazio. Erros 503 em jogo/ranking suprimem publicidade. Bloco simulado sem preenchimento recolhido fora da área visível.
- Geometria real do DOM com placeholder inerte: 160 px nas larguras 320, 390, 768 e 1440; sem rolagem horizontal ou erro JavaScript. Capturas em `.runtime/screenshots/`. Não são criativos reais nem evidência de configuração do painel.
- Testes JavaScript simulam consentimento ausente, negado, incompleto, CMP divergente, revogação, falta de preenchimento e trava de localhost/preview. Os cenários BR, DE, GB, CH, US e região desconhecida validam o bloqueio comum, **não** certificam uma CMP ou geolocalização reais.

## Pendências externas exatas

1. **Deploy/Vercel:** publicar este código, confirmar empacotamento de `index.html` e dos três catálogos privados nas funções e validar `/`, `/index.html`, `/arquivo.html` sem JavaScript. Verificar `Cache-Control: no-store`, descartar caches de HTML de deploys anteriores e repetir a virada no ambiente de preview. Nenhuma credencial nem progresso foi migrado.
2. **AdSense:** conta habilitada, domínio verificado e slots existentes válidos. Em Anúncios → Por site, desligar anúncios automáticos para estas páginas (incluindo âncora, vinheta, intenção e inserções na área de jogo) antes de ativar a unidade manual. O código não pode garantir as configurações remotas do painel. Conferir Centro de políticas e prévia em mobile/desktop. Não clicar em anúncios.
3. **CMP:** o usuário informou a mensagem Google como Publicada. `consent.js` inicia a tag AdSense com `pauseAdRequests=1`, registra a API oficial Google Privacy & Messaging e oferece revisão de preferências no rodapé. O ID padrão é 300 (Google); `GOLGUESS_CMP_ENABLED=1` habilita a integração somente nos domínios de produção. `GOLGUESS_ADS_ENABLED` continua desligado por padrão: confirme também o valor no painel Vercel. O cabeçalho Referrer-Policy permite enviar a origem ao Google. Antes de liberar anúncios, testar a mensagem real em EEE/UK/CH: aceitar, recusar, reabrir, retirar e retornar ao site; conferir cookies e rede. Brasil e EUA/GPP/GPC ainda precisam de validação/integração regional; `gdprApplies=false` mantém anúncios bloqueados. Desligar anúncios automáticos no painel antes de definir `GOLGUESS_ADS_ENABLED=1`. Analytics permanece desligado. O carregamento pausado envolve conexões ao Google e possível leitura de cookies existentes; não significa ausência de tráfego externo.
4. **Dados/licenças:** conferir os direitos de uso comercial das fontes originais e dos ativos; a declaração CC0 do dataset não resolve automaticamente direitos de terceiros. Os clubes não têm fontes individuais nem data de corte dos títulos no catálogo; rankings Top 10 têm nomes de fontes, mas faltam links específicos e critérios de desempate verificáveis. Não houve auditoria integral desses números. As notas adicionadas usam [Leicester City](https://www.lcfc.com/media-article/LCFC-Men-Records) e [CF Montréal](https://en.cfmontreal.com/club/history). Ampliar contexto apenas com pesquisa específica, sem gerar parágrafos em massa.

## Documentação oficial consultada

- [Qualificação](https://support.google.com/adsense/answer/9724?hl=pt-BR)
- [Preparação de páginas](https://support.google.com/adsense/answer/7299563?hl=pt-BR)
- [Motivos de reprovação](https://support.google.com/adsense/answer/81904?hl=pt-BR)
- [Políticas do programa](https://support.google.com/adsense/answer/48182?hl=pt-BR)
- [Páginas de jogos e recomendação de 150 px](https://support.google.com/adsense/answer/2768340?hl=pt-BR)
- [Posição e cliques acidentais](https://support.google.com/adsense/answer/1346295?hl=pt-BR)
- [Políticas para publishers](https://support.google.com/publisherpolicies/answer/10502938?hl=pt-BR)
- [CMP para EEE, UK e Suíça](https://support.google.com/adsense/answer/13554020?hl=en)
- [GPP nos EUA](https://support.google.com/adsense/answer/14126816?hl=en-GB)

- [Inicialização pausada do AdSense](https://support.google.com/adsense/answer/7670312?hl=en)
- [API de mensagens e revisão de consentimento](https://developers.google.com/funding-choices/fc-api-docs)
- [Mensagem publicada e Referrer-Policy](https://support.google.com/adsense/answer/10960768?hl=pt-BR)
