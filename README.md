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

O jogador do dia é igual para todos. Há cinco chances, e um erro ou passe revela a próxima pista nesta ordem:

1. Liga e temporada
2. Gols e assistências naquela liga e temporada
3. Cartões amarelos e vermelhos
4. Idade atual, calculada pelo servidor
5. Time daquela temporada

O ciclo determinístico percorre todos os 874 jogadores antes de repetir. A busca ignora acentos e maiúsculas. O resultado pode ser compartilhado sem revelar a resposta.

## Interface

A tela mobile-first abre diretamente no jogo, em uma coluna central de até 560px. As pistas usam componentes próprios para placar, cartões e time, e a interface pode ser alternada entre português, inglês e espanhol pelo menu do cabeçalho.

O rodapé liga as páginas Sobre, Desafios anteriores, Como jogar, Política de Privacidade, Política de Cookies, Termos de Uso e Contato para parcerias. As páginas institucionais são estáticas; o arquivo é renderizado pela função Python para publicar as rodadas encerradas automaticamente. O contato informado é `torvicbusiness35@gmail.com`.

## Deploy no Vercel

O projeto inclui `vercel.json`, funções Python em `api/` e um build que publica somente as páginas, CSS, JavaScript, atribuição e arquivos de descoberta necessários. O catálogo completo continua dentro da função e não é servido como arquivo estático.

O Vercel reescreve `/arquivo.html` para a função `/api/archive`. O arquivo é paginado e nunca mostra a rodada do dia; se uma resposta antiga voltar ao desafio atual após um ciclo, ela fica oculta até a rodada seguinte. As URLs canônicas, o sitemap e o `robots.txt` usam `https://www.golguess.com.br/`.

O SQLite não é persistente nas funções serverless do Vercel. Por isso, sem configuração adicional, a rodada e as estatísticas ficam em um cookie assinado, HttpOnly e Secure. O jogo funciona imediatamente após o deploy e mantém o limite por navegador.

Para persistência centralizada e estatísticas mais robustas, conecte um banco Postgres compatível:

1. No painel do projeto no Vercel, abra **Storage** e conecte um banco Neon/Postgres.
2. Confirme que a integração criou `DATABASE_URL` ou `POSTGRES_URL` nos ambientes Production e Preview.
3. Faça um novo deploy.
4. Abra `/api/health`; a resposta indica `"storage":"postgres"`.

O código cria as tabelas `visitors` e `career_rounds` automaticamente. Use a URL de conexão com pool quando o provedor oferecer uma. Credenciais ficam nas variáveis do Vercel e nunca devem entrar no Git.

Sem banco, `/api/health` indica `"storage":"signed-cookie"`. Defina também `GOLGUESS_SECRET` com uma sequência longa e aleatória para que a assinatura seja exclusiva do projeto. Sem essa variável, o jogo usa uma chave padrão adequada apenas ao MVP casual.

A interface agora mostra a mensagem devolvida pela API, em vez de atribuir todo erro à conexão do usuário.

## Uma rodada por dia sem conta

Um cookie anônimo, HttpOnly, Secure e SameSite=Lax identifica o navegador. No modo Postgres, o servidor guarda e valida cada lance, usa versão da rodada e bloqueio transacional para impedir duas abas de consumirem a mesma chance. No modo padrão do Vercel, o próprio estado assinado fica no cookie. Recarregar ou abrir outra aba recupera a partida nos dois modos.

O limite é por navegador. Apagar cookies, abrir janela anônima ou usar outro dispositivo cria outra identificação. Sem conta ou identidade externa, não é tecnicamente possível garantir uma única partida por pessoa em todos os dispositivos.

## Catálogo

`data/curated_names.txt` é a lista editorial. `scripts/build_career_catalog.py` cruza esses nomes com o snapshot do [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets), agrupa as partidas por liga, temporada e clube e escolhe uma temporada representativa. O filtro exige participação relevante e um indicador de reconhecimento de carreira; assim entram estrelas e jogadores sólidos conhecidos, sem carregar elencos inteiros ou reservas obscuros.

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

A página do jogo carrega o script do Google AdSense uma vez e solicita o bloco responsivo `ad_01` (`2219850050`) após o jogo, fora das pistas e do palpite. Google Analytics também está presente. A exibição real depende do estado da conta AdSense e das configurações de anúncios automáticos. As páginas de privacidade e cookies descrevem esses serviços. Revise as configurações de consentimento exigidas nas regiões atendidas antes de considerar a integração publicitária concluída.
