"""Роли: /api/roles"""
from routes._crud import make_crud_blueprint

# Выборка с JOIN: к роли добавляются название спектакля и имя актёра.
_ROLE_SELECT = """
SELECT r.role_id, r.role_name, r.is_main,
       r.performance_id, p.title AS performance,
       r.actor_id, ac.full_name AS actor
FROM role r
JOIN performance p  ON p.performance_id = r.performance_id
JOIN actor       ac ON ac.actor_id      = r.actor_id
"""

bp = make_crud_blueprint(
    name="roles",
    table="role",
    pk="role_id",
    fields=["role_name", "performance_id", "actor_id", "is_main"],
    required=["role_name", "performance_id", "actor_id"],
    list_sql=_ROLE_SELECT + " ORDER BY r.role_id",
    item_sql=_ROLE_SELECT + " WHERE r.role_id = %s",
)
