"""Server-only Supabase Data API access for the daily leaderboard."""
import json
import os
import base64
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from storage import StorageUnavailable

PROJECT_ID = 'ucubzsvrlmlcbzrmxjda'


def secret_key():
    for key in (os.environ.get('SUPABASE_SECRET_KEY'), os.environ.get('SUPABASE_SERVICE_ROLE_KEY')):
        if not key:
            continue
        if key.startswith('sb_secret_'):
            return key
        if key.startswith('eyJ'):
            try:
                payload = key.split('.')[1]
                claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
                if claims.get('role') == 'service_role':
                    return key
            except (IndexError, ValueError, UnicodeError):
                pass
    return None


def configured():
    return bool(secret_key())


def base_url():
    return os.environ.get('SUPABASE_URL', f'https://{PROJECT_ID}.supabase.co').rstrip('/')


def request(method, query='', payload=None, count=False):
    key = secret_key()
    if not key:
        raise StorageUnavailable('SUPABASE_SECRET_NOT_CONFIGURED')
    url = base_url() + '/rest/v1/daily_rankings' + ('?' + query if query else '')
    headers = {'apikey': key, 'Accept': 'application/json',
               'Prefer': 'count=exact' if count else 'return=minimal'}
    # Legacy JWT service_role keys also accept Bearer auth. New sb_secret keys
    # are sent only as apikey so Supabase's gateway applies the service role.
    if key.startswith('eyJ'):
        headers['Authorization'] = 'Bearer ' + key
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
    if data is not None:
        headers['Content-Type'] = 'application/json'
    try:
        with urlopen(Request(url, data=data, headers=headers, method=method), timeout=8) as response:
            raw = response.read()
            rows = json.loads(raw) if raw else []
            total = response.headers.get('Content-Range', '').rsplit('/', 1)[-1]
            return rows, int(total) if total.isdigit() else None
    except HTTPError as exc:
        if exc.code == 409:
            raise RankingConflict() from None
        raise StorageUnavailable('SUPABASE_REQUEST_FAILED') from None
    except (URLError, TimeoutError, ValueError):
        raise StorageUnavailable('SUPABASE_REQUEST_FAILED') from None


class RankingConflict(Exception):
    pass


def rows_for_day(day):
    query = urlencode({'select': 'visitor,nickname,country_code,players_score,teams_score,top10_score,total_score,submitted_at',
                       'day': 'eq.' + str(day),
                       'order': 'total_score.desc,submitted_at.asc,visitor.asc',
                       'limit': '100'})
    return request('GET', query, count=True)


def own_row(day, visitor):
    query = urlencode({'select': 'visitor,nickname,country_code,players_score,teams_score,top10_score,total_score,submitted_at',
                       'day': 'eq.' + str(day), 'visitor': 'eq.' + visitor, 'limit': '1'})
    rows, _ = request('GET', query)
    return rows[0] if rows else None


def rank_of(day, row):
    stamp = row['submitted_at']
    visitor = row['visitor']
    score = row['total_score']
    earlier = f'(total_score.gt.{score},and(total_score.eq.{score},submitted_at.lt.{stamp}),and(total_score.eq.{score},submitted_at.eq.{stamp},visitor.lt.{visitor}))'
    query = urlencode({'select': 'visitor', 'day': 'eq.' + str(day), 'or': earlier})
    _, count = request('HEAD', query, count=True)
    return (count or 0) + 1


def insert(day, visitor, nickname, scores, country_code='UN'):
    payload = {'day': str(day), 'visitor': visitor, 'nickname': nickname, 'country_code': country_code,
               'players_score': scores['players'], 'teams_score': scores['teams'],
               'top10_score': scores['top10'], 'total_score': scores['total']}
    request('POST', payload=payload)


def update(day, visitor, scores):
    query = urlencode({'day': 'eq.' + str(day), 'visitor': 'eq.' + visitor})
    payload = {'players_score': scores['players'], 'teams_score': scores['teams'],
               'top10_score': scores['top10'], 'total_score': scores['total']}
    request('PATCH', query, payload=payload)


def purge_old(day):
    request('DELETE', urlencode({'day': 'lt.' + str(day)}))
