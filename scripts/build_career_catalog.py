"""Build the editorial club-season catalog from transfermarkt-datasets CSV exports."""
import csv
import gzip
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

from player_metadata import profile_fields

ROOT = Path(__file__).resolve().parents[1]
COMPETITIONS = {
    'GB1': 'Premier League', 'ES1': 'La Liga', 'IT1': 'Serie A',
    'L1': 'Bundesliga', 'FR1': 'Ligue 1',
    'BRA1': 'Campeonato Brasileiro - Série A', 'ARG1': 'Liga Profesional',
}
EUROPE = {'GB1', 'ES1', 'IT1', 'L1', 'FR1'}
TEAM_NAMES = {
    'FC Barcelona': 'Barcelona', 'Real Madrid CF': 'Real Madrid', 'Atlético de Madrid': 'Atlético de Madrid',
    'Arsenal FC': 'Arsenal', 'Chelsea FC': 'Chelsea', 'Liverpool FC': 'Liverpool',
    'Tottenham Hotspur': 'Tottenham', 'Manchester United': 'Manchester United',
    'Manchester City': 'Manchester City', 'Bayern Munich': 'Bayern de Munique',
    'Paris Saint-Germain': 'Paris Saint-Germain', 'Inter Milan': 'Inter de Milão',
    'SSC Napoli': 'Napoli', 'ACF Fiorentina': 'Fiorentina',
    'Associazione Sportiva Roma': 'Roma', 'Juventus FC': 'Juventus',
    'Clube de Regatas do Flamengo': 'Flamengo', 'Sociedade Esportiva Palmeiras': 'Palmeiras',
    'Sport Club Corinthians Paulista': 'Corinthians', 'São Paulo Futebol Clube': 'São Paulo',
    'Grêmio Foot-Ball Porto Alegrense': 'Grêmio', 'Sport Club Internacional': 'Internacional',
    'Clube Atlético Mineiro': 'Atlético-MG', 'Cruzeiro Esporte Clube': 'Cruzeiro',
    'Fluminense Football Club': 'Fluminense', 'S. A. F. Botafogo': 'Botafogo',
    'Esporte Clube Bahia': 'Bahia', 'Santos Futebol Clube': 'Santos',
    'Fortaleza Esporte Clube': 'Fortaleza', 'Coritiba Foot Ball Club': 'Coritiba',
    'Club Atlético Boca Juniors': 'Boca Juniors', 'Club Atlético River Plate': 'River Plate',
    'Racing Club Asociación Civil de Avellaneda': 'Racing',
    'Club Estudiantes de La Plata': 'Estudiantes', 'Club Atlético Lanús': 'Lanús',
    'Club Atlético Tigre': 'Tigre', 'Club Atlético Belgrano': 'Belgrano',
}

def norm(value):
    value = ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()

