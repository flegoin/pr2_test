# -*- coding: utf-8 -*-
"""
REST API (Flask) для CRUD над всеми таблицами БД "Покупка билетов в театр".

Запуск:  python rest_api.py        (порт 8080)

Авторизация: HTTP Basic Auth, где логин и пароль — учётные данные PostgreSQL.
Сервер под каждым запросом открывает соединение к БД от имени указанного
пользователя; при неверных данных PostgreSQL возвращается 401.

Переменные окружения (со значениями по умолчанию):
    PGHOST=localhost   PGPORT=5432   PGDATABASE=teatr
    API_HOST=127.0.0.1 API_PORT=8080

Ресурсы (ASCII-алиас -> таблица):
    genres         -> жанры
    plays          -> спектакли
    play_genres    -> спектакли_жанры        (составной PK)
    actors         -> актёры
    actor_plays    -> актёры_спектакли       (составной PK)
    halls          -> залы
    seats          -> места
    shows          -> показы
    hall_passports -> паспорта_залов

Точки входа:
    GET    /api                     список ресурсов и подсказка
    GET    /api/<resource>          список (?limit=&offset= и фильтры по столбцам)
    POST   /api/<resource>          создать запись (JSON)
    GET    /api/<resource>/<pk>     прочитать одну запись
    PUT    /api/<resource>/<pk>     обновить (полностью; тело JSON)
    PATCH  /api/<resource>/<pk>     обновить (частично; тело JSON)
    DELETE /api/<resource>/<pk>     удалить
    GET    /health                  проверка живости (без авторизации)

Для составного первичного ключа значения указываются через запятую,
в порядке столбцов PK, например: /api/play_genres/1,2
"""

import os
from decimal import Decimal
from datetime import date, datetime, time

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from flask import Flask, g, request, jsonify

# ------------------------------------------------------------ конфигурация
PGHOST = os.environ.get("PGHOST", "localhost")
PGPORT = int(os.environ.get("PGPORT", "5432"))
PGDATABASE = os.environ.get("PGDATABASE", "teatr")
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "8080"))

# ASCII-алиас -> реальное (кириллическое) имя таблицы
RESOURCES = {
    "genres": "жанры",
    "plays": "спектакли",
    "play_genres": "спектакли_жанры",
    "actors": "актёры",
    "actor_plays": "актёры_спектакли",
    "halls": "залы",
    "seats": "места",
    "shows": "показы",
    "hall_passports": "паспорта_залов",
}

INT_TYPES = {"smallint", "integer", "bigint"}
NUM_TYPES = {"numeric", "decimal", "real", "double precision", "money"}

app = Flask(__name__)
app.json.ensure_ascii = False


