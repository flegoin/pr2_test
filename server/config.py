"""Конфигурация сервера и подключения к БД.

Значения берутся из переменных окружения; при наличии файла `.env`
рядом с этим файлом — предварительно подгружается из него.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    """Минимальный загрузчик .env (KEY=VALUE), без внешних зависимостей."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


_load_dotenv(BASE_DIR / ".env")


class Config:
    # --- PostgreSQL ---
    PGHOST = os.environ.get("PGHOST", "localhost")
    PGPORT = int(os.environ.get("PGPORT", "5432"))
    PGDATABASE = os.environ.get("PGDATABASE", "theater")
    PGUSER = os.environ.get("PGUSER", "postgres")
    PGPASSWORD = os.environ.get("PGPASSWORD", "")

    # --- HTTP-сервер ---
    SERVER_HOST = os.environ.get("SERVER_HOST", "127.0.0.1")
    SERVER_PORT = int(os.environ.get("SERVER_PORT", "3000"))
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
