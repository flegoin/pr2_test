# -*- coding: utf-8 -*-
"""
Генерация ER-диаграммы БД "Покупка билетов в театр" (упрощённая, 9 таблиц).

Рисуется офлайн средствами Pillow (без внешних сервисов и Graphviz).
Результат: er_diagram.png рядом со скриптом.

Демонстрируются все виды связей:
    * один-ко-многим (1:M)
    * многие-ко-многим (M:M, через связующие таблицы)
    * один-к-одному   (1:1)
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------- параметры
S = 2                       # супер-сэмплинг для сглаживания
IMG_W, IMG_H = 1640, 1240   # базовый размер полотна

W_BOX = 340
HEADER_H = 46
ROW_H = 30

COL_HEADER = {
    "ref":      (41, 87, 141),    # справочники
    "junction": (192, 80, 20),    # связующие таблицы (M:M)
    "core":     (84, 130, 53),    # основные таблицы
    "one2one":  (112, 48, 160),   # 1:1
}
COL_BODY = (247, 247, 247)
COL_BORDER = (55, 55, 55)
COL_ROW_LINE = (215, 215, 215)
COL_TEXT = (20, 20, 20)
COL_TYPE = (105, 105, 105)
COL_EDGE = (70, 70, 70)
COL_LABEL_BG = (255, 255, 255)

BADGE = {
    "PK": (184, 134, 11),
    "FK": (0, 128, 128),
    "U":  (112, 48, 160),
}


# ---------------------------------------------------------------- шрифты
def _font_path(candidates):
    fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for name in candidates:
        p = os.path.join(fonts_dir, name)
        if os.path.exists(p):
            return p
    return None


FONT_REG = _font_path(["segoeui.ttf", "arial.ttf", "calibri.ttf", "tahoma.ttf"])
FONT_BOLD = _font_path(["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "tahomabd.ttf"])
FONT_MONO = _font_path(["consola.ttf", "cour.ttf", "lucon.ttf"])


def font(path, size):
    return ImageFont.truetype(path, size * S) if path else ImageFont.load_default()


# ---------------------------------------------------------------- описание схемы
# Каждая таблица: имя, группа (цвет), позиция (x, y), колонки (имя, тип, ключи)
TABLES = [
    {
        "name": "жанры", "group": "ref", "pos": (60, 100),
        "cols": [
            ("id", "integer", "PK"),
            ("название", "varchar(60)", "U"),
        ],
    },
    {
        "name": "спектакли", "group": "ref", "pos": (620, 490),
        "cols": [
            ("id", "integer", "PK"),
            ("название", "varchar(150)", ""),
            ("описание", "text", ""),
            ("длительность_минут", "integer", ""),
            ("возрастное_ограничение", "smallint", ""),
        ],
    },
    {
        "name": "спектакли_жанры", "group": "junction", "pos": (60, 300),
        "cols": [
            ("спектакль_id", "integer", "PK FK"),
            ("жанр_id", "integer", "PK FK"),
        ],
    },
    {
        "name": "актёры", "group": "ref", "pos": (60, 530),
        "cols": [
            ("id", "integer", "PK"),
            ("фамилия", "varchar(50)", ""),
            ("имя", "varchar(50)", ""),
            ("отчество", "varchar(50)", ""),
            ("звание", "varchar(80)", ""),
        ],
    },
    {
        "name": "актёры_спектакли", "group": "junction", "pos": (60, 850),
        "cols": [
            ("актёр_id", "integer", "PK FK"),
            ("спектакль_id", "integer", "PK FK"),
            ("роль", "varchar(80)", ""),
        ],
    },
    {
        "name": "залы", "group": "ref", "pos": (1180, 400),
        "cols": [
            ("id", "integer", "PK"),
            ("название", "varchar(80)", ""),
            ("количество_мест", "integer", ""),
            ("этаж", "smallint", ""),
        ],
    },
    {
        "name": "места", "group": "core", "pos": (1180, 720),
        "cols": [
            ("id", "integer", "PK"),
            ("зал_id", "integer", "FK"),
            ("ряд", "smallint", ""),
            ("номер", "smallint", ""),
            ("категория", "varchar(40)", ""),
        ],
    },
    {
        "name": "показы", "group": "core", "pos": (620, 960),
        "cols": [
            ("id", "integer", "PK"),
            ("спектакль_id", "integer", "FK"),
            ("зал_id", "integer", "FK"),
            ("дата_время", "timestamp", ""),
            ("базовая_цена", "numeric(10,2)", ""),
        ],
    },
    {
        "name": "паспорта_залов", "group": "one2one", "pos": (1180, 100),
        "cols": [
            ("id", "integer", "PK"),
            ("зал_id", "integer", "FK U"),
            ("площадь", "numeric(8,2)", ""),
            ("высота_сцены", "numeric(4,2)", ""),
            ("год_постройки", "smallint", ""),
        ],
    },
]

BY_NAME = {t["name"]: t for t in TABLES}
for t in TABLES:
    t["w"] = W_BOX
    t["h"] = HEADER_H + len(t["cols"]) * ROW_H


# ---------------------------------------------------------------- связи
# waypoints — промежуточные точки (в базовых координатах), label — подпись линии
EDGES = [
    {"f": "жанры", "fa": "bottom", "t": "спектакли_жанры", "ta": "top",
     "wp": [], "label": "1:M", "lp": (238, 246)},
    {"f": "спектакли_жанры", "fa": "right", "t": "спектакли", "ta": "left",
     "wp": [(520, None), (520, 540)], "label": "M:1", "lp": (432, 338)},
    {"f": "актёры", "fa": "bottom", "t": "актёры_спектакли", "ta": "top",
     "wp": [], "label": "1:M", "lp": (238, 786)},
    {"f": "актёры_спектакли", "fa": "right", "t": "спектакли", "ta": "left",
     "wp": [(520, None), (520, 612)], "label": "M:1", "lp": (432, 900)},
    {"f": "спектакли", "fa": "bottom", "t": "показы", "ta": "top",
     "wp": [], "label": "1:M", "lp": (800, 826)},
    {"f": "залы", "fa": "bottom", "t": "места", "ta": "top",
     "wp": [], "label": "1:M", "lp": (1360, 632)},
    {"f": "залы", "fa": "top", "t": "паспорта_залов", "ta": "bottom",
     "wp": [], "label": "1:1", "lp": (1360, 340)},
    {"f": "залы", "fa": "left", "t": "показы", "ta": "right",
     "wp": [(1070, None), (1070, 1058)], "label": "1:M", "lp": (1080, 760)},
]

# Подписи под связующими таблицами
JUNCTION_NOTES = [
    ("спектакли_жанры", "связь M:M"),
    ("актёры_спектакли", "связь M:M"),
]


# ---------------------------------------------------------------- геометрия
def anchor(t, side):
    x, y, w, h = t["pos"][0], t["pos"][1], t["w"], t["h"]
    if side == "top":
        return (x + w / 2, y)
    if side == "bottom":
        return (x + w / 2, y + h)
    if side == "left":
        return (x, y + h / 2)
    if side == "right":
        return (x + w, y + h / 2)
    raise ValueError(side)


def build_points(edge):
    p0 = anchor(BY_NAME[edge["f"]], edge["fa"])
    p1 = anchor(BY_NAME[edge["t"]], edge["ta"])
    pts = [p0]
    for wx, wy in edge["wp"]:
        if wx is None:
            wx = pts[-1][0]
        if wy is None:
            wy = pts[-1][1]
        pts.append((wx, wy))
    pts.append(p1)
    return [(x * S, y * S) for (x, y) in pts]


# ---------------------------------------------------------------- рисование
def main():
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "er_diagram.png")

    img = Image.new("RGB", (IMG_W * S, IMG_H * S), (255, 255, 255))
    d = ImageDraw.Draw(img)

    f_title = font(FONT_BOLD, 26)
    f_sub = font(FONT_REG, 15)
    f_head = font(FONT_BOLD, 17)
    f_col = font(FONT_REG, 15)
    f_type = font(FONT_MONO, 13)
    f_badge = font(FONT_BOLD, 12)
    f_edge = font(FONT_BOLD, 13)
    f_note = font(FONT_REG, 13)
    f_leg_t = font(FONT_BOLD, 15)
    f_leg = font(FONT_REG, 14)

    # ---- связи рисуем первыми (под блоками)
    for edge in EDGES:
        pts = build_points(edge)
        d.line(pts, fill=COL_EDGE, width=2 * S, joint="curve")

        # наконечник стрелки
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        dx, dy = x1 - x0, y1 - y0
        length = (dx * dx + dy * dy) ** 0.5 or 1
        ux, uy = dx / length, dy / length
        a = 9 * S
        b = 4 * S
        base_x, base_y = x1 - ux * a, y1 - uy * a
        perp_x, perp_y = -uy, ux
        tri = [
            (x1, y1),
            (base_x + perp_x * b, base_y + perp_y * b),
            (base_x - perp_x * b, base_y - perp_y * b),
        ]
        d.polygon(tri, fill=COL_EDGE)

        # подпись
        lx, ly = edge["lp"]
        lx, ly = lx * S, ly * S
        w = d.textlength(edge["label"], font=f_edge)
        d.rectangle([lx - 5 * S, ly - 10 * S, lx + w + 5 * S, ly + 6 * S],
                    fill=COL_LABEL_BG)
        d.text((lx, ly - 8 * S), edge["label"], font=f_edge, fill=(160, 30, 30))

    # ---- таблицы
    for t in TABLES:
        x, y = t["pos"][0] * S, t["pos"][1] * S
        w, h = t["w"] * S, t["h"] * S
        head_col = COL_HEADER[t["group"]]

        # тело
        d.rounded_rectangle([x, y, x + w, y + h], radius=8 * S,
                            fill=COL_BODY, outline=COL_BORDER, width=2 * S)
        # шапка
        d.rounded_rectangle([x, y, x + w, y + HEADER_H * S], radius=8 * S,
                            fill=head_col)
        d.rectangle([x, y + (HEADER_H - 10) * S, x + w, y + HEADER_H * S],
                    fill=head_col)
        # заголовок
        tw = d.textlength(t["name"], font=f_head)
        d.text((x + w / 2 - tw / 2, y + 11 * S), t["name"], font=f_head,
               fill=(255, 255, 255))

        # строки колонок
        for i, (cname, ctype, keys) in enumerate(t["cols"]):
            ry = y + HEADER_H * S + i * ROW_H * S
            if i > 0:
                d.line([(x + 1, ry), (x + w - 1, ry)], fill=COL_ROW_LINE,
                       width=1 * S)
            d.text((x + 12 * S, ry + 7 * S), cname, font=f_col, fill=COL_TEXT)

            # тип (справа)
            tww = d.textlength(ctype, font=f_type)
            d.text((x + w - 12 * S - tww, ry + 8 * S), ctype, font=f_type,
                   fill=COL_TYPE)

            # бейджи ключей (левее типа)
            if keys:
                tokens = keys.split()
                bx = x + w - 12 * S - tww - 10 * S
                for tok in reversed(tokens):
                    bw = d.textlength(tok, font=f_badge) + 12 * S
                    bx -= bw
                    col = BADGE.get(tok, (90, 90, 90))
                    d.rounded_rectangle(
                        [bx, ry + 5 * S, bx + bw, ry + ROW_H * S - 5 * S],
                        radius=4 * S, fill=col)
                    d.text((bx + 6 * S, ry + 8 * S), tok, font=f_badge,
                           fill=(255, 255, 255))
                    bx -= 4 * S

        # примечание под связующей таблицей
        for tname, note in JUNCTION_NOTES:
            if tname == t["name"]:
                d.text((x + 4 * S, y + h + 6 * S), note, font=f_note,
                       fill=head_col)

    # ---- заголовок
    d.text((60 * S, 22 * S),
           "Схема базы данных «Покупка билетов в театр»",
           font=f_title, fill=(20, 20, 20))
    d.text((60 * S, 62 * S),
           "PostgreSQL • БД teatr • 9 таблиц • связи 1:M, M:M, 1:1",
           font=f_sub, fill=(90, 90, 90))

    # ---- легенда
    lx, ly = 620, 120
    lw, lh = 360, 330
    d.rounded_rectangle([lx * S, ly * S, (lx + lw) * S, (ly + lh) * S],
                        radius=8 * S, fill=(252, 252, 252),
                        outline=(200, 200, 200), width=2 * S)
    d.text((lx * S + 16 * S, ly * S + 14 * S), "Условные обозначения",
           font=f_leg_t, fill=(20, 20, 20))

    items = [
        ("PK", "первичный ключ"),
        ("FK", "внешний ключ"),
        ("U", "уникальное поле (связь 1:1)"),
    ]
    ey = ly * S + 46 * S
    for tok, desc in items:
        bw = d.textlength(tok, font=f_badge) + 12 * S
        d.rounded_rectangle([lx * S + 18 * S, ey, lx * S + 18 * S + bw, ey + 20 * S],
                            radius=4 * S, fill=BADGE[tok])
        d.text((lx * S + 24 * S, ey + 3 * S), tok, font=f_badge, fill=(255, 255, 255))
        d.text((lx * S + 18 * S + bw + 10 * S, ey + 1 * S), desc, font=f_leg,
               fill=(40, 40, 40))
        ey += 30 * S

    ey += 8 * S
    rels = [
        ("1:M", "один-ко-многим"),
        ("M:M", "многие-ко-многим (через связующие таблицы)"),
        ("1:1", "один-к-одному"),
    ]
    for tok, desc in rels:
        d.text((lx * S + 18 * S, ey), tok, font=f_edge, fill=(160, 30, 30))
        d.text((lx * S + 64 * S, ey), desc, font=f_leg, fill=(40, 40, 40))
        ey += 28 * S

    img = img.resize((IMG_W, IMG_H), Image.LANCZOS)
    img.save(out_path, "PNG")
    print("OK ->", out_path, img.size)


if __name__ == "__main__":
    main()
