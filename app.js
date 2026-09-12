'use strict';
const $ = id => document.getElementById(id);
const copy = {
  pt: {
    modePlayers:'Jogadores', modeTeams:'Times',
    dailyPlayer:'Adivinhe o jogador de futebol de hoje', dailyTeam:'Adivinhe o time de futebol de hoje',
    pageTitle:'GolGuess – Adivinhe o Jogador de Futebol | Desafio Diário',
    pageTitleTeam:'GolGuess – Adivinhe o Time de Futebol | Desafio Diário',
    aboutGame:'O <strong>GolGuess</strong> é um jogo diário de futebol feito para quem ama o esporte. A cada dia, um novo jogador misterioso é escolhido: use seus palpites para revelar pistas de liga, temporada, gols, assistências, cartões, idade e clubes até acertar o nome em até cinco tentativas.',
    aboutGameTeam:'O <strong>GolGuess</strong> Times é um jogo diário de clubes de futebol. A cada rodada, descubra o clube misterioso através de pistas sobre continente, títulos de liga, país, cores e cidade sede em até cinco tentativas.',
    guess:'Chutar', retry:'Tentar novamente', share:'Compartilhar',
    nextGame:'Próximo jogador em', nextTeam:'Próximo time em',
    guesses:'Palpites', privacy:'Privacidade', data:'Dados',
    howTitle:'Como jogar',
    help1:'Leia a primeira pista.', help2:'Escolha um jogador ou revele outra pista.', help3:'Acerte em até cinco tentativas.',
    help1Team:'Leia a primeira pista sobre o time.', help2Team:'Escolha um time ou revele outra pista.', help3Team:'Acerte o time em até cinco tentativas.',
    play:'Jogar', statsTitle:'Estatísticas', played:'Partidas', winRate:'Vitórias', streak:'Sequência',
    privacyText:'Um cookie anônimo mantém sua rodada neste navegador. Não pedimos nome ou e-mail.',
    catalogText:'jogadores conhecidos de sete grandes ligas.',
    catalogTeamsText:'times das 13 principais ligas das Américas e Europa.',
    methodology:'Créditos e metodologia ↗', copy:'Copiar resultado',
    labels:['Liga e temporada','Gols e assistências','Cartões','Idade atual','Time da temporada'],
    teamLabels:['Continente','Títulos de liga','País','Cores','Cidade'],
    locked:'Bloqueada', playerPlaceholder:'Qual jogador?', teamPlaceholder:'Qual time?',
    skip:'Pular · revelar pista', skipName:'Pista revelada',
    noResults:'Nenhum jogador encontrado', noTeamsResults:'Nenhum time encontrado',
    selected:'Jogador selecionado.', selectedTeam:'Time selecionado.',
    pick:'Selecione um nome da lista.', pickTeam:'Selecione um time da lista.',
    newClue:'Nova pista revelada.', wrong:'Não foi dessa vez. Nova pista revelada.',
    loadError:'Não conseguimos acessar o jogo. Tente novamente.',
    guessError:'Não foi possível registrar o palpite.', searchError:'A busca falhou. Tente novamente.',
    goal:n=>`Golaço! ${n}/5`, loss:name=>`Era ${name}.`, lossText:'Hoje não deu. Amanhã tem mais.',
    gameOver:'FIM DE JOGO', shareLine:'Você conhece esse jogador?', shareLineTeams:'Você conhece esse time?',
    copied:'Resultado copiado ✓', yellow:'cartões amarelos', red:'cartões vermelhos', years:'anos',
    goals:'gols', assists:'assist.', titleSingular:'título', titlePlural:'títulos',
    attempt:'Tentativa', available:'disponível', wrongAttempt:'incorreta', skippedAttempt:'pulada',
    correctAttempt:'correta', close:'Fechar', stats:'Estatísticas', help:'Como jogar',
    language:'Selecionar idioma', searchLabel:'Jogadores encontrados', searchTeamsLabel:'Times encontrados'
  },
  en: {
    modePlayers:'Players', modeTeams:'Teams',
    dailyPlayer:'Guess today’s football player', dailyTeam:'Guess today’s football club',
    pageTitle:'GolGuess – Guess the Football Player | Daily Challenge',
    pageTitleTeam:'GolGuess – Guess the Football Club | Daily Challenge',
    aboutGame:'<strong>GolGuess</strong> is a daily football trivia game. Every day, a new mystery player is selected: make your guesses to reveal clues about league, season, goals, assists, cards, age, and clubs until you find the answer in up to 5 attempts.',
    aboutGameTeam:'<strong>GolGuess</strong> Teams is a daily football club trivia challenge. Guess today\'s mystery football club with clues about continent, league titles, country, colors, and home city in up to 5 attempts.',
    guess:'Guess', retry:'Try again', share:'Share',
    nextGame:'Next player in', nextTeam:'Next team in',
    guesses:'Guesses', privacy:'Privacy', data:'Data',
    howTitle:'How to play',
    help1:'Read the first clue.', help2:'Pick a player or reveal another clue.', help3:'Find the player in five tries.',
    help1Team:'Read the first clue about the club.', help2Team:'Pick a team or reveal another clue.', help3Team:'Find the team in five tries.',
    play:'Play', statsTitle:'Statistics', played:'Played', winRate:'Win rate', streak:'Streak',
    privacyText:'An anonymous cookie keeps your round in this browser. We do not ask for your name or email.',
    catalogText:'well-known players from seven major leagues.',
    catalogTeamsText:'teams from 13 top leagues across the Americas and Europe.',
    methodology:'Credits and methodology ↗', copy:'Copy result',
    labels:['League and season','Goals and assists','Cards','Current age','Season club'],
    teamLabels:['Continent','League titles','Country','Colors','City'],
    locked:'Locked', playerPlaceholder:'Which player?', teamPlaceholder:'Which team?',
    skip:'Skip · reveal clue', skipName:'Clue revealed',
    noResults:'No players found', noTeamsResults:'No teams found',
    selected:'Player selected.', selectedTeam:'Team selected.',
    pick:'Choose a name from the list.', pickTeam:'Choose a team from the list.',
    newClue:'New clue revealed.', wrong:'Not this time. New clue revealed.',
    loadError:'We could not reach the game. Try again.',
    guessError:'We could not save your guess.', searchError:'Search failed. Try again.',
    goal:n=>`Goal! ${n}/5`, loss:name=>`It was ${name}.`, lossText:'Not today. Come back tomorrow.',
    gameOver:'FULL TIME', shareLine:'Do you know this player?', shareLineTeams:'Do you know this team?',
    copied:'Result copied ✓', yellow:'yellow cards', red:'red cards', years:'years',
    goals:'goals', assists:'assists', titleSingular:'title', titlePlural:'titles',
    attempt:'Attempt', available:'available', wrongAttempt:'wrong', skippedAttempt:'skipped',
    correctAttempt:'correct', close:'Close', stats:'Statistics', help:'How to play',
    language:'Select language', searchLabel:'Players found', searchTeamsLabel:'Teams found'
  },
  es: {
    modePlayers:'Jugadores', modeTeams:'Times',
    dailyPlayer:'Adivina el futbolista de hoy', dailyTeam:'Adivina el equipo de fútbol de hoy',
    pageTitle:'GolGuess – Adivina el Futbolista | Desafío Diario',
    pageTitleTeam:'GolGuess – Adivina el Equipo | Desafío Diario',
    aboutGame:'<strong>GolGuess</strong> es un juego diario de fútbol. Cada día se selecciona un nuevo jugador misterioso: usa tus intentos para descubrir pistas sobre liga, temporada, goles, asistencias, tarjetas, edad y clubes hasta acertar en un máximo de 5 intentos.',
    aboutGameTeam:'<strong>GolGuess</strong> Equipos es un desafío diario de clubes de fútbol. Adivina el club misterioso con pistas de continente, títulos de liga, país, colores y ciudad en hasta 5 intentos.',
    guess:'Adivinar', retry:'Intentar de nuevo', share:'Compartir',
    nextGame:'Próximo jugador en', nextTeam:'Próximo equipo en',
    guesses:'Intentos', privacy:'Privacidade', data:'Datos',
    howTitle:'Cómo jugar',
    help1:'Lee la primera pista.', help2:'Elige un jugador o revela otra pista.', help3:'Acierta en cinco intentos.',
    help1Team:'Lee la primera pista sobre el club.', help2Team:'Elige un equipo o revela otra pista.', help3Team:'Acierta el equipo en cinco intentos.',
    play:'Jugar', statsTitle:'Estadísticas', played:'Partidas', winRate:'Victorias', streak:'Racha',
    privacyText:'Una cookie anónima guarda tu partida en este navegador. No pedimos nombre ni correo.',
    catalogText:'jugadores conocidos de siete grandes ligas.',
    catalogTeamsText:'equipos de las 13 principales ligas de América y Europa.',
    methodology:'Créditos y metodología ↗', copy:'Copiar resultado',
    labels:['Liga y temporada','Goles y asistencias','Tarjetas','Edad actual','Club de la temporada'],
    teamLabels:['Continente','Títulos de liga','País','Colores','Ciudad'],
    locked:'Bloqueada', playerPlaceholder:'¿Qué jugador?', teamPlaceholder:'¿Qué equipo?',
    skip:'Saltar · revelar pista', skipName:'Pista revelada',
    noResults:'No se encontraron jugadores', noTeamsResults:'No se encontraron equipos',
    selected:'Jugador seleccionado.', selectedTeam:'Equipo seleccionado.',
    pick:'Elige un nombre de la lista.', pickTeam:'Elige un equipo de la lista.',
    newClue:'Nueva pista revelada.', wrong:'No fue esta vez. Nueva pista revelada.',
    loadError:'No pudimos acceder al juego. Inténtalo de nuevo.',
    guessError:'No pudimos guardar tu intento.', searchError:'La búsqueda falló. Inténtalo de nuevo.',
    goal:n=>`¡Golazo! ${n}/5`, loss:name=>`Era ${name}.`, lossText:'Hoy no pudo ser. Mañana hay otra.',
    gameOver:'FINAL', shareLine:'¿Conoces a este jugador?', shareLineTeams:'¿Conoces a este equipo?',
    copied:'Resultado copiado ✓', yellow:'tarjetas amarillas', red:'tarjetas rojas', years:'años',
    goals:'goles', assists:'asist.', titleSingular:'título', titlePlural:'títulos',
    attempt:'Intento', available:'disponible', wrongAttempt:'incorrecto', skippedAttempt:'saltado',
    correctAttempt:'correcto', close:'Cerrar', stats:'Estadísticas', help:'Cómo jugar',
    language:'Seleccionar idioma', searchLabel:'Jugadores encontrados', searchTeamsLabel:'Equipos encontrados'
  }
};
let lang = (() => { try { return localStorage.getItem('golguess-lang') || 'pt'; } catch { return 'pt'; } })();
if (!copy[lang]) lang = 'pt';
let mode = (() => {
  try {
    const p = new URLSearchParams(window.location.search);
    const m = p.get('jogo') || p.get('mode');
    if (m === 'times' || m === 'teams') return 'teams';
    return localStorage.getItem('golguess-mode') === 'teams' ? 'teams' : 'players';
  } catch {
    return 'players';
  }
})();
let game, selected = null, results = [], active = -1, busy = false, loading = false;
let queryTimer, searchController, blurTimer, serverOffset = 0, nextRefresh = 0;
const input = $('guessInput');
const channel = 'BroadcastChannel' in window ? new BroadcastChannel('golguess-channel') : null;
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
function updateModeButtons() {
  const isTeams = mode === 'teams';
  $('modePlayersBtn')?.classList.toggle('active', !isTeams);
  $('modePlayersBtn')?.setAttribute('aria-selected', String(!isTeams));
  $('modeTeamsBtn')?.classList.toggle('active', isTeams);
  $('modeTeamsBtn')?.setAttribute('aria-selected', String(isTeams));
}
function switchMode(newMode) {
  if (mode === newMode && game) return;
  mode = newMode;
  try { localStorage.setItem('golguess-mode', mode); } catch {}
  const url = new URL(window.location.href);
  if (mode === 'teams') {
    url.searchParams.set('jogo', 'times');
    url.searchParams.delete('mode');
  } else {
    url.searchParams.delete('jogo');
    url.searchParams.delete('mode');
  }
  window.history.replaceState({}, '', url.pathname + (url.search ? url.search : ''));
  game = null;
  resetSearch();
  applyLanguage();
  loadGame();
}
function applyLanguage() {
  document.documentElement.lang = {pt:'pt-BR',en:'en',es:'es'}[lang];
  document.querySelectorAll('[data-i18n]').forEach(el => el.textContent = t(el.dataset.i18n));
  const isTeams = mode === 'teams';
  document.title = isTeams ? t('pageTitleTeam') : t('pageTitle');
  $('roundKicker').textContent = isTeams ? t('dailyTeam') : t('dailyPlayer');
  if ($('aboutGameText')) {
    $('aboutGameText').innerHTML = isTeams ? t('aboutGameTeam') : t('aboutGame');
  }
  input.placeholder = isTeams ? t('teamPlaceholder') : t('playerPlaceholder');
  $('skipBtn').textContent = t('skip');
  if ($('nextGameLabel')) $('nextGameLabel').textContent = isTeams ? t('nextTeam') : t('nextGame');
  $('statsBtn').setAttribute('aria-label', t('stats')); $('statsBtn').title = t('stats');
  $('helpBtn').setAttribute('aria-label', t('help')); $('helpBtn').title = t('help');
  $('languageMenu').querySelector('summary').setAttribute('aria-label', t('language'));
  $('suggestions').setAttribute('aria-label', isTeams ? t('searchTeamsLabel') : t('searchLabel'));
  document.querySelectorAll('.dialog-close').forEach(button => button.setAttribute('aria-label', t('close')));
  document.querySelectorAll('[data-lang]').forEach(button => button.setAttribute('aria-checked', String(button.dataset.lang === lang)));

  if ($('helpStep1')) $('helpStep1').textContent = isTeams ? t('help1Team') : t('help1');
  if ($('helpStep2')) $('helpStep2').textContent = isTeams ? t('help2Team') : t('help2');
  if ($('helpStep3')) $('helpStep3').textContent = isTeams ? t('help3Team') : t('help3');
  if ($('catalogLabel')) $('catalogLabel').textContent = isTeams ? t('catalogTeamsText') : t('catalogText');

  updateModeButtons();
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
  if (mode === 'teams') {
    if (index === 0) {
      value.classList.add('continent-value');
      const badge = document.createElement('span'); badge.className = 'continent-badge';
      badge.textContent = clue.continent || clue.value;
      value.append(badge);
    } else if (index === 1 && (Number.isInteger(clue.titles) || Number.isInteger(clue.value))) {
      value.classList.add('titles-value');
      const num = Number.isInteger(clue.titles) ? clue.titles : clue.value;
      const strong = document.createElement('strong'); strong.textContent = num;
      const small = document.createElement('small'); small.textContent = num === 1 ? t('titleSingular') : t('titlePlural');
      value.append(strong, small);
    } else if (index === 2) {
      value.classList.add('country-value');
      value.textContent = clue.country || clue.value;
    } else if (index === 3) {
      value.classList.add('colors-value');
      value.textContent = clue.colors || clue.value;
    } else if (index === 4) {
      value.classList.add('city-value');
      value.textContent = clue.city || clue.value;
    } else value.textContent = clue.value;
    return value;
  }
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
  const labels = mode === 'teams' ? t('teamLabels') : t('labels');
  $('clues').replaceChildren(...labels.map((label, index) => {
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
  $('catalogCount').textContent = mode === 'teams' ? (game.totalTeams || 269) : game.totalPlayers;
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
  $('game').setAttribute('aria-busy', 'true');
  try {
    const response = await fetch(`/api/game?mode=${mode}`, {cache:'no-store'});
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
  selected = results[index]; input.value = selected.name; closeSearch(); controls();
  feedback(mode === 'teams' ? t('selectedTeam') : t('selected'));
  input.focus();
}
function highlight(index) {
  active = index;
  [...$('suggestions').children].forEach((el, i) => el.setAttribute('aria-selected', String(i === active)));
  input.setAttribute('aria-activedescendant', `option-${index}`);
  $('suggestions').children[index]?.scrollIntoView({block:'nearest'});
}
function showResults() {
  if (!results.length) {
    const empty = document.createElement('li'); empty.className = 'empty'; empty.setAttribute('role', 'status');
    empty.textContent = mode === 'teams' ? t('noTeamsResults') : t('noResults');
    $('suggestions').replaceChildren(empty);
  } else {
    $('suggestions').replaceChildren(...results.map((item, index) => {
      const li = document.createElement('li'); li.id = `option-${index}`; li.setAttribute('role', 'option'); li.setAttribute('aria-selected', 'false');
      if (mode === 'teams') {
        const name = document.createElement('span'); name.textContent = item.name;
        const sub = document.createElement('span'); sub.className = 'suggestion-sub'; sub.textContent = `${item.league} · ${item.country}`;
        li.append(name, sub);
      } else {
        li.textContent = item.name;
      }
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
      const endpoint = (mode === 'teams' ? '/api/teams?q=' : '/api/players?q=') + encodeURIComponent(query);
      const response = await fetch(endpoint, {signal:controller.signal});
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (input.value.trim() !== query || controller.signal.aborted) return;
      results = data.filter(item => !game.moves.some(move => move.id === item.id)); showResults();
    } catch (error) { if (error.name !== 'AbortError') feedback(t('searchError'), true); }
  }, 180);
});
input.addEventListener('keydown', event => {
  if (event.key === 'Escape') closeSearch();
  if (!$('suggestions').hidden && results.length) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); highlight((active + (event.key === 'ArrowDown' ? 1 : -1) + results.length) % results.length); }
    if (event.key === 'Enter') { event.preventDefault(); if (active >= 0) choose(active); else if (results.length === 1) choose(0); else feedback(mode === 'teams' ? t('pickTeam') : t('pick')); }
  }
});
input.addEventListener('blur', () => { blurTimer = setTimeout(closeSearch, 200); });
input.addEventListener('focus', () => clearTimeout(blurTimer));
$('suggestions').addEventListener('pointerdown', () => clearTimeout(blurTimer));
$('clearBtn').onclick = () => { resetSearch(); controls(); feedback(); input.focus(); };
async function submit(guessId) {
  if (busy || !game || game.done) return;
  busy = true; controls(); feedback(); closeSearch();
  try {
    const body = {
      day: game.day,
      version: game.version,
      mode,
      playerId: mode === 'players' ? guessId : undefined,
      teamId: mode === 'teams' ? guessId : undefined
    };
    const response = await fetch('/api/guess', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok) { if (data.game) accept(data.game); feedback(data.error || t('guessError'), true); return; }
    resetSearch(); accept(data); channel?.postMessage({type:'updated', mode});
    feedback(game.done ? '' : guessId === null ? t('newClue') : t('wrong'));
    if (game.done) { $('resultTitle').tabIndex = -1; $('resultTitle').focus({preventScroll:true}); }
  } catch { feedback(t('guessError'), true); $('retryBtn').hidden = false; }
  finally { busy = false; controls(); }
}
$('guessForm').onsubmit = event => { event.preventDefault(); if (selected) submit(selected.id); else feedback(mode === 'teams' ? t('pickTeam') : t('pick')); };
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
function shareText() {
  const isTeams = mode === 'teams';
  const tag = isTeams ? `GolGuess Times #${String(game.number).padStart(3,'0')} 🛡️` : `GolGuess #${String(game.number).padStart(3,'0')} ⚽`;
  const url = isTeams ? `${location.origin}/?jogo=times` : `${location.origin}/`;
  const line = isTeams ? t('shareLineTeams') : t('shareLine');
  return `${tag} ${game.won ? game.moves.length : 'X'}/5\n${squares()}\n${line}\n${url}`;
}
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
$('modePlayersBtn').onclick = () => switchMode('players');
$('modeTeamsBtn').onclick = () => switchMode('teams');
window.addEventListener('popstate', () => {
  const p = new URLSearchParams(window.location.search);
  const m = p.get('jogo') || p.get('mode');
  const target = (m === 'times' || m === 'teams') ? 'teams' : 'players';
  if (target !== mode) switchMode(target);
});
channel?.addEventListener('message', event => {
  if (!event.data || event.data.mode === mode) loadGame();
});
setInterval(tick, 1000);
applyLanguage();
loadGame();
