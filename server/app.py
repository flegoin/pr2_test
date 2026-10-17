"""REST-сервер «Спектакли в театре» (Flask + PostgreSQL).

Запуск:
    python app.py            # хост и порт берутся из .env (по умолчанию 127.0.0.1:3000)
"""
import datetime

import psycopg
from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider

from config import Config
from db import get_cursor
from routes import register_blueprints


class ISOJSONProvider(DefaultJSONProvider):
    """Сериализует date/datetime в ISO 8601 (а не в HTTP-формат)."""

    @staticmethod
    def default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return DefaultJSONProvider.default(o)


class App(Flask):
    json_provider_class = ISOJSONProvider


def create_app() -> Flask:
    app = App(__name__)
    register_blueprints(app)

    @app.get("/api/health")
    def health():
        with get_cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()
        return jsonify({"status": "ok", "database": Config.PGDATABASE})

    @app.errorhandler(psycopg.errors.IntegrityError)
    def on_integrity(e):
        return jsonify({"error": "integrity_error", "detail": str(e).strip()}), 409

    @app.errorhandler(psycopg.errors.DataError)
    def on_data(e):
        return jsonify({"error": "bad_request", "detail": str(e).strip()}), 400

    @app.errorhandler(psycopg.Error)
    def on_db(e):
        return jsonify({"error": "database_error", "detail": str(e).strip()}), 500

    @app.errorhandler(404)
    def on_404(e):
        return jsonify({"error": "not_found"}), 404

    @app.errorhandler(405)
    def on_405(e):
        return jsonify({"error": "method_not_allowed"}), 405

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=Config.SERVER_HOST,
        port=Config.SERVER_PORT,
        debug=Config.DEBUG,
        use_reloader=False,
    )
