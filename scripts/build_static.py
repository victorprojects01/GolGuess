"""Publish only an allowlist. Catalog, source code and SQLite must stay private."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
DIST = ROOT / 'dist'
FILES = [
    'index.html', 'app.js', 'styles.css', 'institucional.css',
    'ranking.html', 'ranking.js', 'ranking.css',
    'favicon.ico', 'favicon.svg', 'favicon-32.png', 'apple-touch-icon.png',
    'icon-192.png', 'icon-512.png', 'site.webmanifest',
    'assets/logo-mark.svg', 'assets/golguess-social.png',
    'sobre.html', 'como-jogar.html', 'politica-de-privacidade.html',
    'politica-de-cookies.html', 'termos-de-uso.html', 'contato.html',
    'arquivo.html',
    'data/ATTRIBUTION.md', 'ads.txt', 'robots.txt', 'sitemap.xml',
]

def build():
    # Pre-render archive HTML so /arquivo.html is never a dead link
    try:
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from server import archive_html, today
        archive_content = archive_html(today(), 1)
        if archive_content:
            (ROOT / 'arquivo.html').write_bytes(archive_content)
    except Exception as exc:
        print(f'Archive pre-render notice: {exc}')

    for name in FILES:
        for folder in (PUBLIC, DIST):
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
    unexpected = [p for p in PUBLIC.rglob('*') if p.is_file() and not p.name.startswith('.') and p.relative_to(PUBLIC).as_posix() not in FILES]
    if unexpected:
        raise RuntimeError(f'Unexpected file in public output: {unexpected}; review before deployment.')
    print(f'Static build ready: {len(FILES)} files in public and dist. API handled by Python server.')

if __name__ == '__main__':
    build()
