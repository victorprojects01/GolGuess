"""Editorial translation of the source's player profile fields."""

# Transfermarkt's primary country field supplies the nationality clue.
# Keep the source's England, Scotland and Wales identities distinct.
COUNTRIES = {
    'Albania': ('Albânia', 'AL'),
    'Algeria': ('Argélia', 'DZ'),
    'Argentina': ('Argentina', 'AR'),
    'Armenia': ('Armênia', 'AM'),
    'Austria': ('Áustria', 'AT'),
    'Belgium': ('Bélgica', 'BE'),
    'Bosnia-Herzegovina': ('Bósnia e Herzegovina', 'BA'),
    'Brazil': ('Brasil', 'BR'),
    'Bulgaria': ('Bulgária', 'BG'),
    'Burkina Faso': ('Burkina Faso', 'BF'),
    'Cameroon': ('Camarões', 'CM'),
    'Canada': ('Canadá', 'CA'),
    'Central African Republic': ('República Centro-Africana', 'CF'),
    'Chile': ('Chile', 'CL'),
    'Colombia': ('Colômbia', 'CO'),
    'Costa Rica': ('Costa Rica', 'CR'),
    "Cote d'Ivoire": ('Costa do Marfim', 'CI'),
    'Croatia': ('Croácia', 'HR'),
    'Czech Republic': ('Tchéquia', 'CZ'),
    'Denmark': ('Dinamarca', 'DK'),
    'DR Congo': ('República Democrática do Congo', 'CD'),
    'Ecuador': ('Equador', 'EC'),
    'Egypt': ('Egito', 'EG'),
    'England': ('Inglaterra', 'GB-ENG'),
    'France': ('França', 'FR'),
    'Gabon': ('Gabão', 'GA'),
    'Georgia': ('Geórgia', 'GE'),
    'Germany': ('Alemanha', 'DE'),
    'Ghana': ('Gana', 'GH'),
    'Guinea': ('Guiné', 'GN'),
    'Hungary': ('Hungria', 'HU'),
    'Iceland': ('Islândia', 'IS'),
    'Italy': ('Itália', 'IT'),
    'Jamaica': ('Jamaica', 'JM'),
    'Japan': ('Japão', 'JP'),
    'Kenya': ('Quênia', 'KE'),
    'Korea, South': ('Coreia do Sul', 'KR'),
    'Kosovo': ('Kosovo', 'XK'),
    'Mali': ('Mali', 'ML'),
    'Mexico': ('México', 'MX'),
    'Montenegro': ('Montenegro', 'ME'),
    'Morocco': ('Marrocos', 'MA'),
    'Netherlands': ('Países Baixos', 'NL'),
    'Nigeria': ('Nigéria', 'NG'),
    'Norway': ('Noruega', 'NO'),
    'Paraguay': ('Paraguai', 'PY'),
    'Peru': ('Peru', 'PE'),
    'Poland': ('Polônia', 'PL'),
    'Portugal': ('Portugal', 'PT'),
    'Romania': ('Romênia', 'RO'),
    'Russia': ('Rússia', 'RU'),
    'Scotland': ('Escócia', 'GB-SCT'),
    'Senegal': ('Senegal', 'SN'),
    'Serbia': ('Sérvia', 'RS'),
    'Slovakia': ('Eslováquia', 'SK'),
    'Slovenia': ('Eslovênia', 'SI'),
    'Spain': ('Espanha', 'ES'),
    'Sweden': ('Suécia', 'SE'),
    'Switzerland': ('Suíça', 'CH'),
    'Togo': ('Togo', 'TG'),
    'Turkey': ('Turquia', 'TR'),
    'Türkiye': ('Turquia', 'TR'),
    'Ukraine': ('Ucrânia', 'UA'),
    'United States': ('Estados Unidos', 'US'),
    'Uruguay': ('Uruguai', 'UY'),
    'Venezuela': ('Venezuela', 'VE'),
    'Wales': ('País de Gales', 'GB-WLS'),
}

# Two source rows have no citizenship; both were checked against UEFA profiles.
COUNTRY_OVERRIDES = {'41982': 'Belgium', '28021': 'Slovenia'}

def position_code(position, sub_position):
    if position == 'Goalkeeper':
        return 'GOL'
    if position == 'Attack':
        return 'ATA'
    if position == 'Midfield':
        return 'MEI'
    if position == 'Defender':
        if sub_position == 'Centre-Back':
            return 'ZAG'
        if sub_position in ('Right-Back', 'Left-Back'):
            return 'LAT'
    raise ValueError(f'Unmapped player position: {position!r} / {sub_position!r}')


def profile_fields(person):
    country = person['country_of_citizenship'] or COUNTRY_OVERRIDES.get(str(person['player_id']))
    if country not in COUNTRIES:
        raise ValueError(f'Unmapped citizenship for {person["player_id"]}: {country!r}')
    nationality, code = COUNTRIES[country]
    return {'position': position_code(person['position'], person['sub_position']),
            'nationality': nationality, 'nationalityCode': code}
