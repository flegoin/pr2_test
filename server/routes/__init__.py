"""Маршруты API: жанры, авторы, актёры, спектакли, роли."""
from flask import Flask

from routes.actors import bp as actors_bp
from routes.authors import bp as authors_bp
from routes.genres import bp as genres_bp
from routes.performances import bp as performances_bp
from routes.roles import bp as roles_bp


def register_blueprints(app: Flask) -> None:
    for bp in (genres_bp, authors_bp, actors_bp, performances_bp, roles_bp):
        app.register_blueprint(bp)
