# Camisa 10 — MVP

Exportação do código da primeira versão do jogo. O site publicado não foi alterado.

## Executar e editar

Abra esta pasta no seu editor. O arquivo `index.html` contém todo o HTML, CSS, dados e JavaScript, sem etapa de compilação ou dependências npm.

Use um servidor HTTP local, por exemplo a extensão Live Server do VS Code. Alternativamente, com Python instalado, execute na pasta:

```bash
python -m http.server 8000
```

Abra http://localhost:8000. No Windows, caso necessário, use `py` no lugar de `python`. As fontes são carregadas do Google Fonts; sem conexão, o navegador usa fontes alternativas.

## Onde editar

- `<style>`: cores, layout e responsividade.
- `players`: catálogo dos 40 jogadores e pistas.
- `T`: textos em português, inglês e espanhol.
- `clueData`: ordem e apresentação das pistas.
- `guess`, `advance` e `finish`: regras do jogo.
- `render`: atualização da interface.
- `localStorage`: progresso e estatísticas locais do navegador.

## Enviar ao seu Git

Crie um repositório remoto vazio. Dentro desta pasta, substitua a URL abaixo pela URL real do seu repositório:

```bash
git init
git add .
git commit -m "Adiciona MVP Camisa 10"
git branch -M main
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

Se usar um repositório já clonado, copie estes arquivos para ele e use seu fluxo habitual de add, commit e push. Nenhuma configuração da publicação original ou histórico Git foi incluído.

## Limitações conhecidas e pontos para evoluir

Esta é uma cópia fiel do MVP, não uma versão revisada para produção:

- As estatísticas do catálogo não foram verificadas contra fontes esportivas. Valide gols, assistências e cartões antes de disponibilizar o jogo ao público.
- As idades são valores fixos: substitua por datas de nascimento e cálculo dinâmico.
- Os dados de cartões estão em português mesmo quando o idioma da interface muda.
- O desafio utiliza a data UTC e repete o catálogo a cada 40 dias. Uma página aberta não troca automaticamente de desafio à meia-noite; precisa ser recarregada.
- O palpite correto não incrementa `tries`, afetando a contagem e os quadrados do compartilhamento.
- A sequência soma vitórias sem verificar se ocorreram em dias consecutivos.
- A busca precisa de melhorias de acessibilidade e navegação por teclado.
- Progresso e estatísticas ficam somente no navegador, sem conta ou sincronização. Limpar o armazenamento permite reiniciar a rodada.
- A resposta e o catálogo ficam visíveis no código do navegador; não existe proteção contra consulta da resposta.
- O botão de compartilhamento copia texto; a falha de permissão da área de transferência ainda não apresenta uma alternativa ao usuário.

Não há backend, API esportiva, banco de dados, autenticação ou credenciais neste pacote. Hospede o `index.html` em qualquer serviço de arquivos estáticos compatível.
