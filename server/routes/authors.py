"""Авторы: /api/authors"""
from routes._crud import make_crud_blueprint

bp = make_crud_blueprint(
    name="authors",
    table="author",
    pk="author_id",
    fields=["full_name", "country", "birth_year"],
    required=["full_name"],
    order_by="author_id",
)
