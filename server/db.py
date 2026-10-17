"""Доступ к PostgreSQL через psycopg 3."""
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from config import Config


def connect() -> psycopg.Connection:
    """Новое соединение (строки приходят как dict)."""
    return psycopg.connect(
        host=Config.PGHOST,
        port=Config.PGPORT,
        dbname=Config.PGDATABASE,
        user=Config.PGUSER,
        password=Config.PGPASSWORD,
        row_factory=dict_row,
    )


@contextmanager
def get_cursor():
    """Курсор в контексте соединения.

    При успешном выходе транзакция фиксируется (COMMIT),
    при исключении — откатывается (ROLLBACK); connection закрывается.
    """
    with connect() as conn:
        with conn.cursor() as cur:
            yield cur
