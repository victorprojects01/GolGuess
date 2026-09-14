"""Add verified profile clues to the existing catalog from players.csv.gz."""
import csv
import gzip
import json
import sys
from pathlib import Path

from player_metadata import profile_fields

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data/players.json'


def enrich(source_path):
    opener = gzip.open if str(source_path).endswith('.gz') else open
    with opener(source_path, 'rt', encoding='utf-8-sig', newline='') as source:
        rows = {str(row['player_id']): row for row in csv.DictReader(source)}
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    updated = []
    for player in catalog:
        player_id = player['id']
        if player_id.startswith('tm-'):
            source_id = player_id[3:]
            if source_id not in rows:
                raise ValueError(f'Player missing from source: {player_id}')
            fields = profile_fields(rows[source_id])
        else:
            fields = {key: player[key] for key in ('position', 'nationality', 'nationalityCode')}
        if not all(fields.values()):
            raise ValueError(f'Incomplete profile: {player_id}')
        updated.append({'id': player['id'], 'name': player['name'], 'birth': player['birth'],
                        **fields, **{key: value for key, value in player.items()
                                   if key not in {'id', 'name', 'birth', *fields}}})
    if len(updated) != len(catalog):
        raise ValueError('Catalog size changed unexpectedly.')
    CATALOG.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(updated)} player profiles enriched.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/enrich_player_catalog.py players.csv.gz')
    enrich(Path(sys.argv[1]))
