'use strict';
const byId = id => document.getElementById(id);
let nextAt = 0;
let day = '';
let serverOffset = 0;

function status(message, error = false) {
  if (error) window.golguessAds?.setEligible(false);
  byId('rankingStatus').textContent = message;
  byId('rankingStatus').classList.toggle('error', error);
}

function countryFlagElement(countryCode) {
  const code = typeof countryCode === 'string' ? countryCode.toUpperCase() : 'UN';
  const valid = /^[A-Z]{2}$/.test(code) && code !== 'UN';
  const flag = document.createElement('span');
  flag.className = 'rank-flag';
  flag.setAttribute('role', 'img');
  flag.setAttribute('aria-label', valid ? `País ${code}` : 'País não identificado');
  flag.title = valid ? code : 'País não identificado';
  flag.textContent = valid
    ? String.fromCodePoint(...[...code].map(letter => 127397 + letter.charCodeAt(0)))
    : '🌎';
  return flag;
}

function scoreChanged(data) {
  if (!data.submitted || !data.mine || !data.previewScore) return false;
  return ['players','teams','top10','total'].some(key => data.mine[key] !== data.previewScore[key]);
}

async function syncScore() {
  const response = await fetch('/api/ranking', {method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({sync:true})});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Não foi possível atualizar sua pontuação.');
  return data;
}

function render(data) {
  window.golguessAds?.setEligible(data.entries.length > 0);
  day = data.day;
  nextAt = Date.parse(data.nextAt);
  serverOffset = Date.parse(data.serverTime) - Date.now();
  byId('rankingDay').textContent = new Intl.DateTimeFormat('pt-BR', {day:'2-digit', month:'2-digit', timeZone:'America/Sao_Paulo'}).format(new Date(`${day}T12:00:00-03:00`));
  tick();
  byId('rankingProgress').hidden = false;
  for (const [mode, id, label] of [['players','progressPlayers','Jogadores'],['teams','progressTeams','Times'],['top10','progressTop10','Top 10']]) {
    const done = !!data.completed[mode];
    byId(id).textContent = `${done ? '✓' : '○'} ${label}`;
    byId(id).classList.toggle('done', done);
  }
  byId('rankingForm').hidden = !data.eligible || data.submitted;
  if (data.previewScore) byId('previewScore').textContent = data.previewScore.total;
  byId('myRank').hidden = !data.mine;
  if (data.mine) {
    byId('myRank').replaceChildren();
    const label = document.createElement('span');
    label.append(document.createTextNode(`Sua posição: #${data.mine.rank} · `),
      countryFlagElement(data.mine.countryCode), document.createTextNode(` ${data.mine.nickname} · `));
    const score = document.createElement('strong');
    score.textContent = `${data.mine.total} pontos`;
    byId('myRank').append(label, score);
  }
  byId('playerCount').textContent = `${data.totalPlayers} ${data.totalPlayers === 1 ? 'participante' : 'participantes'}`;
  const items = data.entries.map(entry => {
    const li = document.createElement('li');
    if (entry.mine) li.className = 'mine';
    const rank = document.createElement('span'); rank.className = 'rank-number'; rank.textContent = `#${entry.rank}`;
    const name = document.createElement('span'); name.className = 'rank-name';
    name.append(countryFlagElement(entry.countryCode), document.createTextNode(entry.nickname));
    const detail = document.createElement('small'); detail.textContent = `Jogadores ${entry.players} · Times ${entry.teams} · Top 10 ${entry.top10}`;
    name.append(detail);
    const points = document.createElement('strong'); points.className = 'rank-score'; points.textContent = entry.total;
    li.append(rank, name, points);
    return li;
  });
  byId('rankingList').replaceChildren(...items);
  byId('rankingEmpty').hidden = data.entries.length > 0;
  const completedCount = Object.values(data.completed).filter(Boolean).length;
  status(data.submitted
    ? `Você está no ranking · ${completedCount}/3 desafios concluídos.`
    : data.eligible ? 'Seu primeiro resultado já vale pontos. Escolha um nickname.'
    : 'Conclua um desafio para participar.');
}

async function load() {
  window.golguessAds?.setEligible(false);
  try {
    const response = await fetch('/api/ranking', {cache:'no-store'});
    let data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível carregar o ranking.');
    if (scoreChanged(data)) data = await syncScore();
    render(data);
  } catch (error) { status(error.message || 'Não foi possível carregar o ranking.', true); }
}

function tick() {
  if (!nextAt) return;
  const left = Math.max(0, Math.ceil((nextAt - Date.now() - serverOffset) / 1000));
  byId('rankingCountdown').textContent = [Math.floor(left/3600), Math.floor(left/60)%60, left%60].map(n => String(n).padStart(2,'0')).join(':');
  if (!left && day) { day = ''; load(); }
}

byId('rankingForm').addEventListener('submit', async event => {
  event.preventDefault();
  const button = byId('rankingForm').querySelector('button');
  button.disabled = true;
  try {
    const response = await fetch('/api/ranking', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({nickname:byId('rankingNickname').value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível entrar no ranking.');
    render(data);
  } catch (error) { status(error.message || 'Não foi possível entrar no ranking.', true); }
  finally { button.disabled = false; }
});

setInterval(tick, 1000);
load();
