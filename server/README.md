# Сервер «Спектакли в театре» (Flask + PostgreSQL)

REST-сервис над базой данных театральных спектаклей (см. `../database/theater.sql`).
Стек: **Python 3.13**, **Flask 3**, **psycopg 3**, СУБД **PostgreSQL**.

## Структура

```
server/
├── app.py              # точка входа: создание приложения, обработчики ошибок
├── config.py           # конфиг из переменных окружения / .env
├── db.py               # подключение к PostgreSQL (psycopg 3)
├── routes/
│   ├── __init__.py     # регистрация blueprint'ов
│   ├── _crud.py        # универсальная фабрика CRUD-маршрутов
│   ├── genres.py       # /api/genres
│   ├── authors.py      # /api/authors
│   ├── actors.py       # /api/actors
│   ├── performances.py # /api/performances (+ /roles)
│   └── roles.py        # /api/roles
├── requirements.txt
├── .env                # локальные настройки (включая пароль БД)
└── .env.example        # шаблон без секрета
```

## Как поднять сервер

### Что нужно заранее
- **Python 3.10+** (проверено на 3.13);
- **PostgreSQL**, запущенный локально (по умолчанию `localhost:5432`) — проверено на 18;
- утилиты `psql` и `createdb` в `PATH`. Если их нет, используйте полный путь,
  например `"C:\Program Files\PostgreSQL\18\bin\psql.exe"`.

> Все команды выполняются из папки `server` (в ней `app.py` и `.env`).

### Шаг 1. Перейти в папку сервера
```powershell
cd server
```

### Шаг 2. (по желанию) создать виртуальное окружение
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Шаг 3. Установить зависимости
```powershell
python -m pip install -r requirements.txt      # Flask, psycopg[binary]
```

### Шаг 4. Проверить настройки подключения в `.env`
Файл `server/.env` уже создан. При необходимости поправьте хост/порт/базу/пароль:
```ini
PGHOST=localhost
PGPORT=5432
PGDATABASE=theater
PGUSER=postgres
PGPASSWORD=12345678
SERVER_HOST=127.0.0.1
SERVER_PORT=3000
FLASK_DEBUG=0
```

### Шаг 5. Подготовить базу данных (один раз)
Если БД `theater` ещё нет — создайте её и загрузите схему с данными:
```powershell
$env:PGPASSWORD = "12345678"                     # пароль пользователя postgres

createdb -U postgres theater
psql -U postgres -d theater -f ..\database\theater.sql
```
Должно выполниться 5 `CREATE TABLE` и 5 `INSERT 0 10`.

### Шаг 6. Запустить сервер
```powershell
python app.py
```
Ожидаемый вывод:
```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:3000
```

### Шаг 7. Проверить, что сервер поднялся
```powershell
curl.exe http://127.0.0.1:3000/api/health
# {"status":"ok","database":"theater"}
```
Либо средствами PowerShell:
```powershell
Invoke-RestMethod http://127.0.0.1:3000/api/health
(Invoke-RestMethod http://127.0.0.1:3000/api/performances).Count   # 10
```

### Шаг 8. Остановить сервер
Нажмите **Ctrl+C** в окне, где запущен `python app.py`.

### Запуск на другом порту
Измените `SERVER_PORT` в `.env` и перезапустите:
```powershell
# server\.env
SERVER_PORT=3001
```
Освободить занятый порт (если нужно):
```powershell
Get-NetTCPConnection -LocalPort 3000 -State Listen |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

> Сервер использует встроенный сервер Flask — он подходит для разработки/тестирования.
> Для «боевого» запуска применяйте WSGI-сервер, например:
> `pip install waitress` и `waitress-serve --host 127.0.0.1 --port 3000 app:app`.

## Эндпоинты

| Метод и путь | Действие |
|---|---|
| `GET /api/health` | проверка соединения с БД |
| `GET /api/genres` | список жанров |
| `POST /api/genres` | создать жанр |
| `GET /api/genres/<id>` | один жанр |
| `PUT`/`PATCH`/`DELETE /api/genres/<id>` | изменить / удалить |
| ... | то же для `authors`, `actors`, `performances`, `roles` |
| `GET /api/performances` | спектакли с жанром и автором (JOIN) |
| `GET /api/performances/<id>/roles` | актёрский состав спектакля |
| `GET /api/roles` | роли с названием спектакля и актёром (JOIN) |

## Формат данных

Тело запроса и ответ — JSON. Примеры:

```bash
# создать жанр
curl -X POST http://127.0.0.1:3000/api/genres \
     -H "Content-Type: application/json" \
     -d '{"name": "Драма"}'

# создать спектакль
curl -X POST http://127.0.0.1:3000/api/performances \
     -H "Content-Type: application/json" \
     -d '{"title":"Вишнёвый сад","genre_id":1,"author_id":1,
          "premiere_date":"1904-01-17","duration_min":180,"age_limit":16}'

# частичное обновление
curl -X PATCH http://127.0.0.1:3000/api/performances/1 \
     -H "Content-Type: application/json" -d '{"duration_min":170}'
```

## Коды ответов

| Код | Когда |
|---|---|
| `200` | успешное чтение/обновление |
| `201` | создано |
| `204` | удалено (без тела) |
| `400` | не переданы обязательные поля / некорректный тип (`validation_error`, `bad_request`) |
| `404` | запись не найдена (`not_found`) |
| `409` | нарушение ограничений БД: FK/UNIQUE/CHECK (`integrity_error`) |
| `500` | прочие ошибки БД (`database_error`) |

## Безопасность

Все SQL-запросы **параметризованы** (`%s`), значения подставляет драйвер —
конкатенации пользовательских данных в SQL нет, инъекции исключены.