# ------------------------------------------------------------ утилиты JSON
def jsonable(value):
    """Приводит значения из БД к JSON-совместимому виду."""
    if value is None or isinstance(value, (int, float, bool, str)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return str(value)


def row_to_dict(row):
    return {k: jsonable(v) for k, v in row.items()}


def json_error(status, message, detail=None):
    payload = {"error": message}
    if detail:
        payload["detail"] = detail
    return jsonify(payload), status


# ------------------------------------------------------------ метаданные БД
_meta_cache = {}


def load_table_meta(conn, table):
    """Читает из каталога столбцы и первичный ключ таблицы (с кэшем)."""
    if table in _meta_cache:
        return _meta_cache[table]

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT column_name, data_type, is_nullable, is_identity
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        cols = cur.fetchall()
        if not cols:
            return None

        cur.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema   = kcu.table_schema
            WHERE tc.table_schema = 'public'
              AND tc.table_name   = %s
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
            """,
            (table,),
        )
        pk = [r["column_name"] for r in cur.fetchall()]

    meta = {
        "columns": {c["column_name"]: c for c in cols},
        "colnames": [c["column_name"] for c in cols],
        "pk": pk,
    }
    _meta_cache[table] = meta
    return meta


def coerce(meta, col, value):
    """Приводит значение из JSON к типу столбца."""
    if value is None:
        return None
    dtype = meta["columns"][col]["data_type"]
    try:
        if dtype in INT_TYPES:
            return int(value)
        if dtype in NUM_TYPES:
            return Decimal(str(value))
        if dtype == "boolean":
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("1", "true", "t", "yes", "on")
    except (ValueError, TypeError):
        raise ValueError(
            f"значение поля «{col}» не соответствует типу {dtype}"
        )
    return str(value)


def db_error_response(exc):
    """Преобразует ошибку PostgreSQL в HTTP-ответ."""
    name = type(exc).__name__
    if name in ("UniqueViolation",):
        return json_error(409, "Нарушение уникальности", str(exc).strip())
    if name in ("ForeignKeyViolation", "RestrictViolation"):
        return json_error(409, "Нарушение ссылочной целостности", str(exc).strip())
    if name in ("NotNullViolation", "CheckViolation"):
        return json_error(400, "Нарушение ограничения", str(exc).strip())
    if name in ("InvalidTextRepresentation", "DataError", "NumericValueOutOfRange"):
        return json_error(400, "Недопустимое значение", str(exc).strip())
    if name in ("UndefinedColumn", "UndefinedTable"):
        return json_error(400, "Неизвестный столбец или таблица", str(exc).strip())
    if isinstance(exc, psycopg.OperationalError):
        return json_error(503, "Нет соединения с базой данных", str(exc).strip())
    return json_error(500, "Ошибка базы данных", str(exc).strip())


# ------------------------------------------------------------ авторизация
def _unauthorized(detail=None):
    resp = json_error(401, "Требуется авторизация (Basic Auth)", detail)
    resp[0].headers["WWW-Authenticate"] = 'Basic realm="teatr"'
    return resp


@app.before_request
def open_connection():
    """Проверяет Basic Auth и открывает соединение к БД от имени клиента."""
    if request.path == "/health":
        return None

    auth = request.authorization
    if not auth or not auth.username:
        return _unauthorized()

    try:
        conn = psycopg.connect(
            host=PGHOST,
            port=PGPORT,
            dbname=PGDATABASE,
            user=auth.username,
            password=auth.password,
            connect_timeout=5,
        )
    except psycopg.OperationalError as exc:
        return _unauthorized(str(exc).strip())

    g.conn = conn
    g.db_user = auth.username
    return None


@app.teardown_request
def close_connection(exc):
    conn = getattr(g, "conn", None)
    if conn is not None:
        conn.close()


def resolve_table(resource):
    return RESOURCES.get(resource)


# ------------------------------------------------------------ маршруты
@app.get("/health")
def health():
    return jsonify({"status": "ok", "database": PGDATABASE, "port": PGPORT})


@app.get("/api")
def api_index():
    return jsonify(
        {
            "database": PGDATABASE,
            "resources": RESOURCES,
            "note": "Основной маршрут: /api/<resource>[/<pk>]; "
                    "для составного PK значения через запятую, напр. /api/play_genres/1,2",
        }
    )


@app.route("/api/<resource>", methods=["GET", "POST"])
@app.route("/api/<resource>/<pk>", methods=["GET", "PUT", "PATCH", "DELETE"])
def resource_endpoint(resource, pk=None):
    table = resolve_table(resource)
    if table is None:
        return json_error(404, f"Неизвестный ресурс «{resource}»",
                          f"Доступно: {', '.join(RESOURCES)}")

    meta = load_table_meta(g.conn, table)
    if meta is None:
        return json_error(404, f"Таблица «{table}» не найдена в базе")

    handler = {
        "GET": _handle_get,
        "POST": _handle_post,
        "PUT": _handle_update,
        "PATCH": _handle_update,
        "DELETE": _handle_delete,
    }[request.method]

    try:
        result = handler(table, meta, pk)
        g.conn.commit()
        return result
    except ValueError as exc:
        g.conn.rollback()
        return json_error(400, str(exc))
    except psycopg.Error as exc:
        g.conn.rollback()
        return db_error_response(exc)


# ------------------------------------------------------------ обработчики
def _pk_values(meta, pk):
    """Разбирает значение pk из URL (поддерживает составной ключ)."""
    if pk is None:
        raise ValueError("Не указан первичный ключ")
    raw = pk.split(",")
    if len(raw) != len(meta["pk"]):
        raise ValueError(
            f"Ожидается {len(meta['pk'])} значений PK "
            f"({', '.join(meta['pk'])}) через запятую"
        )
    return {col: coerce(meta, col, val) for col, val in zip(meta["pk"], raw)}


def _pk_where(meta, values):
    clause = sql.SQL(" AND ").join(
        sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder())
        for c in meta["pk"]
    )
    params = [values[c] for c in meta["pk"]]
    return clause, params


def _body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Тело запроса должно быть JSON-объектом")
    return data


def _validate_columns(meta, data):
    unknown = [k for k in data if k not in meta["columns"]]
    if unknown:
        raise ValueError(
            f"Неизвестные столбцы: {', '.join(unknown)}. "
            f"Допустимо: {', '.join(meta['colnames'])}"
        )


def _handle_get(table, meta, pk):
    if pk is None:
        limit = request.args.get("limit", type=int)
        offset = request.args.get("offset", type=int, default=0)

        conditions, params = [], []
        for key, val in request.args.items():
            if key in ("limit", "offset"):
                continue
            if key not in meta["columns"]:
                raise ValueError(f"Неизвестный столбец фильтра «{key}»")
            conditions.append(
                sql.SQL("{} = {}").format(sql.Identifier(key), sql.Placeholder())
            )
            params.append(coerce(meta, key, val))

        query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
        if conditions:
            query += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)
        if meta["pk"]:
            query += sql.SQL(" ORDER BY ") + sql.SQL(", ").join(
                sql.Identifier(c) for c in meta["pk"]
            )
        if limit is not None:
            query += sql.SQL(" LIMIT {}").format(sql.Placeholder())
            params.append(limit)
            query += sql.SQL(" OFFSET {}").format(sql.Placeholder())
            params.append(offset or 0)
        elif offset:
            query += sql.SQL(" OFFSET {}").format(sql.Placeholder())
            params.append(offset)

        with g.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            rows = [row_to_dict(r) for r in cur.fetchall()]
        return jsonify({"resource": table, "count": len(rows), "data": rows})

    # одна запись
    values = _pk_values(meta, pk)
    where, params = _pk_where(meta, values)
    query = sql.SQL("SELECT * FROM {} WHERE {}").format(
        sql.Identifier(table), where
    )
    with g.conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    if row is None:
        return json_error(404, "Запись не найдена")
    return jsonify(row_to_dict(row))


def _handle_post(table, meta, pk):
    data = _body()
    if not data:
        raise ValueError("Пустое тело запроса")
    _validate_columns(meta, data)

    cols = list(data.keys())
    params = [coerce(meta, c, data[c]) for c in cols]

    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in cols),
        sql.SQL(", ").join(sql.Placeholder() for _ in cols),
    )
    with g.conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    return jsonify(row_to_dict(row)), 201


def _handle_update(table, meta, pk):
    data = _body()
    if not data:
        raise ValueError("Пустое тело запроса")
    _validate_columns(meta, data)

    values = _pk_values(meta, pk)
    cols = list(data.keys())
    params = [coerce(meta, c, data[c]) for c in cols]
    where, where_params = _pk_where(meta, values)

    query = sql.SQL("UPDATE {} SET {} WHERE {} RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder())
            for c in cols
        ),
        where,
    )
    with g.conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params + where_params)
        row = cur.fetchone()
    if row is None:
        return json_error(404, "Запись не найдена")
    return jsonify(row_to_dict(row))


def _handle_delete(table, meta, pk):
    values = _pk_values(meta, pk)
    where, params = _pk_where(meta, values)
    query = sql.SQL("DELETE FROM {} WHERE {} RETURNING *").format(
        sql.Identifier(table), where
    )
    with g.conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    if row is None:
        return json_error(404, "Запись не найдена")
    return jsonify({"deleted": row_to_dict(row)})


# ------------------------------------------------------------ запуск
if __name__ == "__main__":
    print(f"REST API: http://{API_HOST}:{API_PORT}/api")
    print(f"База: {PGDATABASE} на {PGHOST}:{PGPORT}. "
          f"Авторизация — как у PostgreSQL (Basic Auth).")
    app.run(host=API_HOST, port=API_PORT, debug=False, threaded=True)
