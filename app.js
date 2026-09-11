'use strict';
const $ = id => document.getElementById(id);
const copy = {
  pt: {
    dailyPlayer:'Jogador do dia', guess:'Chutar', retry:'Tentar novamente', share:'Compartilhar', nextGame:'Próximo jogador em', guesses:'Palpites', privacy:'Privacidade', data:'Dados', howTitle:'Como jogar', help1:'Leia a primeira pista.', help2:'Escolha um jogador ou revele outra pista.', help3:'Acerte em até cinco tentativas.', play:'Jogar', statsTitle:'Estatísticas', played:'Partidas', winRate:'Vitórias', streak:'Sequência', privacyText:'Um cookie anônimo mantém sua rodada neste navegador. Não pedimos nome ou e-mail.', catalogText:'jogadores conhecidos de sete grandes ligas.', methodology:'Créditos e metodologia ↗', copy:'Copiar resultado',
    labels:['Liga e temporada','Gols e assistências','Cartões','Idade atual','Time da temporada'], locked:'Bloqueada', playerPlaceholder:'Qual jogador?', skip:'Pular · revelar pista', skipName:'Pista revelada', noResults:'Nenhum jogador encontrado', selected:'Jogador selecionado.', pick:'Selecione um nome da lista.', newClue:'Nova pista revelada.', wrong:'Não foi dessa vez. Nova pista revelada.', loadError:'Não conseguimos acessar o jogo. Tente novamente.', guessError:'Não foi possível registrar o palpite.', searchError:'A busca falhou. Tente novamente.', goal:n=>`Golaço! ${n}/5`, loss:name=>`Era ${name}.`, lossText:'Hoje não deu. Amanhã tem mais.', gameOver:'FIM DE JOGO', shareLine:'Você conhece esse jogador?', copied:'Resultado copiado ✓', yellow:'cartões amarelos', red:'cartões vermelhos', years:'anos', goals:'gols', assists:'assist.', attempt:'Tentativa', available:'disponível', wrongAttempt:'incorreta', skippedAttempt:'pulada', correctAttempt:'correta', close:'Fechar', stats:'Estatísticas', help:'Como jogar', language:'Selecionar idioma', searchLabel:'Jogadores encontrados'
  },
  en: {
    dailyPlayer:'Player of the day', guess:'Guess', retry:'Try again', share:'Share', nextGame:'Next player in', guesses:'Guesses', privacy:'Privacy', data:'Data', howTitle:'How to play', help1:'Read the first clue.', help2:'Pick a player or reveal another clue.', help3:'Find the player in five tries.', play:'Play', statsTitle:'Statistics', played:'Played', winRate:'Win rate', streak:'Streak', privacyText:'An anonymous cookie keeps your round in this browser. We do not ask for your name or email.', catalogText:'well-known players from seven major leagues.', methodology:'Credits and methodology ↗', copy:'Copy result',
    labels:['League and season','Goals and assists','Cards','Current age','Season club'], locked:'Locked', playerPlaceholder:'Which player?', skip:'Skip · reveal clue', skipName:'Clue revealed', noResults:'No players found', selected:'Player selected.', pick:'Choose a name from the list.', newClue:'New clue revealed.', wrong:'Not this time. New clue revealed.', loadError:'We could not reach the game. Try again.', guessError:'We could not save your guess.', searchError:'Search failed. Try again.', goal:n=>`Goal! ${n}/5`, loss:name=>`It was ${name}.`, lossText:'Not today. Come back tomorrow.', gameOver:'FULL TIME', shareLine:'Do you know this player?', copied:'Result copied ✓', yellow:'yellow cards', red:'red cards', years:'years', goals:'goals', assists:'assists', attempt:'Attempt', available:'available', wrongAttempt:'wrong', skippedAttempt:'skipped', correctAttempt:'correct', close:'Close', stats:'Statistics', help:'How to play', language:'Select language', searchLabel:'Players found'
  },
  es: {
    dailyPlayer:'Jugador del día', guess:'Adivinar', retry:'Intentar de nuevo', share:'Compartir', nextGame:'Próximo jugador en', guesses:'Intentos', privacy:'Privacidad', data:'Datos', howTitle:'Cómo jugar', help1:'Lee la primera pista.', help2:'Elige un jugador o revela otra pista.', help3:'Acierta en cinco intentos.', play:'Jugar', statsTitle:'Estadísticas', played:'Partidas', winRate:'Victorias', streak:'Racha', privacyText:'Una cookie anónima guarda tu partida en este navegador. No pedimos nombre ni correo.', catalogText:'jugadores conocidos de siete grandes ligas.', methodology:'Créditos y metodología ↗', copy:'Copiar resultado',
    labels:['Liga y temporada','Goles y asistencias','Tarjetas','Edad actual','Club de la temporada'], locked:'Bloqueada', playerPlaceholder:'¿Qué jugador?', skip:'Saltar · revelar pista', skipName:'Pista revelada', noResults:'No se encontraron jugadores', selected:'Jugador seleccionado.', pick:'Elige un nombre de la lista.', newClue:'Nueva pista revelada.', wrong:'No fue esta vez. Nueva pista revelada.', loadError:'No pudimos acceder al juego. Inténtalo de nuevo.', guessError:'No pudimos guardar tu intento.', searchError:'La búsqueda falló. Inténtalo de nuevo.', goal:n=>`¡Golazo! ${n}/5`, loss:name=>`Era ${name}.`, lossText:'Hoy no pudo ser. Mañana hay otra.', gameOver:'FINAL', shareLine:'¿Conoces a este jugador?', copied:'Resultado copiado ✓', yellow:'tarjetas amarillas', red:'tarjetas rojas', years:'años', goals:'goles', assists:'asist.', attempt:'Intento', available:'disponible', wrongAttempt:'incorrecto', skippedAttempt:'saltado', correctAttempt:'correcto', close:'Cerrar', stats:'Estadísticas', help:'Cómo jugar', language:'Seleccionar idioma', searchLabel:'Jugadores encontrados'
  }
};
let lang = (() => { try { return localStorage.getItem('golguess-lang') || 'pt'; } catch { return 'pt'; } })();
if (!copy[lang]) lang = 'pt';
let game, selected = null, results = [], active = -1, busy = false, loading = false;
let queryTimer, searchController, blurTimer, serverOffset = 0, nextRefresh = 0;
const input = $('guessInput');
const channel = 'BroadcastChannel' in window ? new BroadcastChannel('golguess-round') : null;
const marks = {correct:'🟩', wrong:'🟥', skip:'🟨'};
const t = key => copy[lang][key];

