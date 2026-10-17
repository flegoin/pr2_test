"""Жанры: /api/genres"""
from routes._crud import make_crud_blueprint

bp = make_crud_blueprint(
    name="genres",
    table="genre",
    pk="genre_id",
    fields=["name"],
    required=["name"],
    order_by="genre_id",
)
