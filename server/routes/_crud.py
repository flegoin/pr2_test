"""Универсальная фабрика CRUD-эндпоинтов для таблиц PostgreSQL.

Для каждого ресурса создаётся Blueprint с маршрутами:
    GET    /api/<name>            — список
    POST   /api/<name>            — создание
    GET    /api/<name>/<id>       — чтение
    PUT    /api/<name>/<id>       — полное обновление
    PATCH  /api/<name>/<id>       — частичное обновление
    DELETE /api/<name>/<id>       — удаление
"""
from flask import Blueprint, jsonify, request

from db import get_cursor


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def make_crud_blueprint(
    *,
    name: str,
    table: str,
    pk: str,
    fields: list,
    required: tuple = (),
    list_sql: str = None,
    item_sql: str = None,
    order_by: str = None,
) -> Blueprint:
    bp = Blueprint(name, __name__, url_prefix=f"/api/{name}")

    list_query = list_sql or (
        f"SELECT * FROM {table}" + (f" ORDER BY {order_by}" if order_by else "")
    )
    item_query = item_sql or f"SELECT * FROM {table} WHERE {pk} = %s"

    @bp.get("")
    def list_items():
        with get_cursor() as cur:
            cur.execute(list_query)
            return jsonify(cur.fetchall())

    @bp.get("/<int:item_id>")
    def get_item(item_id):
        with get_cursor() as cur:
            cur.execute(item_query, (item_id,))
            row = cur.fetchone()
        if row is None:
            return jsonify({"error": "not_found", "id": item_id}), 404
        return jsonify(row)

    @bp.post("")
    def create_item():
        data = _json_body()
        missing = [f for f in required if data.get(f) in (None, "")]
        if missing:
            return jsonify({"error": "validation_error", "missing": missing}), 400
        cols = [f for f in fields if f in data]
        if not cols:
            return jsonify({"error": "validation_error", "message": "no fields provided"}), 400
        placeholders = ", ".join(["%s"] * len(cols))
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) "
            f"VALUES ({placeholders}) RETURNING *"
        )
        with get_cursor() as cur:
            cur.execute(sql, [data[c] for c in cols])
            row = cur.fetchone()
        return jsonify(row), 201

    @bp.put("/<int:item_id>")
    @bp.patch("/<int:item_id>")
    def update_item(item_id):
        data = _json_body()
        cols = [f for f in fields if f in data]
        if not cols:
            return jsonify({"error": "validation_error", "message": "no fields provided"}), 400
        assignments = ", ".join(f"{c} = %s" for c in cols)
        sql = f"UPDATE {table} SET {assignments} WHERE {pk} = %s RETURNING *"
        with get_cursor() as cur:
            cur.execute(sql, [data[c] for c in cols] + [item_id])
            row = cur.fetchone()
        if row is None:
            return jsonify({"error": "not_found", "id": item_id}), 404
        return jsonify(row)

    @bp.delete("/<int:item_id>")
    def delete_item(item_id):
        with get_cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE {pk} = %s RETURNING {pk}", (item_id,))
            row = cur.fetchone()
        if row is None:
            return jsonify({"error": "not_found", "id": item_id}), 404
        return "", 204

    return bp
