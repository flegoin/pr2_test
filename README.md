# Театр — база данных и REST API

Учебный проект: база данных PostgreSQL «Покупка билетов в театр» (9 таблиц,
связи 1:M, M:M, 1:1) и REST-сервер на Flask для CRUD-доступа к данным.

## Структура проекта

```
pr2\
  database\              база данных и схема
    schema.sql           структура таблиц
    data.sql             тестовые данные (>=10 строк на таблицу)
    reset_db.sql         сброс и восстановление БД
    generate_er_diagram.py  генератор ER-диаграммы
    er_diagram.png       изображение схемы
    er_diagram.mmd       исходник диаграммы (Mermaid)
  server\                REST API
    rest_api.py          Flask-сервер (порт 8080)
    requirements.txt     зависимости Python
    start.ps1            скрипт запуска
    API.md               полное описание API
  README.md              этот файл
```

## Требования

- **PostgreSQL 18** (сервер запущен, стандартный порт **5432**)
- **Python 3.13** и `pip`

Параметры подключения к БД по умолчанию:

| Параметр | Значение |
|----------|----------|
| Хост | `localhost` |
| Порт | `5432` |
| База | `teatr` |
| Пользователь | `postgres` |
| Пароль | `12345678` |

## Запуск сервера

### 1. Восстановить базу данных

```powershell
psql -U postgres -h localhost -p 5432 -d postgres -f database\reset_db.sql
```

Скрипт удаляет прежнюю базу `teatr`, создаёт её заново и наполняет данными.
(Если `psql` не в PATH, используйте полный путь:
`"C:\Program Files\PostgreSQL\18\bin\psql.exe"`.)

### 2. Установить зависимости Python

```powershell
python -m pip install -r server\requirements.txt
```

### 3. Запустить REST-сервер

```powershell
python server\rest_api.py
```

или

```powershell
.\server\start.ps1
```

Сервер поднимется на **http://127.0.0.1:8080**.

### Параметры через переменные окружения (необязательно)

| Переменная | По умолчанию |
|------------|--------------|
| `PGHOST` | `localhost` |
| `PGPORT` | `5432` |
| `PGDATABASE` | `teatr` |
| `API_HOST` | `127.0.0.1` |
| `API_PORT` | `8080` |

## Авторизация

API использует **HTTP Basic Auth** с учётными данными PostgreSQL.
Логин и пароль совпадают с пользователем БД (`postgres` / `12345678`).
Без авторизации или с неверными данными возвращается `401`.

## Проверка работы

```powershell
# без авторизации (не требует логина)
curl.exe http://127.0.0.1:8080/health

# список спектаклей
curl.exe -u postgres:12345678 http://127.0.0.1:8080/api/plays
```

Полный список эндпоинтов, ресурсов и примеры запросов — в
[`server/API.md`](server/API.md).