function feedback(message = '', error = false) {
  $('feedback').textContent = message;
  $('feedback').classList.toggle('error', error);
}
function closeSearch() {
  clearTimeout(blurTimer);
  $('suggestions').hidden = true;
  input.setAttribute('aria-expanded', 'false');
  input.removeAttribute('aria-activedescendant');
  active = -1;
}
function resetSearch() {
  clearTimeout(queryTimer);
  searchController?.abort();
  selected = null; results = []; input.value = ''; $('clearBtn').hidden = true; closeSearch();
}
function controls() {
  input.disabled = busy || !game || game.done;
  $('guessBtn').disabled = input.disabled || !selected;
  $('skipBtn').disabled = input.disabled || game?.clues.length >= 5;
  $('skipBtn').hidden = !!game && (game.done || game.clues.length >= 5);
  $('clearBtn').disabled = busy;
}
function applyLanguage() {
  document.documentElement.lang = {pt:'pt-BR',en:'en',es:'es'}[lang];
  document.querySelectorAll('[data-i18n]').forEach(el => el.textContent = t(el.dataset.i18n));
  input.placeholder = t('playerPlaceholder');
  $('skipBtn').textContent = t('skip');
  $('statsBtn').setAttribute('aria-label', t('stats')); $('statsBtn').title = t('stats');
  $('helpBtn').setAttribute('aria-label', t('help')); $('helpBtn').title = t('help');
  $('languageMenu').querySelector('summary').setAttribute('aria-label', t('language'));
  $('suggestions').setAttribute('aria-label', t('searchLabel'));
  document.querySelectorAll('.dialog-close').forEach(button => button.setAttribute('aria-label', t('close')));
  document.querySelectorAll('[data-lang]').forEach(button => button.setAttribute('aria-checked', String(button.dataset.lang === lang)));
  if (game) render();
}
function accept(data) {
  if (game && (data.day < game.day || (data.day === game.day && data.version < game.version))) return;
  const changed = game && (game.day !== data.day || game.version !== data.version);
  if (changed) resetSearch();
  game = data;
  serverOffset = Date.parse(data.serverTime) - Date.now();
  render();
}
function clueContent(clue, index) {
  const value = document.createElement('div'); value.className = 'clue-value';
  if (index === 0 && clue.league) {
    value.classList.add('league-value');
    const league = document.createElement('span'); league.textContent = clue.league;
    const season = document.createElement('span'); season.className = 'season'; season.textContent = clue.season;
    value.append(league, season);
  } else if (index === 1 && Number.isInteger(clue.goals)) {
    value.classList.add('metrics');
    [['goals', clue.goals], ['assists', clue.assists]].forEach(([label, number]) => {
      const metric = document.createElement('span'); metric.className = 'metric';
      const strong = document.createElement('strong'); strong.textContent = number;
      const small = document.createElement('small'); small.textContent = t(label);
      metric.append(strong, small); value.append(metric);
    });
  } else if (index === 2 && Number.isInteger(clue.yellow)) {
    value.classList.add('cards');
    [['yellow', clue.yellow], ['red', clue.red]].forEach(([type, number]) => {
      const item = document.createElement('span'); item.className = 'card-count'; item.setAttribute('aria-label', `${number} ${t(type)}`);
      const icon = document.createElement('i'); icon.className = `card-icon ${type === 'red' ? 'red' : ''}`; icon.setAttribute('aria-hidden', 'true');
      const count = document.createElement('span'); count.textContent = number; count.setAttribute('aria-hidden', 'true');
      item.append(icon, count); value.append(item);
    });
  } else if (index === 3 && Number.isInteger(clue.age)) {
    value.classList.add('age-value');
    const strong = document.createElement('strong'); strong.textContent = clue.age;
    const small = document.createElement('small'); small.textContent = t('years');
    value.append(strong, small);
  } else if (index === 4 && clue.team) {
    value.classList.add('team-value');
    const shield = document.createElement('i'); shield.className = 'shield'; shield.setAttribute('aria-hidden', 'true'); shield.textContent = clue.team.slice(0, 1).toUpperCase();
    const team = document.createElement('span'); team.textContent = clue.team;
    value.append(shield, team);
  } else value.textContent = clue.value;
  return value;
}
function renderClues() {
  $('clues').replaceChildren(...t('labels').map((label, index) => {
    const clue = game.clues[index];
    const li = document.createElement('li');
    li.className = `clue ${!clue ? 'locked' : index === game.clues.length - 1 && !game.done ? 'latest' : ''}`;
    const number = document.createElement('span'); number.className = 'clue-index'; number.textContent = clue ? index + 1 : '🔒'; number.setAttribute('aria-hidden', 'true');
    const title = document.createElement('span'); title.className = 'clue-label'; title.textContent = label;
    const value = clue ? clueContent(clue, index) : document.createElement('span');
    if (!clue) { value.className = 'clue-value'; value.textContent = t('locked'); li.setAttribute('aria-label', `${label}: ${t('locked')}`); }
    li.append(number, title, value); return li;
  }));
}
function renderAttempts() {
  $('attemptDots').replaceChildren(...Array.from({length:5}, (_, index) => {
    const move = game.moves[index];
    const marker = document.createElement('span'); marker.className = `attempt-marker ${move?.result || ''}`;
    marker.textContent = move ? ({wrong:'×',skip:'—',correct:'✓'}[move.result]) : index + 1;
    const state = move ? t({wrong:'wrongAttempt',skip:'skippedAttempt',correct:'correctAttempt'}[move.result]) : t('available');
    marker.setAttribute('aria-label', `${t('attempt')} ${index + 1}: ${state}`); return marker;
  }));
}
function render() {
  $('game').setAttribute('aria-busy', 'false');
  $('dayNumber').textContent = '#' + String(game.number).padStart(3, '0');
  renderClues(); renderAttempts();
  $('playArea').hidden = game.done; $('result').hidden = !game.done;
  $('historyArea').hidden = !game.moves.length;
  $('history').replaceChildren(...game.moves.map(move => {
    const li = document.createElement('li'); li.className = move.result;
    const mark = document.createElement('b'); mark.setAttribute('aria-hidden', 'true'); mark.textContent = {wrong:'×',correct:'✓',skip:'—'}[move.result];
    const name = document.createElement('span'); name.textContent = move.result === 'skip' ? t('skipName') : move.name;
    li.append(mark, name); return li;
  }));
  $('played').textContent = game.stats.played;
  $('wins').textContent = (game.stats.played ? Math.round(game.stats.wins / game.stats.played * 100) : 0) + '%';
  $('streak').textContent = game.stats.streak;
  $('catalogCount').textContent = game.totalPlayers;
  if (game.done) {
    $('result').classList.toggle('lost', !game.won);
    $('resultKicker').textContent = t('gameOver');
    $('resultTitle').textContent = game.won ? t('goal')(game.moves.length) : t('loss')(game.answer);
    $('resultText').textContent = game.won ? game.answer : t('lossText');
    $('resultSquares').textContent = squares();
  }
  controls(); tick();
}
async function loadGame() {
  if (loading || busy) return;
  loading = true;
  try {
    const response = await fetch('/api/game', {cache:'no-store'});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || t('loadError'));
    accept(data); $('retryBtn').hidden = true; feedback();
  } catch (error) {
    feedback(error.message === 'Failed to fetch' ? t('loadError') : error.message, true);
    $('retryBtn').hidden = false; $('game').setAttribute('aria-busy', 'false');
  } finally { loading = false; }
}
function choose(index) {
  clearTimeout(blurTimer);
  if (!results[index]) return;
  selected = results[index]; input.value = selected.name; closeSearch(); controls(); feedback(t('selected')); input.focus();
}
function highlight(index) {
  active = index;
  [...$('suggestions').children].forEach((el, i) => el.setAttribute('aria-selected', String(i === active)));
  input.setAttribute('aria-activedescendant', `player-option-${index}`);
  $('suggestions').children[index]?.scrollIntoView({block:'nearest'});
}
function showResults() {
  if (!results.length) {
    const empty = document.createElement('li'); empty.className = 'empty'; empty.setAttribute('role', 'status'); empty.textContent = t('noResults');
    $('suggestions').replaceChildren(empty);
  } else {
    $('suggestions').replaceChildren(...results.map((player, index) => {
      const li = document.createElement('li'); li.id = `player-option-${index}`; li.setAttribute('role', 'option'); li.setAttribute('aria-selected', 'false'); li.textContent = player.name;
      li.addEventListener('click', () => choose(index)); return li;
    }));
  }
  $('suggestions').hidden = false; input.setAttribute('aria-expanded', 'true');
}
input.addEventListener('input', () => {
  selected = null; results = []; controls(); closeSearch(); feedback();
  $('clearBtn').hidden = !input.value; clearTimeout(queryTimer); searchController?.abort();
  const query = input.value.trim(); if (!query) return;
  queryTimer = setTimeout(async () => {
    const controller = new AbortController(); searchController = controller;
    try {
      const response = await fetch('/api/players?q=' + encodeURIComponent(query), {signal:controller.signal});
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (input.value.trim() !== query || controller.signal.aborted) return;
      results = data.filter(player => !game.moves.some(move => move.id === player.id)); showResults();
    } catch (error) { if (error.name !== 'AbortError') feedback(t('searchError'), true); }
  }, 180);
});
input.addEventListener('keydown', event => {
  if (event.key === 'Escape') closeSearch();
  if (!$('suggestions').hidden && results.length) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); highlight((active + (event.key === 'ArrowDown' ? 1 : -1) + results.length) % results.length); }
    if (event.key === 'Enter') { event.preventDefault(); if (active >= 0) choose(active); else if (results.length === 1) choose(0); else feedback(t('pick')); }
  }
});
input.addEventListener('blur', () => { blurTimer = setTimeout(closeSearch, 200); });
input.addEventListener('focus', () => clearTimeout(blurTimer));
$('suggestions').addEventListener('pointerdown', () => clearTimeout(blurTimer));
$('clearBtn').onclick = () => { resetSearch(); controls(); feedback(); input.focus(); };
async function submit(playerId) {
  if (busy || !game || game.done) return;
  busy = true; controls(); feedback(); closeSearch();
  try {
    const response = await fetch('/api/guess', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({day:game.day, version:game.version, playerId})});
    const data = await response.json();
    if (!response.ok) { if (data.game) accept(data.game); feedback(data.error || t('guessError'), true); return; }
    resetSearch(); accept(data); channel?.postMessage('updated');
    feedback(game.done ? '' : playerId === null ? t('newClue') : t('wrong'));
    if (game.done) { $('resultTitle').tabIndex = -1; $('resultTitle').focus({preventScroll:true}); }
  } catch { feedback(t('guessError'), true); $('retryBtn').hidden = false; }
  finally { busy = false; controls(); }
}
$('guessForm').onsubmit = event => { event.preventDefault(); if (selected) submit(selected.id); else feedback(t('pick')); };
$('skipBtn').onclick = () => submit(null);
$('retryBtn').onclick = loadGame;
function tick() {
  if (!game) return;
  const remaining = Math.max(0, Math.ceil((Date.parse(game.nextAt) - Date.now() - serverOffset) / 1000));
  const text = [Math.floor(remaining/3600), Math.floor(remaining/60)%60, remaining%60].map(number => String(number).padStart(2,'0')).join(':');
  document.querySelectorAll('.countdown').forEach(element => element.textContent = text);
  if (!remaining && Date.now() > nextRefresh) { nextRefresh = Date.now() + 10000; loadGame(); }
}
function squares() { return Array.from({length:5}, (_, index) => marks[game.moves[index]?.result] || '⬜').join(''); }
function shareText() { return `GolGuess #${String(game.number).padStart(3,'0')} ⚽ ${game.won ? game.moves.length : 'X'}/5\n${squares()}\n${t('shareLine')}\n${location.origin}/`; }
function shareFallback(text) { $('shareText').value = text; $('copyBtn').textContent = t('copy'); $('shareDialog').showModal(); $('shareText').select(); }
$('shareBtn').onclick = async () => {
  const text = shareText();
  try { if (navigator.share) { await navigator.share({text}); return; } await navigator.clipboard.writeText(text); $('shareBtn').textContent = t('copied'); }
  catch (error) { if (error.name !== 'AbortError') shareFallback(text); }
};
$('copyBtn').onclick = async () => { try { await navigator.clipboard.writeText($('shareText').value); $('copyBtn').textContent = t('copied'); } catch { $('shareText').focus(); $('shareText').select(); } };
for (const name of ['help','stats','privacy','sources']) $(name + 'Btn').onclick = () => $(name + 'Dialog').showModal();
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.querySelector('.dialog-close').onclick = () => dialog.close();
  dialog.querySelector('.dialog-done')?.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
});
document.querySelectorAll('[data-lang]').forEach(button => button.onclick = () => {
  lang = button.dataset.lang; try { localStorage.setItem('golguess-lang', lang); } catch {}
  $('languageMenu').open = false; applyLanguage(); feedback();
});
channel?.addEventListener('message', loadGame);
setInterval(tick, 1000);
applyLanguage();
loadGame();
