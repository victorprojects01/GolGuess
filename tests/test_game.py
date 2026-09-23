import concurrent.futures
import hashlib
import http.client
import hmac
import json
import tempfile
import threading
import unittest
import os
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import server
import storage
import supabase_ranking
from scripts.player_metadata import position_code


class DailyGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_db = storage.DB_PATH
        storage.DB_PATH = Path(cls.temp.name) / 'test.sqlite3'
        storage._initialized.clear()
        server.initialize()
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        storage.DB_PATH = cls.old_db
        storage._initialized.clear()
        cls.temp.cleanup()

    def request(self, path='/api/game', body=None, cookie=None, origin=None, extra_headers=None):
        conn = http.client.HTTPConnection(*self.http.server_address)
        headers = {'Content-Type': 'application/json'}
        if cookie:
            headers['Cookie'] = cookie
        if origin:
            headers['Origin'] = origin
        if extra_headers:
            headers.update(extra_headers)
        conn.request('POST' if body is not None else 'GET', path,
                     json.dumps(body) if body is not None else None, headers)
        response = conn.getresponse()
        content = response.read()
        status, new_cookie = response.status, response.getheader('Set-Cookie')
        conn.close()
        return status, json.loads(content), new_cookie

    def start(self):
        status, game, cookie = self.request()
        self.assertEqual(status, 200)
        self.assertIn('HttpOnly', cookie)
        return game, cookie.split(';')[0]

    def move(self, game, cookie, player_id=None):
        return self.request('/api/guess', dict(day=game['day'], version=game['version'], playerId=player_id), cookie)

    def test_catalog_and_schedule(self):
        self.assertGreaterEqual(len(server.BY_ID), 365)
        self.assertEqual(len({p['name'] for p in server.PLAYERS}), len(server.PLAYERS))
        ids = [server.answer(server.EPOCH + timedelta(days=i))['id'] for i in range(len(server.PLAYERS))]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(ids[0], server.answer(server.EPOCH + timedelta(days=len(ids)))['id'])
        self.assertEqual({p['league'] for p in server.PLAYERS}, {
            'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
            'Campeonato Brasileiro - Série A', 'Liga Profesional'})
        for name in ['Rogério Ceni', 'Raheem Sterling', 'Samuel Umtiti', 'Antonio Di Natale',
                     'Steven Gerrard', 'Jadon Sancho', 'Harry Kane', 'Lionel Messi',
                     'Alexandre Pato', 'Oscar', 'Mesut Özil']:
            self.assertIn(name, {p['name'] for p in server.PLAYERS})
        required = {'id','name','birth','position','nationality','nationalityCode',
                    'league','season','goals','assists','yellow','red','team','matches','source'}
        self.assertEqual({p['position'] for p in server.PLAYERS}, {'ATA','MEI','ZAG','LAT','GOL'})
        for p in server.PLAYERS:
            self.assertEqual(set(p), required)
            self.assertTrue(all(p[k] for k in ['id','name','birth','position','nationality','nationalityCode',
                                               'league','season','team','matches','source']))
            self.assertIn(p['position'], {'ATA','MEI','ZAG','LAT','GOL'})
            self.assertTrue(all(isinstance(p[k], int) and p[k] >= 0 for k in ['goals','assists','yellow','red']))
            server.date.fromisoformat(p['birth'])
        supplements = json.loads((Path(server.ROOT) / 'data/legacy_players.json').read_text(encoding='utf-8'))
        self.assertEqual(len(supplements), 4)
        self.assertTrue(all(p['position'] and p['nationality'] and p['nationalityCode'] for p in supplements))

    def test_position_mapping_keeps_goalkeepers_and_full_backs_distinct(self):
        self.assertEqual(position_code('Goalkeeper', 'Goalkeeper'), 'GOL')
        self.assertEqual(position_code('Defender', 'Centre-Back'), 'ZAG')
        self.assertEqual(position_code('Defender', 'Right-Back'), 'LAT')
        self.assertEqual(position_code('Attack', 'Right Winger'), 'ATA')

    def test_clues_have_requested_order_and_current_age(self):
        game, cookie = self.start()
        for expected_count in (2, 3, 4, 5, 6):
            _, game, _ = self.move(game, cookie)
            self.assertEqual(len(game['clues']), expected_count)
            self.assertFalse(game['done'])
        self.assertEqual([c['label'] for c in game['clues']], [
            'Liga e temporada', 'Gols e assistências', 'Posição', 'Idade atual',
            'Nacionalidade', 'Time da temporada'])
        self.assertEqual([c['key'] for c in game['clues']], [
            'leagueSeason', 'goalsAssists', 'position', 'age', 'nationality', 'team'])
        self.assertTrue(all(key in game['clues'][1] for key in ('goals', 'assists')))
        player = server.answer(server.today())
        self.assertEqual(game['clues'][2]['position'], player['position'])
        self.assertEqual(game['clues'][4]['nationality'], player['nationality'])
        self.assertEqual(game['clues'][4]['nationalityCode'], player['nationalityCode'])
        self.assertEqual(game['clues'][5]['team'], player['team'])
        birth = server.date.fromisoformat(player['birth'])
        expected_age = server.today().year - birth.year - ((server.today().month, server.today().day) < (birth.month, birth.day))
        self.assertEqual(game['clues'][3]['value'], f'{expected_age} anos')

    def test_answer_hidden_and_private_files_blocked(self):
        game, _ = self.start()
        self.assertIsNone(game['answer'])
        self.assertEqual(len(game['clues']), 1)
        for path in ['/data/players.json', '/server.py', '/.runtime/game.sqlite3', '/.git/config', '/../server.py']:
            self.assertEqual(self.request(path)[0], 404)

    def test_institutional_pages_are_linked_and_served(self):
        pages = ('sobre.html', 'como-jogar.html', 'politica-de-privacidade.html',
                 'politica-de-cookies.html', 'termos-de-uso.html', 'contato.html')
        conn = http.client.HTTPConnection(*self.http.server_address)
        conn.request('GET', '/')
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        home = response.read().decode('utf-8')
        conn.close()
        for page in pages:
            self.assertIn(f'href="/{page}"', home)
            conn = http.client.HTTPConnection(*self.http.server_address)
            conn.request('GET', '/' + page)
            response = conn.getresponse()
            self.assertEqual(response.status, 200, page)
            self.assertIn('text/html', response.getheader('Content-Type'))
            content = response.read().decode('utf-8')
            self.assertIn('<h1>', content)
            self.assertIn('href="/"', content)
            conn.close()
        self.assertIn('mailto:torvicbusiness35@gmail.com', content)

    def test_archive_reveals_only_completed_rounds(self):
        current_day = server.EPOCH + timedelta(days=16)
        with patch.object(server, 'today', return_value=current_day):
            conn = http.client.HTTPConnection(*self.http.server_address)
            conn.request('GET', '/arquivo.html')
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn('text/html', response.getheader('Content-Type'))
            archive = response.read().decode('utf-8')
            conn.close()
            self.assertIn(server.answer(current_day - timedelta(days=1))['name'], archive)
            self.assertNotIn(f'<h2>{server.answer(current_day)["name"]}</h2>', archive)
            self.assertIn(server.team_answer(current_day - timedelta(days=1))['name'], archive)
            self.assertIn('arquivo.html?pagina=2', archive)
            self.assertIn('https://www.golguess.com.br/arquivo.html', archive)

            conn = http.client.HTTPConnection(*self.http.server_address)
            conn.request('GET', '/arquivo.html?pagina=2')
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            older = response.read().decode('utf-8')
            conn.close()
            self.assertIn(server.answer(server.EPOCH)['name'], older)
            self.assertNotIn(f'<h2>{server.answer(current_day)["name"]}</h2>', older)

        repeated_day = server.EPOCH + timedelta(days=len(server.TOP10_SCHEDULE))
        first_round_page = (len(server.TOP10_SCHEDULE) - 1) // 14 + 1
        repeated_archive = server.archive_html(repeated_day, first_round_page).decode('utf-8')
        self.assertIn('Este Top 10 está em disputa hoje', repeated_archive)
        self.assertNotIn(server.top10_answer(repeated_day)['title']['pt'], repeated_archive)

    def test_server_rendered_dates_and_archive_at_midnight(self):
        from datetime import date, datetime, timezone
        before = datetime(2026, 9, 23, 2, 59, 59, tzinfo=timezone.utc).astimezone(server.BRASILIA).date()
        after = datetime(2026, 9, 23, 3, 0, 0, tzinfo=timezone.utc).astimezone(server.BRASILIA).date()
        self.assertEqual(before, date(2026, 9, 22))
        self.assertEqual(after, date(2026, 9, 23))
        for day in (before, after):
            with patch.object(server, 'today', return_value=day):
                for path in ('/', '/index.html', '/api/home', '/arquivo.html'):
                    conn = http.client.HTTPConnection(*self.http.server_address)
                    conn.request('GET', path)
                    response = conn.getresponse()
                    document = response.read().decode()
                    self.assertEqual(response.status, 200)
                    self.assertIn('no-store', response.getheader('Cache-Control'))
                    self.assertNotIn('{{', document)
                    yesterday = day - timedelta(days=1)
                    self.assertIn(f'arquivo.html?data={yesterday}', document)
                    conn.close()
                home = server.home_html(day).decode()
                self.assertIn(f'Ontem · {yesterday:%d/%m/%Y}', home)
                self.assertIn(f'Anteontem · {day-timedelta(days=2):%d/%m/%Y}', home)
                self.assertIn(f'#{server.round_info(day)["number"]:03d}', home)
        self.assertIsNone(server.archive_html(before, selected_day=before))
        self.assertIsNotNone(server.archive_html(after, selected_day=before))
        self.assertIsNone(server.archive_html(after, selected_day=after + timedelta(days=1)))
        self.assertIsNone(server.archive_html(after, selected_day=server.EPOCH - timedelta(days=1)))

    def test_archive_detail_has_all_clues_and_original_sources(self):
        from datetime import date
        document = server.archive_html(date(2026,9,23), selected_day=date(2026,9,22)).decode()
        self.assertIn('33 anos', document)
        self.assertIn('Leicester City: registros do clube', document)
        self.assertIn('CF Montréal: história oficial', document)
        for clue in ('Américas', 'Canadá', 'Montreal', 'Azul e preto', 'Títulos de liga'):
            self.assertIn(clue, document)
        self.assertIn('archive-ranking', document)
        self.assertIn('critério adicional', document)
        for offset in range(12):
            entry = server.answer(server.EPOCH + timedelta(days=offset))
            note = server.editorial_note(entry['id'])
            self.assertIn('https://', note, entry['name'])

    def test_merged_recent_cards_share_calendar_and_hide_repeated_answers(self):
        day = server.EPOCH + timedelta(days=12)
        self.assertEqual(server.get_recent_challenges(server.EPOCH), [])
        recent = server.get_recent_challenges(day)
        self.assertEqual([item['number'] for item in recent], [12, 11])
        self.assertEqual([item['dayIso'] for item in recent], ['2026-09-22', '2026-09-21'])
        document = server.home_html(day).decode()
        self.assertEqual(document.count('id="retrospective"'), 1)
        self.assertIn('id="recentGrid"', document)
        self.assertIn(recent[0]['player']['name'], document)
        for schedule, key in ((server.SCHEDULE, 'player'), (server.TEAMS_SCHEDULE, 'team'), (server.TOP10_SCHEDULE, 'top10')):
            repeated = server.EPOCH + timedelta(days=len(schedule))
            rows = server.get_recent_challenges(repeated, limit=len(schedule))
            self.assertIsNone(rows[-1][key])

    def test_merged_head_routes_and_attribution(self):
        for path in ('/', '/arquivo', '/atribuicao.html', '/atribuicao', '/api/recent'):
            conn = http.client.HTTPConnection(*self.http.server_address)
            conn.request('HEAD', path)
            response = conn.getresponse()
            self.assertEqual(response.status, 200, path)
            self.assertEqual(response.read(), b'')
            conn.close()

    def test_first_try_win_and_reload_lock(self):
        game, cookie = self.start()
        status, result, _ = self.move(game, cookie, server.answer(server.today())['id'])
        self.assertEqual(status, 200)
        self.assertTrue(result['won'])
        self.assertEqual(result['version'], 1)
        self.assertEqual(result['stats']['played'], 1)
        self.assertEqual(result['stats']['wins'], 1)
        reloaded = self.request(cookie=cookie)[1]
        self.assertEqual(reloaded['moves'], result['moves'])
        self.assertEqual(self.move(reloaded, cookie)[0], 409)
        self.assertEqual(self.request(cookie=cookie)[1]['stats']['played'], 1)

    def test_daily_ranking_starts_after_first_round_updates_and_resets(self):
        game, cookie = self.start()
        self.assertEqual(self.request('/api/ranking', {'nickname': 'Torcida 7'}, cookie)[0], 403)
        self.assertEqual(self.request('/api/ranking', {'nickname': '<script>'}, cookie)[0], 400)

        wrong_player = next(p['id'] for p in server.PLAYERS if p['id'] != server.answer(server.today())['id'])
        _, game, _ = self.move(game, cookie)
        _, game, _ = self.move(game, cookie, wrong_player)
        _, game, _ = self.move(game, cookie, server.answer(server.today())['id'])
        self.assertTrue(game['done'])
        first = self.request('/api/ranking', cookie=cookie)[1]
        self.assertTrue(first['eligible'])
        self.assertEqual(first['previewScore'], {'players':88, 'teams':0, 'top10':0, 'total':88})
        status, ranked, _ = self.request('/api/ranking', {'nickname':'Torcida 7', 'total':300}, cookie,
                                         extra_headers={'x-vercel-ip-country':'br'})
        self.assertEqual(status, 200)
        self.assertEqual(ranked['mine']['total'], 88)
        self.assertEqual(ranked['mine']['countryCode'], 'BR')

        team = self.request('/api/game?mode=teams', cookie=cookie)[1]
        wrong_team = next(t['id'] for t in server.TEAMS if t['id'] != server.team_answer(server.today())['id'])
        for guess_id in (None, wrong_team, server.team_answer(server.today())['id']):
            _, team, _ = self.request('/api/guess',
                                      {'mode':'teams', 'day':team['day'], 'version':team['version'], 'teamId':guess_id}, cookie)
        self.assertTrue(team['done'])
        partial = self.request('/api/ranking', cookie=cookie)[1]
        self.assertEqual(partial['previewScore'], {'players':88, 'teams':78, 'top10':0, 'total':166})
        status, ranked, _ = self.request('/api/ranking', {'sync':True}, cookie)
        self.assertEqual(status, 200)
        self.assertEqual(ranked['mine']['total'], 166)
        self.assertEqual(ranked['mine']['countryCode'], 'BR')

        top10 = self.request('/api/game?mode=top10', cookie=cookie)[1]
        challenge = server.top10_answer(server.today())
        correct_ids = {item['player_id'] for item in challenge['ranking']}
        wrong_top10 = next(p['id'] for p in server.PLAYERS if p['id'] not in correct_ids)
        _, top10, _ = self.request('/api/guess', {'mode':'top10', 'day':top10['day'],
                                'version':top10['version'], 'position':1, 'playerId':wrong_top10}, cookie)
        for item in challenge['ranking']:
            _, top10, _ = self.request('/api/guess', {'mode':'top10', 'day':top10['day'],
                                    'version':top10['version'], 'position':item['position'],
                                    'playerId':item['player_id']}, cookie)
        self.assertTrue(top10['done'])

        status, preview, _ = self.request('/api/ranking', cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(preview['previewScore'], {'players':88, 'teams':78, 'top10':98, 'total':264})
        self.assertTrue(preview['submitted'])
        status, ranked, _ = self.request('/api/ranking', {'sync':True}, cookie)
        self.assertEqual(status, 200)
        self.assertEqual(ranked['mine']['total'], 264)
        self.assertEqual(self.request('/api/ranking', {'nickname':'Novo Nome'}, cookie)[0], 409)
        outsider, outsider_cookie = self.start()
        visible = self.request('/api/ranking', cookie=outsider_cookie)[1]
        self.assertTrue(any(row['nickname'] == 'Torcida 7' and row['total'] == 264 for row in visible['entries']))
        self.assertTrue(any(row['nickname'] == 'Torcida 7' and row['countryCode'] == 'BR' for row in visible['entries']))
        with patch.object(server, 'today', return_value=server.today() + timedelta(days=1)):
            next_day = self.request('/api/ranking', cookie=cookie)[1]
            self.assertEqual(next_day['entries'], [])
            self.assertFalse(next_day['submitted'])
            self.assertFalse(next_day['eligible'])

    def test_ranking_page_and_database_requirement(self):
        conn = http.client.HTTPConnection(*self.http.server_address)
        conn.request('GET', '/')
        home = conn.getresponse().read().decode('utf-8')
        conn.close()
        self.assertIn('href="/ranking"', home)
        conn = http.client.HTTPConnection(*self.http.server_address)
        conn.request('GET', '/ranking')
        response = conn.getresponse()
        page = response.read().decode('utf-8')
        conn.close()
        self.assertEqual(response.status, 200)
        self.assertIn('data-ad-slot="2022436715"', page)
        self.assertIn('https://www.golguess.com.br/ranking', page)
        with patch.object(server, 'cookie_mode', return_value=True):
            status, payload, _ = self.request('/api/ranking')
            self.assertEqual(status, 503)
            self.assertEqual(payload['code'], 'RANKING_REQUIRES_DATABASE')

    def test_supabase_ranking_uses_signed_rounds_and_server_score(self):
        secret = 'this-is-a-long-random-test-secret-for-ranking'
        with patch.dict(os.environ, {'GOLGUESS_SECRET': secret, 'SUPABASE_SECRET_KEY': 'sb_secret_test'}, clear=False), \
             patch.object(server, 'cookie_mode', return_value=True), \
             patch.object(supabase_ranking, 'own_row', return_value=None), \
             patch.object(supabase_ranking, 'insert') as insert, \
             patch.object(supabase_ranking, 'purge_old'), \
             patch.object(supabase_ranking, 'rows_for_day', return_value=([], 0)):
            day = str(server.today())
            base = {'v':1, 'day':day, 'played':1, 'wins':1, 'streak':1, 'lastWin':day}
            player_state = server.encode_state(dict(base, moves=[{'id':server.answer(server.today())['id'],
                                                                   'name':'Jogador', 'result':'correct'}]))
            team_state = server.encode_state(dict(base, moves=[{'id':server.team_answer(server.today())['id'],
                                                                 'name':'Time', 'result':'correct'}]))
            top10_state = server.encode_state(dict(base, moves=[{'id':None, 'name':'Desistência',
                                                                  'position':None, 'result':'giveup'}]))
            visitor = 'a' * 32
            signature = hmac.new(secret.encode(), ('rank:' + visitor).encode(), hashlib.sha256).hexdigest()
            cookie = f'gg_state={player_state}; gg_state_teams={team_state}; gg_state_top10={top10_state}; gg_rank_id={visitor}.{signature}'
            self.assertEqual(self.request('/api/ranking', {'nickname':'Teste'}, cookie.replace(signature, '0' * 64))[0], 403)
            status, payload, _ = self.request('/api/ranking', {'nickname':'Teste', 'total':300}, cookie,
                                              extra_headers={'x-vercel-ip-country':'PT'})
            self.assertEqual(status, 200)
            self.assertEqual(payload['previewScore']['total'], 200)
            self.assertEqual(insert.call_args.args[3], {'players':100, 'teams':100, 'top10':0, 'total':200})
            self.assertEqual(insert.call_args.args[4], 'PT')
            row = {'visitor':visitor, 'nickname':'Teste', 'players_score':100, 'teams_score':100,
                   'top10_score':0, 'total_score':200, 'country_code':'PT',
                   'submitted_at':'2026-01-01T00:00:00-03:00'}
            with patch.object(supabase_ranking, 'own_row', return_value=row), \
                 patch.object(supabase_ranking, 'update') as update, \
                 patch.object(supabase_ranking, 'rank_of', return_value=1):
                status, payload, _ = self.request('/api/ranking', {'sync':True}, cookie)
                self.assertEqual(status, 200)
                self.assertEqual(payload['mine']['total'], 200)
                self.assertEqual(update.call_args.args[2], {'players':100, 'teams':100, 'top10':0, 'total':200})

    def test_anon_key_cannot_be_used_as_supabase_write_key(self):
        with patch.dict(os.environ, {'SUPABASE_SECRET_KEY':
             'eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.signature'}, clear=False):
            self.assertFalse(supabase_ranking.configured())

    def test_supabase_request_keeps_secret_on_server(self):
        class Response:
            headers = {'Content-Range':'0-0/1'}
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self): return b'[{"visitor":"anon","nickname":"Teste"}]'
        with patch.dict(os.environ, {'SUPABASE_SECRET_KEY':'sb_secret_test',
                                    'SUPABASE_URL':'https://ucubzsvrlmlcbzrmxjda.supabase.co'}, clear=False), \
             patch.object(supabase_ranking, 'urlopen', return_value=Response()) as transport:
            rows, count = supabase_ranking.rows_for_day(server.today())
            sent = transport.call_args.args[0]
            self.assertEqual(count, 1)
            self.assertEqual(rows[0]['nickname'], 'Teste')
            self.assertIn('ucubzsvrlmlcbzrmxjda.supabase.co/rest/v1/daily_rankings', sent.full_url)
            self.assertEqual(sent.get_header('Apikey'), 'sb_secret_test')
            self.assertIsNone(sent.get_header('Authorization'))
            supabase_ranking.insert(server.today(), 'anon', 'Teste',
                                    {'players':94, 'teams':0, 'top10':0, 'total':94}, 'PT')
            sent = transport.call_args.args[0]
            self.assertEqual(sent.get_method(), 'POST')
            self.assertEqual(json.loads(sent.data)['country_code'], 'PT')
            supabase_ranking.update(server.today(), 'anon',
                                    {'players':94, 'teams':0, 'top10':0, 'total':94})
            sent = transport.call_args.args[0]
            self.assertEqual(sent.get_method(), 'PATCH')
            self.assertIn('visitor=eq.anon', sent.full_url)
            self.assertEqual(json.loads(sent.data),
                             {'players_score':94, 'teams_score':0, 'top10_score':0, 'total_score':94})

    def test_top10_giveup_cannot_earn_full_ranking_score(self):
        self.assertEqual(server.ranking_country_code({}), 'UN')
        self.assertEqual(server.ranking_country_code({'x-vercel-ip-country':' us '}), 'US')
        self.assertEqual(server.ranking_country_code({'x-vercel-ip-country':'unknown'}), 'UN')
        partial = server.ranking_scores({'players':[{'result':'correct'}], 'teams':[], 'top10':[]})
        self.assertEqual(partial, {'players':100, 'teams':0, 'top10':0, 'total':100})
        scores = server.ranking_scores({'players':[{'result':'correct'}],
                                        'teams':[{'result':'correct'}],
                                        'top10':[{'result':'giveup'}]})
        self.assertEqual(scores['top10'], 0)
        self.assertEqual(scores['total'], 200)

    def test_fifth_try_win(self):
        game, cookie = self.start()
        for _ in range(4):
            _, game, _ = self.move(game, cookie)
        _, game, _ = self.move(game, cookie, server.answer(server.today())['id'])
        self.assertTrue(game['won'])
        self.assertEqual(len(game['moves']), 5)
        self.assertEqual([m['result'] for m in game['moves']], ['skip'] * 4 + ['correct'])

    def test_sixth_try_win_in_cookie_mode(self):
        with patch.dict(os.environ, {'GOLGUESS_COOKIE_MODE': '1'}):
            game, cookie = self.start()
            for expected_count in (2, 3, 4, 5, 6):
                status, game, updated_cookie = self.move(game, cookie)
                self.assertEqual(status, 200)
                self.assertFalse(game['done'])
                self.assertEqual(len(game['clues']), expected_count)
                cookie = updated_cookie.split(';')[0]
            status, game, _ = self.move(game, cookie, server.answer(server.today())['id'])
            self.assertEqual(status, 200)
            self.assertTrue(game['done'])
            self.assertTrue(game['won'])
            self.assertEqual(len(game['moves']), 6)

    def test_loss_and_no_seventh_attempt(self):
        game, cookie = self.start()
        for _ in range(6):
            _, game, _ = self.move(game, cookie)
        self.assertTrue(game['done'])
        self.assertFalse(game['won'])
        self.assertTrue(game['answer'])
        self.assertEqual(self.move(game, cookie)[0], 409)

    def test_concurrent_tabs_consume_only_one_attempt(self):
        game, cookie = self.start()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: self.move(game, cookie), range(2)))
        self.assertEqual(sorted(r[0] for r in responses), [200, 409])
        self.assertEqual(self.request(cookie=cookie)[1]['version'], 1)

    def test_invalid_and_duplicate_guesses_do_not_cost_attempt(self):
        game, cookie = self.start()
        self.assertEqual(self.move(game, cookie, 'invented')[0], 400)
        wrong = next(p['id'] for p in server.PLAYERS if p['id'] != server.answer(server.today())['id'])
        _, game, _ = self.move(game, cookie, wrong)
        self.assertEqual(self.move(game, cookie, wrong)[0], 400)
        self.assertEqual(self.request(cookie=cookie)[1]['version'], 1)

    def test_midnight_rejects_old_round_without_spending_attempt(self):
        game, cookie = self.start()
        next_day = server.today() + timedelta(days=1)
        with patch.object(server, 'today', return_value=next_day):
            status, response, _ = self.move(game, cookie)
            self.assertEqual(status, 409)
            self.assertEqual(response['game']['version'], 0)
            self.assertEqual(response['game']['day'], str(next_day))
            self.assertTrue(response['game']['nextAt'].endswith('-03:00'))

    def test_streak_requires_consecutive_wins(self):
        base = server.today()
        game, cookie = self.start()
        _, game, _ = self.move(game, cookie, server.answer(base)['id'])
        for offset, expected in [(1, 2), (3, 1)]:
            with patch.object(server, 'today', return_value=base + timedelta(days=offset)):
                game = self.request(cookie=cookie)[1]
                _, game, _ = self.move(game, cookie, server.answer(base + timedelta(days=offset))['id'])
                self.assertEqual(game['stats']['streak'], expected)

    def test_search_accents_and_minimal_payload(self):
        status, results, _ = self.request('/api/players?q=mbappe')
        self.assertEqual(status, 200)
        self.assertTrue(any('Mbappé' in p['name'] for p in results))
        self.assertTrue(all(set(p) == {'id', 'name'} for p in results))

    def test_no_cookie_and_cross_origin_rejected(self):
        game, cookie = self.start()
        self.assertEqual(self.move(game, None)[0], 403)
        body = dict(day=game['day'], version=0, playerId=None)
        self.assertEqual(self.request('/api/guess', body, cookie, 'https://other.example')[0], 403)

    def test_health_endpoint(self):
        status, body, _ = self.request('/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(body['catalog'], 'career-v2')
        self.assertEqual(body['players'], len(server.PLAYERS))

    def test_vercel_without_database_uses_signed_cookie(self):
        old_vercel = os.environ.get('VERCEL')
        old_database = os.environ.pop('DATABASE_URL', None)
        old_postgres = os.environ.pop('POSTGRES_URL', None)
        os.environ['VERCEL'] = '1'
        try:
            status, game, cookie = self.request()
            self.assertEqual(status, 200)
            self.assertIn('gg_state=', cookie)
            cookie = cookie.split(';')[0]
            status, game, updated_cookie = self.move(game, cookie)
            self.assertEqual(status, 200)
            self.assertEqual(game['version'], 1)
            reloaded = self.request(cookie=updated_cookie.split(';')[0])[1]
            self.assertEqual(reloaded['moves'], game['moves'])
            health = self.request('/api/health')[1]
            self.assertEqual(health['storage'], 'signed-cookie')
        finally:
            if old_vercel is None:
                os.environ.pop('VERCEL', None)
            else:
                os.environ['VERCEL'] = old_vercel
            if old_database is not None:
                os.environ['DATABASE_URL'] = old_database
            if old_postgres is not None:
                os.environ['POSTGRES_URL'] = old_postgres

    def test_tampered_or_malformed_signed_state_is_rejected(self):
        state = {'v': 1, 'day': str(server.today()), 'moves': [], 'played': 0,
                 'wins': 0, 'streak': 0, 'lastWin': None}
        signed = server.encode_state(state)
        self.assertIsNone(server.decode_state(signed[:-1] + ('0' if signed[-1] != '0' else '1')))
        malformed = server.encode_state({'v': 1, 'day': str(server.today()), 'moves': []})
        self.assertIsNone(server.decode_state(malformed))

    def test_teams_clues_order_and_content(self):
        status, game, cookie = self.request('/api/game?mode=teams')
        self.assertEqual(status, 200)
        self.assertEqual(game['mode'], 'teams')
        self.assertGreater(game['totalTeams'], 200)
        self.assertIsNone(game['answer'])
        self.assertFalse(game['done'])
        self.assertEqual(len(game['clues']), 1)
        self.assertEqual(game['clues'][0]['key'], 'continent')
        self.assertIn(game['clues'][0]['value'], ('Américas', 'Europa'))

        # Reveal next clues by skipping
        for step, expected_key in enumerate(['titles', 'country', 'colors', 'city'], start=1):
            status, game, _ = self.request('/api/guess', body={'day': game['day'], 'version': game['version'],
                                                               'mode': 'teams', 'teamId': None}, cookie=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(len(game['clues']), step + 1)
            self.assertEqual(game['clues'][step]['key'], expected_key)

    def test_teams_search_and_win(self):
        status, teams, _ = self.request('/api/teams?q=flamengo')
        self.assertEqual(status, 200)
        self.assertTrue(any('flamengo' in t['id'] for t in teams))

        status, game, cookie = self.request('/api/game?mode=teams')
        self.assertEqual(status, 200)
        ans = server.team_answer(server.today())
        status, game, _ = self.request('/api/guess', body={'day': game['day'], 'version': game['version'],
                                                           'mode': 'teams', 'teamId': ans['id']}, cookie=cookie)
        self.assertEqual(status, 200)
        self.assertTrue(game['won'])
        self.assertTrue(game['done'])
        self.assertEqual(game['answer'], ans['name'])
        self.assertEqual(len(game['clues']), 5)
        self.assertEqual([c['key'] for c in game['clues']], ['continent', 'titles', 'country', 'colors', 'city'])

    def test_top10_game_flow_and_win(self):
        status, game, cookie = self.request('/api/game?mode=top10')
        self.assertEqual(status, 200)
        self.assertEqual(game['mode'], 'top10')
        self.assertEqual(len(game['slots']), 10)
        self.assertFalse(game['done'])
        self.assertFalse(game['won'])
        self.assertEqual(game['solvedCount'], 0)
        self.assertIn('title', game['challenge'])

        challenge = server.top10_answer(server.today())
        ranking = challenge['ranking']

        # Guess player 1 in wrong position (e.g. at position 2)
        p1 = ranking[0]
        status, game, new_cookie = self.request('/api/guess', body={'day': game['day'], 'version': game['version'],
                                                                    'mode': 'top10', 'playerId': p1['player_id'],
                                                                    'position': 2}, cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(game['moves'][-1]['result'], 'wrong_pos')
        self.assertEqual(game['solvedCount'], 0)
        if new_cookie:
            cookie = new_cookie.split(';')[0]

        # Guess all 10 correctly
        for item in ranking:
            status, game, new_cookie = self.request('/api/guess', body={'day': game['day'], 'version': game['version'],
                                                                        'mode': 'top10', 'playerId': item['player_id'],
                                                                        'position': item['position']}, cookie=cookie)
            self.assertEqual(status, 200)
            if new_cookie:
                cookie = new_cookie.split(';')[0]

        self.assertTrue(game['done'])
        self.assertTrue(game['won'])
        self.assertEqual(game['solvedCount'], 10)
        self.assertTrue(all(s['revealed'] for s in game['slots']))
        self.assertTrue(all(s['status'] == 'correct' for s in game['slots']))

    def test_top10_give_up_and_reveal(self):
        status, game, cookie = self.request('/api/game?mode=top10')
        self.assertEqual(status, 200)
        self.assertFalse(game['done'])
        self.assertFalse(game['won'])

        challenge = server.top10_answer(server.today())
        ranking = challenge['ranking']

        # Guess 1 player correctly
        p1 = ranking[0]
        status, game, new_cookie = self.request('/api/guess', body={'day': game['day'], 'version': game['version'],
                                                                    'mode': 'top10', 'playerId': p1['player_id'],
                                                                    'position': p1['position']}, cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(game['solvedCount'], 1)
        self.assertFalse(game['done'])
        if new_cookie:
            cookie = new_cookie.split(';')[0]

        # Give up
        status, game, new_cookie = self.request('/api/guess', body={'day': game['day'], 'version': game['version'],
                                                                    'mode': 'top10', 'giveup': True}, cookie=cookie)
        self.assertEqual(status, 200)
        self.assertTrue(game['done'])
        self.assertFalse(game['won'])
        self.assertEqual(game['solvedCount'], 1)
        self.assertEqual(game['moves'][-1]['result'], 'giveup')
        # All slots must be revealed
        self.assertTrue(all(s['revealed'] for s in game['slots']))
        self.assertEqual(game['slots'][0]['status'], 'correct')
        self.assertTrue(all(s['status'] == 'missed' for s in game['slots'][1:]))
        self.assertTrue(all(s['player_id'] and s['name'] for s in game['slots']))

        # Further attempts should be rejected with 409
        status, err, _ = self.request('/api/guess', body={'day': game['day'], 'version': game['version'],
                                                          'mode': 'top10', 'giveup': True}, cookie=cookie)
        self.assertEqual(status, 409)

    def test_top10_give_up_in_cookie_mode(self):
        with patch.dict(os.environ, {'GOLGUESS_COOKIE_MODE': '1'}):
            status, game, cookie = self.request('/api/game?mode=top10')
            self.assertEqual(status, 200)
            self.assertFalse(game['done'])

            status, game, new_cookie = self.request('/api/guess', body={'day': game['day'], 'version': game['version'],
                                                                        'mode': 'top10', 'giveup': True}, cookie=cookie)
            self.assertEqual(status, 200)
            self.assertTrue(game['done'])
            self.assertFalse(game['won'])
            self.assertEqual(game['solvedCount'], 0)
            self.assertTrue(all(s['revealed'] for s in game['slots']))
            self.assertTrue(all(s['status'] == 'missed' for s in game['slots']))
            self.assertIn('gg_state_top10', new_cookie)


if __name__ == '__main__':
    unittest.main()

