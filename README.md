# GolGuess

Desafio diário para reconhecer um jogador por uma temporada marcante da carreira. O catálogo editorial reúne 874 jogadores conhecidos que atuaram desde 2005 nas cinco principais ligas europeias, no Brasileirão Série A e na Liga Profesional da Argentina.

## Executar localmente

Requer Python 3.12. Sem `DATABASE_URL`, o desenvolvimento usa SQLite automaticamente.

```powershell
pip install -r requirements.txt
python server.py
```

Abra http://127.0.0.1:8000. O HTML depende da API; `python -m http.server` não executa o jogo.

## Pistas e regras

O jogador do dia é igual para todos. Há seis chances, e um erro ou passe revela uma pista por vez nesta ordem:

1. Liga e temporada
2. Gols e assistências naquela liga e temporada
3. Posição principal (ATA, MEI, ZAG, LAT ou GOL)
4. Idade atual, calculada pelo servidor
5. Nacionalidade principal do perfil
6. Time daquela temporada

Depois de cinco erros ou passes, todas as pistas ficam visíveis e resta o último palpite. O modo Times continua com cinco tentativas.

O ciclo determinístico percorre todos os 874 jogadores antes de repetir. A busca ignora acentos e maiúsculas. O resultado pode ser compartilhado sem revelar a resposta.

## Interface

A tela mobile-first abre diretamente no jogo, em uma coluna central de até 560px. As pistas usam componentes próprios para placar, posição e time, e a interface pode ser alternada entre português, inglês e espanhol pelo menu do cabeçalho.

O rodapé liga as páginas Sobre, Desafios anteriores, Como jogar, Política de Privacidade, Política de Cookies, Termos de Uso e Contato para parcerias. As páginas institucionais são estáticas; o arquivo é renderizado pela função Python para publicar as rodadas encerradas automaticamente. O contato informado é `torvicbusiness35@gmail.com`.

## Ranking diário

O link **Ranking** no cabeçalho abre `/ranking`. Ao concluir o primeiro desafio do dia, a interface pede um nickname de 3 a 20 caracteres e já inclui o visitante na classificação. Modos ainda não concluídos valem 0; a mesma entrada é atualizada automaticamente quando os outros desafios terminam. A API calcula a pontuação com base nos lances salvos no servidor e aceita uma inscrição por visitante e dia. O código ISO fornecido pela Vercel em `x-vercel-ip-country` é salvo com a inscrição para exibir a bandeira; quando ausente ou inválido, usamos `UN`, sem armazenar o IP. A classificação exibe até 100 posições e a posição do visitante quando estiver fora desse grupo. À meia-noite de Brasília, o ranking exibido começa vazio; os registros anteriores são apagados na próxima consulta.

Cada modo parte de 100 pontos: erro ou passe em Jogadores desconta 6; erro ou passe em Times desconta 11; palpite incorreto ou jogador na posição errada no Top 10 desconta 2. Desistir do Top 10 atribui 0 ponto ao modo, para que revelar as respostas não renda vantagem. Empates são decididos pela hora de inscrição. O bloco AdSense `ad_3` fica depois da classificação e das regras, usando o slot `2022436715`.

O ranking compartilhado pode usar o Supabase pela API REST enquanto as rodadas permanecem em cookies assinados, ou usar o PostgreSQL já configurado em `DATABASE_URL`/`POSTGRES_URL`. A API não aceita pontuação enviada pelo navegador. Como não há conta, o limite de inscrição continua associado ao cookie deste navegador.

### Supabase no Vercel

1. No SQL Editor do projeto `ucubzsvrlmlcbzrmxjda`, execute [`supabase/ranking.sql`](supabase/ranking.sql). Ele cria a tabela com RLS, permite leitura das colunas públicas apenas para o dia atual e não permite escrita com a chave `anon`.
2. Nas variáveis de ambiente do Vercel, configure `SUPABASE_SECRET_KEY` com uma chave **secret** (`sb_secret_...`) do projeto. A chave antiga `service_role` também funciona em `SUPABASE_SERVICE_ROLE_KEY`. Não coloque nenhuma delas em arquivos públicos, no navegador ou no Git. A chave `anon` enviada não deve ser usada para gravar o ranking.
3. Configure `GOLGUESS_SECRET` com uma sequência aleatória de pelo menos 32 caracteres, estável entre deploys. Ela assina os cookies das três rodadas e o identificador anônimo do ranking. Trocar essa chave invalida os cookies anteriores.
4. Faça novo deploy e confira `/api/health`: `"rankingStorage":"supabase"`. O endereço padrão é `https://ucubzsvrlmlcbzrmxjda.supabase.co`; `SUPABASE_URL` pode substituí-lo se necessário.

O Supabase só recebe nickname, pontuação, dia e identificador anônimo. Os palpites continuam no cookie assinado. A API apaga classificações anteriores ao dia atual na próxima consulta. Sem a chave secreta e `GOLGUESS_SECRET`, a página mostra o ranking como indisponível; a chave pública, sozinha, não consegue habilitar a gravação segura.

## Deploy no Vercel

O projeto inclui `vercel.json`, funções Python em `api/` e um build que publica somente as páginas, CSS, JavaScript, atribuição e arquivos de descoberta necessários. O catálogo completo continua dentro da função e não é servido como arquivo estático.

O Vercel reescreve `/arquivo.html` para a função `/api/archive`. O arquivo é paginado e nunca mostra a rodada do dia; se uma resposta antiga voltar ao desafio atual após um ciclo, ela fica oculta até a rodada seguinte. As URLs canônicas, o sitemap e o `robots.txt` usam `https://www.golguess.com.br/`.

