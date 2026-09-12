"""Anonymous, server-owned daily rounds. Run: python server.py."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import unicodedata
from datetime import date, datetime, time, timedelta, timezone
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from storage import connect, database_url, StorageUnavailable

ROOT = Path(__file__).resolve().parent
BRASILIA = timezone(timedelta(hours=-3))
EPOCH = date(2026, 9, 11)
PLAYERS = json.loads((ROOT / 'data/players.json').read_text(encoding='utf-8'))
BY_ID = {p['id']: p for p in PLAYERS}
SCHEDULE = sorted(PLAYERS, key=lambda p: hashlib.sha256(('golguess-career-v1:' + p['id']).encode()).digest())

TEAMS = json.loads((ROOT / 'data/teams.json').read_text(encoding='utf-8'))
TEAMS_BY_ID = {t['id']: t for t in TEAMS}
TEAMS_SCHEDULE = sorted(TEAMS, key=lambda t: hashlib.sha256(('golguess-teams-v1:' + t['id']).encode()).digest())

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(c))

def today():
    return datetime.now(BRASILIA).date()

def answer(day):
    return SCHEDULE[(day - EPOCH).days % len(SCHEDULE)]

def team_answer(day):
    return TEAMS_SCHEDULE[(day - EPOCH).days % len(TEAMS_SCHEDULE)]

def cookie_mode():
    return os.environ.get('GOLGUESS_COOKIE_MODE') == '1' or (bool(os.environ.get('VERCEL')) and not database_url())

def signing_key():
    configured = os.environ.get('GOLGUESS_SECRET') or os.environ.get('VERCEL_PROJECT_ID')
    return (configured or 'golguess-browser-round-v1').encode()

def encode_state(state):
    payload = base64.urlsafe_b64encode(json.dumps(state, separators=(',', ':'), ensure_ascii=False).encode()).decode().rstrip('=')
    signature = hmac.new(signing_key(), payload.encode(), hashlib.sha256).hexdigest()
    return f'{payload}.{signature}'

def decode_state(value, mode='players'):
    try:
        payload, signature = value.rsplit('.', 1)
        expected = hmac.new(signing_key(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        raw = base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4))
        state = json.loads(raw)
        if not isinstance(state, dict) or state.get('v') != 1 or not isinstance(state.get('day'), str):
            return None
        if any(not isinstance(state.get(key), int) or state[key] < 0 for key in ('played', 'wins', 'streak')):
            return None
        if state['wins'] > state['played']:
            return None
        if state.get('lastWin') is not None:
            date.fromisoformat(state['lastWin'])
        moves = state.get('moves')
        if not isinstance(moves, list) or len(moves) > 5:
            return None
        catalog_by_id = TEAMS_BY_ID if mode == 'teams' else BY_ID
        for move in moves:
            if not isinstance(move, dict) or move.get('result') not in {'correct', 'wrong', 'skip'}:
                return None
            item_id = move.get('id')
            if (item_id is None) != (move['result'] == 'skip') or (item_id is not None and item_id not in catalog_by_id):
                return None
            if not isinstance(move.get('name'), str) or len(move['name']) > 120:
                return None
        return state
    except (AttributeError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
        return None

def initialize():
    with connect() as db:
        db.execute('SELECT 1')

def read_moves(db, visitor, day, mode='players'):
    table = 'team_rounds' if mode == 'teams' else 'career_rounds'
    row = db.execute(f'SELECT moves FROM {table} WHERE visitor=? AND day=?', (visitor, str(day))).fetchone()
    return json.loads(row['moves']) if row else []

def finished(moves):
    return len(moves) >= 5 or any(m['result'] == 'correct' for m in moves)

def stats(db, visitor, day, mode='players'):
    table = 'team_rounds' if mode == 'teams' else 'career_rounds'
    rows = db.execute(f'SELECT day, moves FROM {table} WHERE visitor=? AND day<=? ORDER BY day DESC', (visitor, str(day))).fetchall()
    complete = [(date.fromisoformat(r['day']), json.loads(r['moves'])) for r in rows if finished(json.loads(r['moves']))]
    wins = sum(any(x['result'] == 'correct' for x in m) for _, m in complete)
    expected = day if complete and complete[0][0] == day else day - timedelta(days=1)
    streak = 0
    for d, m in complete:
        if d != expected or not any(x['result'] == 'correct' for x in m):
            break
        streak += 1
        expected -= timedelta(days=1)
    return dict(played=len(complete), wins=wins, streak=streak)

def make_snapshot(moves, player_stats, day):
    player = answer(day)
    done = finished(moves)
    birth = date.fromisoformat(player['birth'])
    age = day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))
    cards = f"{player['yellow']} amarelo{'s' if player['yellow'] != 1 else ''}"
    if player['red']:
        cards += f" · {player['red']} vermelho{'s' if player['red'] != 1 else ''}"
    clues = [dict(key='leagueSeason', label='Liga e temporada', value=f"{player['league']} · {player['season']}",
                  league=player['league'], season=player['season']),
             dict(key='goalsAssists', label='Gols e assistências',
                  value=f"{player['goals']} gols · {player['assists']} assistências",
                  goals=player['goals'], assists=player['assists']),
             dict(key='cards', label='Cartões', value=cards, yellow=player['yellow'], red=player['red']),
             dict(key='age', label='Idade atual', value=f'{age} anos', age=age),
             dict(key='team', label='Time', value=player['team'], team=player['team'])]
    return dict(mode='players', day=str(day), number=(day-EPOCH).days+1, totalPlayers=len(PLAYERS),
                serverTime=datetime.now(BRASILIA).isoformat(),
                nextAt=datetime.combine(day+timedelta(days=1), time(), BRASILIA).isoformat(),
                moves=moves, version=len(moves), done=done,
                won=any(m['result']=='correct' for m in moves),
                clues=clues[:5 if done else min(len(moves)+1, 5)],
                answer=player['name'] if done else None, stats=player_stats, catalog='career-v1')

def make_team_snapshot(moves, team_stats, day):
    team = team_answer(day)
    done = finished(moves)
    titles_count = team['titles']
    titles_str = f"{titles_count} título{'s' if titles_count != 1 else ''}"
    clues = [
        dict(key='continent', label='Continente', value=team['continent'], continent=team['continent']),
        dict(key='titles', label='Títulos de liga', value=titles_str, titles=titles_count),
        dict(key='country', label='País', value=team['country'], country=team['country']),
        dict(key='colors', label='Cores', value=team['colors'], colors=team['colors']),
        dict(key='city', label='Cidade', value=team['city'], city=team['city']),
    ]
    return dict(mode='teams', day=str(day), number=(day-EPOCH).days+1, totalTeams=len(TEAMS),
                serverTime=datetime.now(BRASILIA).isoformat(),
                nextAt=datetime.combine(day+timedelta(days=1), time(), BRASILIA).isoformat(),
                moves=moves, version=len(moves), done=done,
                won=any(m['result']=='correct' for m in moves),
                clues=clues[:5 if done else min(len(moves)+1, 5)],
                answer=team['name'] if done else None, stats=team_stats, catalog='teams-v1')

def snapshot(db, visitor, day, mode='players'):
    if mode == 'teams':
        return make_team_snapshot(read_moves(db, visitor, day, 'teams'), stats(db, visitor, day, 'teams'), day)
    return make_snapshot(read_moves(db, visitor, day, 'players'), stats(db, visitor, day, 'players'), day)

class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, content_type='application/json; charset=utf-8', cookie=None, state_cookie=None, state_cookie_teams=None):
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        if os.environ.get('GOLGUESS_ALLOW_FRAME') != '1' and os.environ.get('HOST') != '0.0.0.0':
            self.send_header('X-Frame-Options', 'DENY')
        if cookie:
            secure = '; Secure' if os.environ.get('VERCEL') or os.environ.get('GOLGUESS_SECURE_COOKIE') == '1' else ''
            self.send_header('Set-Cookie', f'gg_visitor={cookie}; HttpOnly; SameSite=Lax; Path=/; Max-Age=34560000{secure}')
        if state_cookie:
            secure = '; Secure' if os.environ.get('VERCEL') or os.environ.get('GOLGUESS_SECURE_COOKIE') == '1' else ''
            self.send_header('Set-Cookie', f'gg_state={state_cookie}; HttpOnly; SameSite=Lax; Path=/; Max-Age=34560000{secure}')
        if state_cookie_teams:
            secure = '; Secure' if os.environ.get('VERCEL') or os.environ.get('GOLGUESS_SECURE_COOKIE') == '1' else ''
            self.send_header('Set-Cookie', f'gg_state_teams={state_cookie_teams}; HttpOnly; SameSite=Lax; Path=/; Max-Age=34560000{secure}')
        self.end_headers()
        self.wfile.write(raw)

    def visitor(self, db, create=False):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get('Cookie', ''))
        except CookieError:
            pass
        token = cookies.get('gg_visitor')
        token = token.value if token else ''
        if token and db.execute('SELECT 1 FROM visitors WHERE id=?', (token,)).fetchone():
            return token, None
        if not create:
            return None, None
        token = secrets.token_urlsafe(32)
        db.execute('INSERT INTO visitors VALUES (?)', (token,))
        return token, token

    def browser_state(self, day, mode='players'):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get('Cookie', ''))
        except CookieError:
            pass
        cookie_name = 'gg_state_teams' if mode == 'teams' else 'gg_state'
        item = cookies.get(cookie_name)
        state = decode_state(item.value, mode=mode) if item else None
        if not state:
            state = {'v': 1, 'day': str(day), 'moves': [], 'played': 0, 'wins': 0, 'streak': 0, 'lastWin': None}
        if state.get('day') != str(day):
            state['day'], state['moves'] = str(day), []
        return state

    def browser_snapshot(self, state, day, mode='players'):
        s = {'played': state['played'], 'wins': state['wins'], 'streak': state['streak']}
        if mode == 'teams':
            return make_team_snapshot(state['moves'], s, day)
        return make_snapshot(state['moves'], s, day)

    def do_GET(self):
        try:
            self.get()
        except StorageUnavailable as exc:
            self.send(503, {'error': 'O jogo está em manutenção. Tente novamente em instantes.', 'code': exc.code})

    def get(self):
        url = urlsplit(self.path)
        if url.path == '/api/health':
            if cookie_mode():
                return self.send(200, {'status': 'ok', 'catalog': 'career-v1', 'players': len(PLAYERS),
                                       'teams': len(TEAMS), 'storage': 'signed-cookie'})
            with connect() as db:
                db.execute('SELECT 1')
            return self.send(200, {'status': 'ok', 'catalog': 'career-v1', 'players': len(PLAYERS),
                                   'teams': len(TEAMS), 'storage': 'postgres' if database_url() else 'sqlite'})
        if url.path == '/api/game':
            mode = parse_qs(url.query).get('mode', ['players'])[0].lower()
            if mode not in ('players', 'teams'):
                mode = 'players'
            if cookie_mode():
                day = today()
                state = self.browser_state(day, mode=mode)
                encoded = encode_state(state)
                if mode == 'teams':
                    return self.send(200, self.browser_snapshot(state, day, mode='teams'), state_cookie_teams=encoded)
                return self.send(200, self.browser_snapshot(state, day, mode='players'), state_cookie=encoded)
            with connect() as db:
                visitor, cookie = self.visitor(db, create=True)
                payload = snapshot(db, visitor, today(), mode=mode)
            return self.send(200, payload, cookie=cookie)
        if url.path == '/api/players':
            query = normalize(parse_qs(url.query).get('q', [''])[0].strip())[:80]
            result = [dict(id=p['id'], name=p['name']) for p in PLAYERS if query and query in normalize(p['name'])]
            result.sort(key=lambda p: (not normalize(p['name']).startswith(query), p['name']))
            return self.send(200, result[:8])
        if url.path in ('/api/teams', '/api/clubs'):
            query = normalize(parse_qs(url.query).get('q', [''])[0].strip())[:80]
            result = [dict(id=t['id'], name=t['name'], league=t['league'], country=t['country'])
                      for t in TEAMS if query and query in normalize(f"{t['name']} {t['league']} {t['city']}")]
            result.sort(key=lambda t: (not normalize(t['name']).startswith(query), t['name']))
            return self.send(200, result[:8])
        files = {'/': ('index.html', 'text/html; charset=utf-8'),
                 '/index.html': ('index.html', 'text/html; charset=utf-8'),
                 '/styles.css': ('styles.css', 'text/css; charset=utf-8'),
                 '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                 '/ads.txt': ('ads.txt', 'text/plain; charset=utf-8'),
                 '/robots.txt': ('robots.txt', 'text/plain; charset=utf-8'),
                 '/sitemap.xml': ('sitemap.xml', 'application/xml; charset=utf-8'),
                 '/data/ATTRIBUTION.md': ('data/ATTRIBUTION.md', 'text/plain; charset=utf-8')}
        if url.path not in files:
            return self.send(404, {'error': 'Página não encontrada.'})
        file, content_type = files[url.path]
        self.send(200, (ROOT / file).read_bytes(), content_type)

    def do_POST(self):
        try:
            self.post()
        except StorageUnavailable as exc:
            self.send(503, {'error': 'Não foi possível salvar o lance. Tente novamente em instantes.', 'code': exc.code})

    def post(self):
        if self.path != '/api/guess':
            return self.send(404, {'error': 'Rota não encontrada.'})
        origin = self.headers.get('Origin')
        if (origin and urlsplit(origin).netloc != self.headers.get('Host')) or self.headers.get('Content-Type') != 'application/json':
            return self.send(403, {'error': 'Origem não permitida.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024:
                raise ValueError()
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError()
            if 'playerId' not in body and 'teamId' not in body and 'guessId' not in body:
                raise ValueError()
        except (ValueError, UnicodeError):
            return self.send(400, {'error': 'Palpite inválido.'})
        mode = body.get('mode')
        if not mode:
            mode = 'teams' if 'teamId' in body else 'players'
        if mode not in ('players', 'teams'):
            mode = 'players'
        if cookie_mode():
            return self.post_browser(body, mode=mode)
        with connect() as db:
            if not db.postgres:
                db.execute('BEGIN IMMEDIATE')
            visitor, _ = self.visitor(db)
            if not visitor:
                return self.send(403, {'error': 'Permita cookies essenciais e recarregue para jogar.'})
            db.lock_visitor(visitor)
            day = today()
            moves = read_moves(db, visitor, day, mode=mode)
            if body.get('day') != str(day) or body.get('version') != len(moves) or finished(moves):
                return self.send(409, {'error': 'A rodada foi atualizada. Confira as pistas.', 'game': snapshot(db, visitor, day, mode=mode)})
            guess_id = body.get('teamId' if mode == 'teams' else 'playerId')
            if guess_id is None and 'guessId' in body:
                guess_id = body.get('guessId')
            if guess_id is None and mode == 'teams' and 'playerId' in body:
                guess_id = body.get('playerId')
            catalog_by_id = TEAMS_BY_ID if mode == 'teams' else BY_ID
            catalog_name = 'time' if mode == 'teams' else 'jogador'
            if guess_id is not None and (not isinstance(guess_id, str) or guess_id not in catalog_by_id):
                return self.send(400, {'error': f'Escolha um {catalog_name} da lista.'})
            if guess_id and any(m['id'] == guess_id for m in moves):
                return self.send(400, {'error': f'Você já tentou esse {catalog_name}. Escolha outro.'})
            correct_id = team_answer(day)['id'] if mode == 'teams' else answer(day)['id']
            result = 'skip' if guess_id is None else 'correct' if guess_id == correct_id else 'wrong'
            moves.append(dict(id=guess_id, name=catalog_by_id[guess_id]['name'] if guess_id else 'Pista revelada', result=result))
            table = 'team_rounds' if mode == 'teams' else 'career_rounds'
            db.execute(f'INSERT INTO {table} VALUES (?, ?, ?) ON CONFLICT(visitor, day) DO UPDATE SET moves=excluded.moves',
                       (visitor, str(day), json.dumps(moves)))
            payload = snapshot(db, visitor, day, mode=mode)
        self.send(200, payload)

    def post_browser(self, body, mode='players'):
        day = today()
        state = self.browser_state(day, mode=mode)
        moves = state['moves']
        if body.get('day') != str(day) or body.get('version') != len(moves) or finished(moves):
            snap = self.browser_snapshot(state, day, mode=mode)
            enc = encode_state(state)
            if mode == 'teams':
                return self.send(409, {'error': 'A rodada foi atualizada. Confira as pistas.', 'game': snap}, state_cookie_teams=enc)
            return self.send(409, {'error': 'A rodada foi atualizada. Confira as pistas.', 'game': snap}, state_cookie=enc)
        guess_id = body.get('teamId' if mode == 'teams' else 'playerId')
        if guess_id is None and 'guessId' in body:
            guess_id = body.get('guessId')
        if guess_id is None and mode == 'teams' and 'playerId' in body:
            guess_id = body.get('playerId')
        catalog_by_id = TEAMS_BY_ID if mode == 'teams' else BY_ID
        catalog_name = 'time' if mode == 'teams' else 'jogador'
        if guess_id is not None and (not isinstance(guess_id, str) or guess_id not in catalog_by_id):
            return self.send(400, {'error': f'Escolha um {catalog_name} da lista.'})
        if guess_id and any(move['id'] == guess_id for move in moves):
            return self.send(400, {'error': f'Você já tentou esse {catalog_name}. Escolha outro.'})
        correct_id = team_answer(day)['id'] if mode == 'teams' else answer(day)['id']
        result = 'skip' if guess_id is None else 'correct' if guess_id == correct_id else 'wrong'
        moves.append({'id': guess_id, 'name': catalog_by_id[guess_id]['name'] if guess_id else 'Pista revelada', 'result': result})
        if finished(moves):
            state['played'] += 1
            if result == 'correct':
                state['wins'] += 1
                yesterday = str(day - timedelta(days=1))
                state['streak'] = state['streak'] + 1 if state.get('lastWin') == yesterday else 1
                state['lastWin'] = str(day)
            else:
                state['streak'] = 0
        snap = self.browser_snapshot(state, day, mode=mode)
        enc = encode_state(state)
        if mode == 'teams':
            return self.send(200, snap, state_cookie_teams=enc)
        return self.send(200, snap, state_cookie=enc)

if __name__ == '__main__':
    initialize()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))
    print(f'GolGuess em http://{host}:{port}', flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
