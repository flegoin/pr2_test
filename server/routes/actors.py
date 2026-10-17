"""Актёры: /api/actors"""
from routes._crud import make_crud_blueprint

bp = make_crud_blueprint(
    name="actors",
    table="actor",
    pk="actor_id",
    fields=["full_name", "birth_date", "experience_years"],
    required=["full_name", "birth_date", "experience_years"],
    order_by="actor_id",
)
