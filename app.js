'use strict';
const $ = id => document.getElementById(id);
let game, selected = null, results = [], active = -1, busy = false, loading = false;
let queryTimer, searchController, serverOffset = 0, nextRefresh = 0;
const input = $('guessInput');
const channel = 'BroadcastChannel' in window ? new BroadcastChannel('golguess-round') : null;
const labels = ['Liga e temporada', 'Gols e assistências', 'Cartões', 'Idade atual', 'Time'];
const marks = { correct: '🟩', wrong: '🟥', skip: '🟨' };
function feedback(message = '') { $('feedback').textContent = message; }
function closeSearch() {
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
  $('skipBtn').disabled = input.disabled;
  $('clearBtn').disabled = busy;
}
function accept(data) {
  if (game && (data.day < game.day || (data.day === game.day && data.version < game.version))) return;
  const changed = game && (game.day !== data.day || game.version !== data.version);
  if (changed) resetSearch();
  game = data;
  serverOffset = Date.parse(data.serverTime) - Date.now();
  render();
}
function render() {
  $('game').setAttribute('aria-busy', 'false');
  $('dayNumber').textContent = '#' + String(game.number).padStart(3, '0');
  $('clueCount').textContent = `${game.clues.length} de 5 reveladas`;
  $('clues').replaceChildren(...labels.map((label, i) => {
    const clue = game.clues[i], li = document.createElement('li');
    li.className = 'clue ' + (!clue ? 'locked' : i === game.clues.length - 1 && !game.done ? 'latest' : '');
    const number = document.createElement('span'); number.className = 'clue-number'; number.textContent = clue ? String(i + 1).padStart(2, '0') : '·';
    const title = document.createElement('span'); title.className = 'clue-label'; title.textContent = label;
    const value = document.createElement('span'); value.className = 'clue-value'; value.textContent = clue ? clue.value : 'A revelar';
    li.append(number, title, value); return li;
  }));
  const left = 5 - game.moves.length;
  $('attemptLabel').textContent = `${left} ${left === 1 ? 'chance restante' : 'chances restantes'}`;
  $('skipBtn').textContent = left === 1 ? 'Não sei, encerrar e ver resposta →' : 'Não sei, revelar próxima pista →';
  $('skipNote').textContent = left === 1 ? 'Este passe encerra sua rodada de hoje.' : 'Revelar uma pista usa uma chance.';
  $('playArea').hidden = game.done; $('result').hidden = !game.done;
  $('bannerText').textContent = game.done ? 'O mistério de hoje foi revelado.' : game.moves.length ? 'Mais uma pista. Mais perto do gol.' : 'A primeira pista já está em campo.';
  $('attemptDots').replaceChildren(...Array.from({length:5}, (_, i) => {const dot=document.createElement('i'); dot.className=game.moves[i]?.result || ''; return dot;}));
  $('attemptDots').setAttribute('aria-label', `${game.moves.length} de 5 chances usadas`);
  $('historyArea').hidden = !game.moves.length;
  $('history').replaceChildren(...game.moves.map(m => {const li=document.createElement('li'); li.className=m.result; li.textContent=`${m.result === 'wrong' ? '×' : m.result === 'correct' ? '✓' : '→'} ${m.name}`; return li;}));
  $('played').textContent = game.stats.played;
  $('wins').textContent = (game.stats.played ? Math.round(game.stats.wins / game.stats.played * 100) : 0) + '%';
  $('streak').textContent = game.stats.streak;
  $('catalogCount').textContent = game.totalPlayers;
  if (game.done) {
    $('result').classList.toggle('lost', !game.won);
    $('resultTitle').textContent = game.won ? 'É gol! Você conhece a bola.' : 'Hoje bateu na trave.';
    $('resultText').textContent = `${game.answer}. ${game.won ? `Você acertou em ${game.moves.length} de 5 chances!` : 'Amanhã tem outra chance de brilhar.'}`;
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
    if (!response.ok) throw new Error(data.error || 'O jogo não respondeu corretamente.');
    accept(data); $('retryBtn').hidden = true; feedback();
  } catch (error) {
    feedback(error.message === 'Failed to fetch' ? 'Não conseguimos acessar o servidor do jogo. Tente novamente.' : error.message);
    $('retryBtn').hidden = false; $('game').setAttribute('aria-busy', 'false');
  } finally { loading = false; }
}
function choose(index) {
  if (!results[index]) return;
  selected = results[index]; input.value = selected.name; closeSearch(); controls(); feedback('Jogador selecionado. Toque em Chutar para confirmar.'); input.focus();
}
function highlight(index) {
  active = index;
  [...$('suggestions').children].forEach((el, i) => el.setAttribute('aria-selected', String(i === active)));
  input.setAttribute('aria-activedescendant', `player-option-${index}`);
  $('suggestions').children[index]?.scrollIntoView({block:'nearest'});
}
input.addEventListener('input', () => {
  selected = null; results = []; controls(); closeSearch(); feedback();
  $('clearBtn').hidden = !input.value;
  clearTimeout(queryTimer); searchController?.abort();
  const query = input.value.trim();
  if (!query) return;
  queryTimer = setTimeout(async () => {
    const controller = new AbortController(); searchController = controller;
    try {
      const response = await fetch('/api/players?q=' + encodeURIComponent(query), {signal:controller.signal});
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (input.value.trim() !== query || controller.signal.aborted) return;
      results = data.filter(p => !game.moves.some(m => m.id === p.id));
      $('suggestions').replaceChildren(...results.map((p, i) => {
        const li=document.createElement('li'); li.id=`player-option-${i}`; li.setAttribute('role','option'); li.setAttribute('aria-selected','false'); li.textContent=p.name;
        li.addEventListener('pointerdown', e=>e.preventDefault()); li.addEventListener('click', ()=>choose(i)); return li;
      }));
      $('suggestions').hidden = !results.length; input.setAttribute('aria-expanded', String(!!results.length));
      feedback(results.length ? `${results.length} jogadores encontrados. Selecione um nome.` : 'Nenhum jogador encontrado. Tente outro nome do catálogo.');
    } catch (error) { if (error.name !== 'AbortError') feedback('A busca falhou. Digite novamente para tentar.'); }
  }, 180);
});
input.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeSearch();
  if (!$('suggestions').hidden && results.length) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); highlight((active + (e.key === 'ArrowDown' ? 1 : -1) + results.length) % results.length); }
    if (e.key === 'Enter') { e.preventDefault(); if (active >= 0) choose(active); else if (results.length === 1) choose(0); else feedback('Selecione um nome da lista para confirmar.'); }
  }
});
input.addEventListener('blur', closeSearch);
$('clearBtn').onclick = () => {resetSearch(); controls(); feedback(); input.focus();};
async function submit(playerId) {
  if (busy || !game || game.done) return;
  busy = true; controls(); feedback(); closeSearch();
  try {
    const response = await fetch('/api/guess', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({day:game.day, version:game.version, playerId})});
    const data = await response.json();
    if (!response.ok) { if(data.game) accept(data.game); feedback(data.error || 'Não foi possível registrar o palpite.'); return; }
    resetSearch(); accept(data); channel?.postMessage('updated');
    feedback(game.done ? '' : playerId === null ? 'Nova pista revelada.' : 'Não foi dessa vez. Uma nova pista foi revelada.');
    if(game.done) { $('resultTitle').tabIndex=-1; $('resultTitle').focus({preventScroll:true}); }
  } catch { feedback('Conexão interrompida. Seu lance pode ter sido salvo. Tente novamente para sincronizar.'); $('retryBtn').hidden=false; }
  finally {busy=false; controls();}
}
$('guessForm').onsubmit = e => {e.preventDefault(); if(selected) submit(selected.id); else feedback('Selecione um jogador da lista.');};
$('skipBtn').onclick = () => submit(null);
$('retryBtn').onclick = loadGame;
function tick() {
  if(!game) return;
  const remaining = Math.max(0, Math.ceil((Date.parse(game.nextAt)-Date.now()-serverOffset)/1000));
  const text = [Math.floor(remaining/3600), Math.floor(remaining/60)%60, remaining%60].map(n=>String(n).padStart(2,'0')).join(':');
  document.querySelectorAll('.countdown').forEach(el=>el.textContent=text);
  if (!remaining && Date.now()>nextRefresh) {nextRefresh=Date.now()+10000; loadGame();}
}
function squares() {return Array.from({length:5},(_,i)=>marks[game.moves[i]?.result] || '⬜').join('');}
function shareText() {return `GolGuess #${String(game.number).padStart(3,'0')} ⚽ ${game.won ? game.moves.length : 'X'}/5\n${squares()}\nVocê conhece esse craque?\n${location.origin}/`;}
function shareFallback(text) {$('shareText').value=text; $('copyBtn').textContent='Copiar resultado'; $('shareDialog').showModal(); $('shareText').select();}
$('shareBtn').onclick = async () => {
  if(!game?.done) return;
  const text=shareText();
  try {
    if(navigator.share) {await navigator.share({text}); return;}
    await navigator.clipboard.writeText(text); $('shareBtn').textContent='Resultado copiado ✓';
  } catch(error) {if(error.name !== 'AbortError') shareFallback(text);}
};
$('copyBtn').onclick=async()=>{try{await navigator.clipboard.writeText($('shareText').value); $('copyBtn').textContent='Copiado ✓';}catch{$('shareText').focus();$('shareText').select();$('copyBtn').textContent='Selecione e copie o texto acima';}};
for(const name of ['help','stats','privacy','sources']) $(name+'Btn').onclick=()=>$(name+'Dialog').showModal();
document.querySelectorAll('dialog').forEach(dialog=>{
  dialog.querySelector('.dialog-close').onclick=()=>dialog.close();
  dialog.querySelector('.dialog-done')?.addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
});
channel?.addEventListener('message', loadGame);
document.addEventListener('visibilitychange',()=>{if(!document.hidden) loadGame();});
window.addEventListener('focus', loadGame);
setInterval(tick,1000);
loadGame();