O SQLite não é persistente nas funções serverless do Vercel. Por isso, sem configuração adicional, a rodada e as estatísticas ficam em um cookie assinado, HttpOnly e Secure. O jogo funciona imediatamente após o deploy e mantém o limite por navegador.

Para persistência centralizada e estatísticas mais robustas, conecte um banco Postgres compatível:

1. No painel do projeto no Vercel, abra **Storage** e conecte um banco Neon/Postgres.
2. Confirme que a integração criou `DATABASE_URL` ou `POSTGRES_URL` nos ambientes Production e Preview.
3. Faça um novo deploy.
4. Abra `/api/health`; a resposta indica `"storage":"postgres"`.

O código cria as tabelas de visitantes, rodadas dos três modos e ranking automaticamente. Use a URL de conexão com pool quando o provedor oferecer uma. Credenciais ficam nas variáveis do Vercel e nunca devem entrar no Git.

Sem banco, `/api/health` indica `"storage":"signed-cookie"`. Defina também `GOLGUESS_SECRET` com uma sequência longa e aleatória para que a assinatura seja exclusiva do projeto. Sem essa variável, o jogo usa uma chave padrão adequada apenas ao MVP casual.

A interface agora mostra a mensagem devolvida pela API, em vez de atribuir todo erro à conexão do usuário.

## Uma rodada por dia sem conta

Um cookie anônimo, HttpOnly, Secure e SameSite=Lax identifica o navegador. No modo Postgres, o servidor guarda e valida cada lance, usa versão da rodada e bloqueio transacional para impedir duas abas de consumirem a mesma chance. No modo padrão do Vercel, o próprio estado assinado fica no cookie. Recarregar ou abrir outra aba recupera a partida nos dois modos.

O limite é por navegador. Apagar cookies, abrir janela anônima ou usar outro dispositivo cria outra identificação. Sem conta ou identidade externa, não é tecnicamente possível garantir uma única partida por pessoa em todos os dispositivos.

## Catálogo

`data/curated_names.txt` é a lista editorial. `scripts/build_career_catalog.py` cruza esses nomes com o snapshot do [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets), agrupa as partidas por liga, temporada e clube e escolhe uma temporada representativa. O filtro exige participação relevante e um indicador de reconhecimento de carreira; assim entram estrelas e jogadores sólidos conhecidos, sem carregar elencos inteiros ou reservas obscuros. Posição e nacionalidade vêm do perfil de cada jogador no mesmo snapshot; as duas cidadanias ausentes estão verificadas em `scripts/player_metadata.py`, e os quatro registros históricos estão completos em `data/legacy_players.json`.

Os dados sul-americanos são reconstruídos a partir dos eventos de gols, assistências, cartões e substituições. Quatro ídolos anteriores à cobertura principal ficam documentados em `data/legacy_players.json`. Veja [a metodologia e a licença](data/ATTRIBUTION.md).

Para refazer o arquivo, baixe os cinco CSVs compactados descritos na atribuição e execute:

```powershell
python scripts/build_career_catalog.py players.csv.gz appearances.csv.gz games.csv.gz clubs.csv.gz game_events.csv.gz
```

## Testes

```powershell
python -m unittest discover -s tests -v
node --check app.js
python scripts/build_static.py
```

Os testes cobrem catálogo, ordem das pistas, cálculo de idade, resposta oculta, concorrência entre abas, fim da rodada, virada do dia, estatísticas, busca sem acentos, origem das requisições e endpoint de saúde.

## Publicidade

Publicidade desativada por padrão (`GOLGUESS_ADS_ENABLED=0`); Analytics desativado. `ads.js` exige conteúdo carregado e consentimento TCF de uma CMP cujo ID corresponda a `GOLGUESS_CMP_ID`. A CMP ainda precisa ser instalada e verificada: definir variáveis não a instala. O bloqueio é conservador em todas as regiões e não habilita anúncios limitados/não personalizados como alternativa. Preview e localhost nunca solicitam Google. Consulte [a entrega e as pendências externas](docs/qualidade-adsense.md) antes de ativar.

A unidade manual mantém 160 px de separação e não é atualizada entre palpites, modos ou viradas. Ranking vazio, falhas e carregamento não habilitam anúncios. O fim da partida continua elegível porque preserva pistas, resultado e histórico. Espaços sem preenchimento ficam invisíveis e só são recolhidos fora da área visível quando isso não desloca controles.

## Calendário e HTML inicial

`/`, `/index.html` e `/api/home` renderizam a página inicial no servidor com número, data, primeira pista pública e retrospectiva. `round_info` é compartilhado com os três modos, e o fuso usa a base IANA `America/Sao_Paulo` (`tzdata` no Windows). O build não publica um `index.html` estático que possa encobrir a função. Arquivo e início usam `no-store`; assets revalidam a cada navegação. Não é necessário cron nem novo deploy diário.

`daily.js` consulta o relógio do servidor no início, na retomada e à meia-noite. Atualiza a retrospectiva e o jogo sem recarregar anúncios. O arquivo, sem publicidade, recarrega após a virada. `/arquivo.html?data=AAAA-MM-DD` é um filtro com URL estável que rejeita datas abertas/futuras; a lista também mantém paginação e busca por data.

Para os testes adicionais: `node --test tests/ads.test.mjs`. O teste visual opcional requer `pip install playwright` e Edge instalado: `python tests/browser_smoke.py`. Ele usa SQLite temporário, bloqueia tráfego externo e salva capturas em `.runtime/screenshots/`.
