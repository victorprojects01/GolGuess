# Catálogo de carreiras do GolGuess

O arquivo privado `players.json` contém uma seleção editorial de jogadores conhecidos que atuaram, de 2005 em diante, na Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Campeonato Brasileiro - Série A ou Liga Profesional da Argentina.

## Fonte principal

As partidas, perfis e eventos usados para calcular temporada, time, gols, assistências e cartões vêm do projeto [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets), consultado em 11/09/2026. O projeto distribui seus datasets sob [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

Para posição e nacionalidade, os 870 perfis identificados por `player_id` foram conferidos no `players.csv.gz` da mesma distribuição em 14/09/2026. O arquivo de origem indicava atualização em 05/09/2026. Os quatro registros históricos restantes foram completados manualmente.

Alterações do GolGuess: seleção editorial de nomes; filtro por relevância histórica e participação; agrupamento de eventos por jogador, clube, liga e temporada; escolha de uma temporada representativa; tradução dos nomes das competições; redução dos campos; cálculo dinâmico da idade. A posição principal do perfil é agrupada em ATA (ataque), MEI (meio-campo), ZAG (zaga), LAT (lateral) ou GOL (goleiro). A nacionalidade segue o país principal do campo `country_of_citizenship` do perfil e é traduzida para português; é um rótulo esportivo, não uma afirmação sobre cidadania legal. Dois perfis sem esse campo no CSV foram conferidos na UEFA: [Radja Nainggolan](https://www.uefa.com/news-media/news/0211-0f8a36217063-8f0b763a081b-1000--nainggolan-coming-to-roma/) e [Samir Handanovič](https://www.uefa.com/uefaeuropaleague/news/01ff-0e7e5d6890ab-679eb98c71c4-1000--udinese-goalkeeper-handanovic-heads-to-inter/).

O snapshot de origem informa cobertura até julho de 2026. Para Brasil e Argentina, as atuações foram reconstruídas a partir de gols, cartões e substituições porque o arquivo de aparições não inclui essas competições. Jogadores sem nenhum desses eventos podem ficar fora da seleção.

## Registros históricos complementares

Rogério Ceni, Ronaldinho, Juan Román Riquelme e Martín Palermo foram incluídos em `legacy_players.json`, pois suas temporadas escolhidas antecedem a cobertura de aparições do snapshot. Esses registros foram revisados manualmente a partir das páginas históricas de temporada do Transfermarkt e páginas de temporadas dos clubes/Wikipedia. Posição e nacionalidade desses quatro jogadores estão no próprio `legacy_players.json`; Ronaldinho foi classificado como atacante conforme o [perfil histórico do Barcelona](https://players.fcbarcelona.com/en/player/763-ronaldinho-ronaldo-assis-moreira). São fatos esportivos, registrados com a marca `manual-reviewed` para permitir nova auditoria.

## Reprodução

Baixe `players.csv.gz`, `appearances.csv.gz`, `games.csv.gz`, `clubs.csv.gz` e `game_events.csv.gz` da distribuição do transfermarkt-datasets. Depois execute:

```bash
python scripts/build_career_catalog.py players.csv.gz appearances.csv.gz games.csv.gz clubs.csv.gz game_events.csv.gz
```

O arquivo `curated_names.txt` controla quem pode entrar. Nomes sem correspondência ou sem uma temporada válida são escritos em `unmatched_curated.txt` para revisão; eles não entram automaticamente no jogo.
