# GolGuess

Desafio diário de futebol: entrar, ler pistas, escolher um jogador e compartilhar o placar. Interface em português, com tema esportivo escuro, verde-lima e layout responsivo.

## Executar

Requer Python 3.10 ou superior. Não há dependências de instalação ou build.

```powershell
python server.py
```

Abra http://127.0.0.1:8000. Use este servidor: abrir o HTML diretamente ou usar `python -m http.server` não oferece a API necessária para jogar.

## Como funciona

- 831 jogadores únicos convocados para a Copa masculina de 2022, incluindo reservas que não entraram em campo.
- Todos recebem o mesmo jogador por dia. O ciclo determinístico passa pelos 831 nomes antes de repetir; não altere o catálogo ou a ordenação durante um ciclo publicado.
- Cinco chances. A seleção aparece primeiro; erro ou passe libera posição, idade em 20/11/2022, camisa naquela Copa e iniciais.
- Busca sem distinção de maiúsculas ou acentos, sugestões por teclado (setas e Enter) e seleção explícita antes do chute.
- O quinto passe encerra a rodada, com texto específico avisando antes.
- Compartilhamento nativo quando disponível, cópia e alternativa manual. O texto inclui o link e os quadrados, sem o nome do jogador.
- Contagem regressiva e troca de desafio à meia-noite de Brasília (UTC−03), usando a data do servidor.
- Estatísticas de partidas encerradas, percentual de vitórias e sequência de dias consecutivos.

## Uma rodada por dia sem conta

Um cookie anônimo, HttpOnly e SameSite=Lax identifica o navegador. Os lances ficam no SQLite, com chave única por identificação e data. O servidor valida cada tentativa, esconde pistas futuras e a resposta, e usa transação com versão da rodada para evitar consumo duplicado em requisições simultâneas. Recarregar ou abrir outra aba recupera a mesma partida; apagar localStorage não a reinicia.

**O limite é por identificação do navegador, não por pessoa.** Limpar cookies, usar outro navegador, janela anônima ou outro dispositivo permite outra identificação. Sem identificar o usuário, não existe garantia absoluta de uma partida por pessoa. IP e fingerprint não resolvem essa identidade com confiabilidade. Não há conta, coleta de e-mail ou fingerprint neste MVP.

O relógio do dispositivo não define o desafio. As estatísticas antigas do MVP Camisa 10, armazenadas em localStorage, não são migradas para o servidor.

## Arquivos

- `index.html`: interface e diálogos acessíveis.
- `styles.css`: identidade visual e layouts mobile/desktop.
- `app.js`: busca, interação, sincronização entre abas e compartilhamento.
- `server.py`: HTTP/API, calendário, regras e persistência.
- `data/players.json`: catálogo versionado, acessível apenas no servidor.
- `data/ATTRIBUTION.md`: fonte, licença e alterações do catálogo.
- `scripts/import_players.py`: reprodução da importação dos CSVs originais.
- `tests/test_game.py`: testes de integração com HTTP e banco temporário.
- `.runtime/game.sqlite3`: banco local gerado automaticamente e ignorado pelo Git.

## Publicidade

Há espaços reservados, sem scripts de anúncios ativos:

- Desktop: área lateral, fora do cartão de jogo.
- Mobile: a lateral some; permanece o espaço abaixo do jogo e da contagem regressiva.
- Rodapé da área principal: faixa com altura reservada para evitar deslocar o conteúdo.

Os blocos são demonstrativos, não uma integração AdSense. Para veicular anúncios é necessário configurar a conta, o domínio e as unidades reais. Preserve a separação dos controles; configure tamanhos compatíveis com o contêiner e revise as exigências aplicáveis de privacidade e consentimento antes de ativar scripts de terceiros. A declaração no diálogo de privacidade deve ser atualizada quando anúncios forem ativados.

## Validação

```powershell
python -m unittest discover -s tests -v
node --check app.js
```

11 testes cobrem integridade do catálogo, ciclo sem repetição, resposta e arquivos privados não expostos, vitória na primeira e quinta chances, derrota e bloqueio da sexta tentativa, retomada, concorrência, palpites inválidos/repetidos, meia-noite, sequência e busca sem acentos. Node é opcional, apenas para a checagem de sintaxe JS. A revisão visual e a interação real no navegador permanecem pendentes: a ferramenta de navegador desta sessão falhou ao conectar.

## Publicação

O servidor incluído é para desenvolvimento e validação do MVP. O projeto deixou de ser puramente estático: precisa de um processo Python e armazenamento persistente. Antes de disponibilizar publicamente, use infraestrutura HTTP apropriada para produção, HTTPS, limitação de requisições, backups e persistência do banco. Não exponha toda a pasta como arquivos estáticos: `server.py` serve apenas os arquivos públicos permitidos.

Configurações por variáveis de ambiente:

- `HOST`: padrão `127.0.0.1`.
- `PORT`: padrão `8000`.
- `GOLGUESS_DB`: caminho do SQLite (padrão `.runtime/game.sqlite3`).
- `GOLGUESS_SECURE_COOKIE=1`: habilitar em HTTPS para enviar o cookie somente em conexões seguras.

Nenhum deploy ou configuração de anúncios foi realizado.

## Dados e licença

Catálogo derivado da [Fjelstul World Cup Database](https://github.com/jfjelstul/worldcup), © 2023 Joshua C. Fjelstul, Ph.D., sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode). O catálogo adaptado mantém essa licença. Foram selecionados convocados de 2022, unidos os dados de nascimento, traduzidos países/posições e reduzidos os campos. Veja `data/ATTRIBUTION.md`.
