"""SQLite locally; durable PostgreSQL on Vercel. Never store rounds in /tmp."""
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('GOLGUESS_DB', ROOT / '.runtime/game.sqlite3'))
_initialized = set()
_schema_lock = threading.Lock()

class StorageUnavailable(Exception):
    def __init__(self, code='STORAGE_UNAVAILABLE'):
        self.code = code
        super().__init__('O armazenamento do jogo está temporariamente indisponível.')

def database_url():
    return os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

class Database:
    def __init__(self, connection, postgres):
        self.connection, self.postgres = connection, postgres

    def execute(self, sql, params=()):
        if self.postgres:
            sql = sql.replace('?', '%s')
        return self.connection.execute(sql, params)

    def lock_visitor(self, visitor):
        if self.postgres:
            self.execute('SELECT id FROM visitors WHERE id=? FOR UPDATE', (visitor,))

@contextmanager
def connect():
    url = database_url()
    if not url and os.environ.get('VERCEL'):
        raise StorageUnavailable('DATABASE_NOT_CONFIGURED')
    conn = None
    try:
        if url:
            import psycopg
            from psycopg.rows import dict_row
            conn = psycopg.connect(url, row_factory=dict_row, connect_timeout=8,
                                  options='-c statement_timeout=10000', prepare_threshold=None)
        else:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.row_factory = sqlite3.Row
        db = Database(conn, bool(url))
        identity = url or str(DB_PATH)
        with _schema_lock:
            if identity not in _initialized:
                if url:
                    db.execute('SELECT pg_advisory_xact_lock(7149202611)')
                else:
                    db.execute('PRAGMA journal_mode=WAL')
                db.execute('CREATE TABLE IF NOT EXISTS visitors (id TEXT PRIMARY KEY)')
                db.execute('CREATE TABLE IF NOT EXISTS career_rounds (visitor TEXT, day TEXT, moves TEXT NOT NULL, PRIMARY KEY(visitor, day))')
                conn.commit()
                _initialized.add(identity)
        with conn:
            yield db
    except StorageUnavailable:
        raise
    except Exception as exc:
        # Never expose connection strings or database errors through an HTTP response.
        if isinstance(exc, (sqlite3.Error, ImportError)) or type(exc).__module__.startswith('psycopg'):
            raise StorageUnavailable() from None
        raise
    finally:
        if conn is not None:
            conn.close()
