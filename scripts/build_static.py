"""Publish only an allowlist. Catalog, source code and SQLite must stay private."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
DIST = ROOT / 'dist'
FILES = [
    'daily.js', 'ads.js', 'ads.css', 'app.js', 'styles.css', 'institucional.css',
    'ranking.html', 'ranking.js', 'ranking.css',
    'favicon.ico', 'favicon.svg', 'favicon-32.png', 'apple-touch-icon.png',
    'icon-192.png', 'icon-512.png', 'site.webmanifest',
    'assets/logo-mark.svg', 'assets/golguess-social.png',
    'sobre.html', 'como-jogar.html', 'politica-de-privacidade.html',
    'politica-de-cookies.html', 'termos-de-uso.html', 'contato.html', 'atribuicao.html',
    'data/ATTRIBUTION.md', 'ads.txt', 'robots.txt', 'sitemap.xml',
]

def build():
    for folder in (PUBLIC, DIST):
        for name in ('index.html', 'arquivo.html'):
            (folder / name).unlink(missing_ok=True)
    for name in FILES:
        for folder in (PUBLIC, DIST):
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
    unexpected = [p for p in PUBLIC.rglob('*') if p.is_file() and p.relative_to(PUBLIC).as_posix() not in FILES]
    if unexpected:
        raise RuntimeError('Unexpected file in public output; review before deployment.')
    print(f'Static build ready: {len(FILES)} public files. API handled by Vercel Python Functions.')

if __name__ == '__main__':
    build()
