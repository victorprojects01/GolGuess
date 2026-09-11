import concurrent.futures
import http.client
import json
import tempfile
import threading
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import server


class DailyGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_db = server.DB_PATH
        server.DB_PATH = Path(cls.temp.name) / 'test.sqlite3'
        server.initialize()
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        server.DB_PATH = cls.old_db
        cls.temp.cleanup()

    def request(self, path='/api/game', body=None, cookie=None, origin=None):
        conn = http.client.HTTPConnection(*self.http.server_address)
        headers = {'Content-Type': 'application/json'}
        if cookie:
            headers['Cookie'] = cookie
        if origin:
            headers['Origin'] = origin
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
        for p in server.PLAYERS:
            self.assertTrue(all(p.values()))
            server.date.fromisoformat(p['birth'])

    def test_answer_hidden_and_private_files_blocked(self):
        game, _ = self.start()
        self.assertIsNone(game['answer'])
        self.assertEqual(len(game['clues']), 1)
        for path in ['/data/players.json', '/server.py', '/.runtime/game.sqlite3', '/.git/config', '/../server.py']:
            self.assertEqual(self.request(path)[0], 404)

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

    def test_fifth_try_win(self):
        game, cookie = self.start()
        for _ in range(4):
            _, game, _ = self.move(game, cookie)
        _, game, _ = self.move(game, cookie, server.answer(server.today())['id'])
        self.assertTrue(game['won'])
        self.assertEqual(len(game['moves']), 5)
        self.assertEqual([m['result'] for m in game['moves']], ['skip'] * 4 + ['correct'])

    def test_loss_and_no_sixth_attempt(self):
        game, cookie = self.start()
        for _ in range(5):
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


if __name__ == '__main__':
    unittest.main()