def rows(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    return csv.DictReader(opener(path, 'rt', encoding='utf-8-sig', newline=''))

def season_label(competition, season):
    year = int(season)
    return f'{year}/{str(year + 1)[-2:]}' if competition in EUROPE else str(year)

def main(players_path, appearances_path, games_path, clubs_path, events_path):
    people = {p['player_id']: p for p in rows(players_path)}
    clubs = {c['club_id']: c['name'] for c in rows(clubs_path)}
    game_info = {}
    for game in rows(games_path):
        competition = game['competition_id']
        season = game['date'][:4] if competition in {'BRA1', 'ARG1'} else game['season']
        if competition in COMPETITIONS and 2005 <= int(season) <= date.today().year:
            game_info[game['game_id']] = (competition, season)
    totals = defaultdict(lambda: dict(matches=0, minutes=0, goals=0, assists=0, yellow=0, red=0))
    for a in rows(appearances_path):
        info = game_info.get(a['game_id'])
        if not info or a['player_id'] not in people:
            continue
        competition, season = info
        key = (a['player_id'], competition, season, a['player_club_id'])
        total = totals[key]
        total['matches'] += 1
        for source, target in [('minutes_played','minutes'), ('goals','goals'), ('assists','assists'),
                               ('yellow_cards','yellow'), ('red_cards','red')]:
            total[target] += int(a[source] or 0)

    # The source snapshot has match events, but no appearance rows, for Brazil and Argentina.
    # Substitutions establish participation; goals/cards also establish it for starters.
    south_america = {'BRA1', 'ARG1'}
    event_games = defaultdict(set)
    for event in rows(events_path):
        info = game_info.get(event['game_id'])
        if not info or info[0] not in south_america:
            continue
        competition, season = info
        club_id = event['club_id']
        involved = [event['player_id']]
        if event['type'] == 'Substitutions' and event['player_in_id']:
            involved.append(event['player_in_id'])
        for player_id in involved:
            if player_id in people:
                key = (player_id, competition, season, club_id)
                event_games[key].add(event['game_id'])
        if event['type'] == 'Goals' and event['player_id'] in people:
            totals[(event['player_id'], competition, season, club_id)]['goals'] += 1
            if event['player_assist_id'] in people:
                totals[(event['player_assist_id'], competition, season, club_id)]['assists'] += 1
                event_games[(event['player_assist_id'], competition, season, club_id)].add(event['game_id'])
        elif event['type'] == 'Cards' and event['player_id'] in people:
            field = 'red' if 'Red card' in event['description'] else 'yellow'
            totals[(event['player_id'], competition, season, club_id)][field] += 1
    for key, games_seen in event_games.items():
        totals[key]['matches'] = len(games_seen)
        totals[key]['minutes'] = len(games_seen) * 90

    requested = []
    seen = set()
    for line in (ROOT / 'data/curated_names.txt').read_text(encoding='utf-8-sig').splitlines():
        name = line.strip()
        if name and not name.startswith('#') and norm(name) not in seen:
            requested.append(name); seen.add(norm(name))
    by_name = defaultdict(list)
    for person in people.values():
        by_name[norm(person['name'])].append(person)

    required = ['Rogério Ceni', 'Raheem Sterling', 'Samuel Umtiti', 'Antonio Di Natale',
                'Steven Gerrard', 'Jadon Sancho', 'Harry Kane', 'Lionel Messi',
                'Alexandre Pato', 'Oscar', 'Mesut Özil']
    required_names = {norm(name) for name in required}
    catalog, missing = [], []
    for requested_name in requested:
        matches = by_name.get(norm(requested_name), [])
        candidates = []
        for person in matches:
            highest_value = int(person['highest_market_value_in_eur'] or 0)
            for (player_id, competition, season, club_id), total in totals.items():
                if (player_id == person['player_id'] and total['minutes'] >= 450
                        and (highest_value >= (5_000_000 if competition in south_america else 20_000_000)
                             or norm(requested_name) in required_names)):
                    # A high-output season wins for attackers; minutes keep defenders/GKs representative.
                    score = total['minutes'] + 240 * (total['goals'] + total['assists'])
                    candidates.append((score, int(season), club_id, competition, total, person))
        if not candidates:
            missing.append(requested_name)
            continue
        _, season, club_id, competition, total, person = max(candidates)
        birth = person['date_of_birth'][:10]
        if not birth:
            missing.append(requested_name)
            continue
        catalog.append({
            'id': f"tm-{person['player_id']}", 'name': person['name'], 'birth': birth,
            **profile_fields(person),
            'league': COMPETITIONS[competition], 'season': season_label(competition, season),
            'goals': total['goals'], 'assists': total['assists'],
            'yellow': total['yellow'], 'red': total['red'],
            'team': TEAM_NAMES.get(clubs.get(club_id), clubs.get(club_id, f'Clube {club_id}')),
            'matches': total['matches'],
            'source': 'transfermarkt-datasets',
        })

    supplements = json.loads((ROOT / 'data/legacy_players.json').read_text(encoding='utf-8'))
    present = {norm(p['name']) for p in catalog}
    catalog.extend(p for p in supplements if norm(p['name']) not in present)
    catalog.sort(key=lambda p: norm(p['name']))
    if len({p['id'] for p in catalog}) != len(catalog) or len({norm(p['name']) for p in catalog}) != len(catalog):
        raise ValueError('Catalog IDs and normalized names must be unique.')
    absent = [name for name in required if norm(name) not in {norm(p['name']) for p in catalog}]
    if absent or len(catalog) < 365:
        raise ValueError(f'Catalog incomplete: {len(catalog)} players; required missing: {absent}')
    (ROOT / 'data/players.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'data/unmatched_curated.txt').write_text('\n'.join(missing) + '\n', encoding='utf-8')
    print(f'{len(catalog)} known players written; {len(missing)} curated names unavailable in the source snapshot.')

if __name__ == '__main__':
    main(*sys.argv[1:])
