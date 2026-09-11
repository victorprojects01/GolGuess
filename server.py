"""Anonymous, server-owned daily rounds. Run: python server.py."""
import hashlib
import json
import os
import secrets
import unicodedata
from datetime import date, datetime, time, timedelta, timezone
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from storage import connect, StorageUnavailable

ROOT = Path(__file__).resolve().parent
BRASILIA = timezone(timedelta(hours=-3))
EPOCH = date(2026, 9, 11)
PLAYERS = json.loads((ROOT / 'data/players.json').read_text(encoding='utf-8'))
BY_ID = {p['id']: p for p in PLAYERS}
SCHEDULE = sorted(PLAYERS, key=lambda p: hashlib.sha256(('golguess-v1:' + p['id']).encode()).digest())

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(c))

def today():
    return datetime.now(BRASILIA).date()

def answer(day):
    return SCHEDULE[(day - EPOCH).days % len(SCHEDULE)]

def initialize():
    with connect() as db:
        db.execute('SELECT 1')

def read_moves(db, visitor, day):
    row = db.execute('SELECT moves FROM career_rounds WHERE visitor=? AND day=?', (visitor, str(day))).fetchone()
    return json.loads(row['moves']) if row else []

def finished(moves):
    return len(moves) >= 5 or any(m['result'] == 'correct' for m in moves)

def stats(db, visitor, day):
    rows = db.execute('SELECT day, moves FROM career_rounds WHERE visitor=? AND day<=? ORDER BY day DESC', (visitor, str(day))).fetchall()
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

def snapshot(db, visitor, day):
    moves = read_moves(db, visitor, day)
    player = answer(day)
    done = finished(moves)
    birth = date.fromisoformat(player['birth'])
    age = 2022 - birth.year - ((11, 20) < (birth.month, birth.day))
    clues = [dict(label='Seleção', value=player['country']),
             dict(label='Posição', value=player['position']),
             dict(label='Idade na Copa', value=f'{age} anos'),
             dict(label='Camisa na Copa', value=f"Nº {player['shirt']}"),
             dict(label='Iniciais do nome', value=' · '.join(w[0].upper() for w in player['name'].split()))]
    return dict(day=str(day), number=(day-EPOCH).days+1, totalPlayers=len(PLAYERS),
                serverTime=datetime.now(BRASILIA).isoformat(),
                nextAt=datetime.combine(day+timedelta(days=1), time(), BRASILIA).isoformat(),
                moves=moves, version=len(moves), done=done,
                won=any(m['result']=='correct' for m in moves),
                clues=clues[:5 if done else min(len(moves)+1, 5)],
                answer=player['name'] if done else None, stats=stats(db, visitor, day))

class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, content_type='application/json; charset=utf-8', cookie=None):
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('X-Frame-Options', 'DENY')
        if cookie:
            secure = '; Secure' if os.environ.get('VERCEL') or os.environ.get('GOLGUESS_SECURE_COOKIE') == '1' else ''
            self.send_header('Set-Cookie', f'gg_visitor={cookie}; HttpOnly; SameSite=Lax; Path=/; Max-Age=34560000{secure}')
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

    def do_GET(self):
        try:
            self.get()
        except StorageUnavailable as exc:
            self.send(503, {'error': 'O jogo está em manutenção. Tente novamente em instantes.', 'code': exc.code})

    def get(self):
        url = urlsplit(self.path)
        if url.path == '/api/health':
            with connect() as db:
                db.execute('SELECT 1')
            return self.send(200, {'status': 'ok', 'catalog': 'career-v1', 'players': len(PLAYERS)})
        if url.path == '/api/game':
            with connect() as db:
                visitor, cookie = self.visitor(db, create=True)
                payload = snapshot(db, visitor, today())
            return self.send(200, payload, cookie=cookie)
        if url.path == '/api/players':
            query = normalize(parse_qs(url.query).get('q', [''])[0].strip())[:80]
            result = [dict(id=p['id'], name=p['name']) for p in PLAYERS if query and query in normalize(p['name'])]
            result.sort(key=lambda p: (not normalize(p['name']).startswith(query), p['name']))
            return self.send(200, result[:8])
        files = {'/': ('index.html', 'text/html; charset=utf-8'),
                 '/index.html': ('index.html', 'text/html; charset=utf-8'),
                 '/styles.css': ('styles.css', 'text/css; charset=utf-8'),
                 '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
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
            if not isinstance(body, dict) or 'playerId' not in body:
                raise ValueError()
        except (ValueError, UnicodeError):
            return self.send(400, {'error': 'Palpite inválido.'})
        with connect() as db:
            if not db.postgres:
                db.execute('BEGIN IMMEDIATE')
            visitor, _ = self.visitor(db)
            if not visitor:
                return self.send(403, {'error': 'Permita cookies essenciais e recarregue para jogar.'})
            db.lock_visitor(visitor)
            day = today()
            moves = read_moves(db, visitor, day)
            if body.get('day') != str(day) or body.get('version') != len(moves) or finished(moves):
                return self.send(409, {'error': 'A rodada foi atualizada. Confira as pistas.', 'game': snapshot(db, visitor, day)})
            player_id = body.get('playerId')
            if player_id is not None and (not isinstance(player_id, str) or player_id not in BY_ID):
                return self.send(400, {'error': 'Escolha um jogador da lista.'})
            if player_id and any(m['id'] == player_id for m in moves):
                return self.send(400, {'error': 'Você já tentou esse jogador. Escolha outro.'})
            result = 'skip' if player_id is None else 'correct' if player_id == answer(day)['id'] else 'wrong'
            moves.append(dict(id=player_id, name=BY_ID[player_id]['name'] if player_id else 'Pista revelada', result=result))
            db.execute('INSERT INTO career_rounds VALUES (?, ?, ?) ON CONFLICT(visitor, day) DO UPDATE SET moves=excluded.moves',
                       (visitor, str(day), json.dumps(moves)))
            payload = snapshot(db, visitor, day)
        self.send(200, payload)

if __name__ == '__main__':
    initialize()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))
    print(f'GolGuess em http://{host}:{port}', flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
