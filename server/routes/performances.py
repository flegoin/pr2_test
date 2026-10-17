"""Спектакли: /api/performances (+ актёрский состав)."""
from flask import jsonify

from db import get_cursor
from routes._crud import make_crud_blueprint

# Выборка с JOIN: к спектаклю добавляются названия жанра и автора.
_PERF_SELECT = """
SELECT p.performance_id, p.title,
       p.genre_id, g.name      AS genre,
       p.author_id, a.full_name AS author,
       p.premiere_date, p.duration_min, p.age_limit
FROM performance p
JOIN genre  g ON g.genre_id  = p.genre_id
JOIN author a ON a.author_id = p.author_id
"""

bp = make_crud_blueprint(
    name="performances",
    table="performance",
    pk="performance_id",
    fields=["title", "genre_id", "author_id", "premiere_date", "duration_min", "age_limit"],
    required=["title", "genre_id", "author_id", "premiere_date", "duration_min", "age_limit"],
    list_sql=_PERF_SELECT + " ORDER BY p.performance_id",
    item_sql=_PERF_SELECT + " WHERE p.performance_id = %s",
)


@bp.get("/<int:performance_id>/roles")
def performance_roles(performance_id):
    """Актёрский состав конкретного спектакля."""
    sql = """
    SELECT r.role_id, r.role_name, r.is_main,
           r.actor_id, ac.full_name AS actor
    FROM role r
    JOIN actor ac ON ac.actor_id = r.actor_id
    WHERE r.performance_id = %s
    ORDER BY r.role_id
    """
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM performance WHERE performance_id = %s", (performance_id,))
        if cur.fetchone() is None:
            return jsonify({"error": "not_found", "id": performance_id}), 404
        cur.execute(sql, (performance_id,))
        return jsonify(cur.fetchall())
