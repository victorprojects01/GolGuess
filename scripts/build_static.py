"""Publish only an allowlist. Catalog, source code and SQLite must stay private."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
FILES = ['index.html', 'app.js', 'styles.css', 'data/ATTRIBUTION.md']

def build():
    for name in FILES:
        target = PUBLIC / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    unexpected = [p for p in PUBLIC.rglob('*') if p.is_file() and p.relative_to(PUBLIC).as_posix() not in FILES]
    if unexpected:
        raise RuntimeError('Unexpected file in public output; review before deployment.')
    print('Static build ready: 4 public files. API handled by Vercel Python Functions.')

if __name__ == '__main__':
    build()
