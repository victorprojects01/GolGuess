"""Build the versioned catalog from Fjelstul's squads.csv and players.csv."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = dict(zip(
    'Argentina|Australia|Belgium|Brazil|Cameroon|Canada|Costa Rica|Croatia|Denmark|Ecuador|England|France|Germany|Ghana|Iran|Japan|Mexico|Morocco|Netherlands|Poland|Portugal|Qatar|Saudi Arabia|Senegal|Serbia|South Korea|Spain|Switzerland|Tunisia|United States|Uruguay|Wales'.split('|'),
    'Argentina|Austrália|Bélgica|Brasil|Camarões|Canadá|Costa Rica|Croácia|Dinamarca|Equador|Inglaterra|França|Alemanha|Gana|Irã|Japão|México|Marrocos|Países Baixos|Polônia|Portugal|Catar|Arábia Saudita|Senegal|Sérvia|Coreia do Sul|Espanha|Suíça|Tunísia|Estados Unidos|Uruguai|País de Gales'.split('|')))

def build(squads_path, players_path):
    with open(players_path, encoding='utf-8-sig') as f:
        people = {p['player_id']: p for p in csv.DictReader(f)}
    with open(squads_path, encoding='utf-8-sig') as f:
        squads = [p for p in csv.DictReader(f) if p['tournament_id'] == 'WC-2022']
    result = []
    for p in squads:
        person = people[p['player_id']]
        name = ' '.join(v for v in (p['given_name'], p['family_name']) if v and v != 'not applicable')
        result.append(dict(id=p['player_id'], name=name, country=COUNTRIES[p['team_name']],
                           position={'GK':'Goleiro','DF':'Defensor','MF':'Meio-campista','FW':'Atacante'}[p['position_code']],
                           birth=person['birth_date'], shirt=int(p['shirt_number'])))
    result.sort(key=lambda p: p['id'])
    assert len({p['id'] for p in result}) == len(result) >= 365
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/players.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(result)} jogadores únicos importados.')

if __name__ == '__main__':
    build(*sys.argv[1:])
