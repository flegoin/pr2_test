-- ============================================================
-- Скрипт сброса и восстановления БД "Покупка билетов в театр"
-- Что делает:
--   1) удаляет базу teatr, если она существует;
--   2) создаёт базу teatr заново (UTF-8);
--   3) подключается к ней;
--   4) применяет schema.sql (структура);
--   5) применяет data.sql  (данные).
--
-- Запуск (из папки со скриптами):
--   psql -U postgres -h localhost -p 5432 -d postgres -f reset_db.sql
--
-- Порт по умолчанию PostgreSQL — 5432.
-- ============================================================

SET client_encoding = 'UTF8';

-- 1) Полный сброс базы
DROP DATABASE IF EXISTS teatr WITH (FORCE);

-- 2) Создание базы
CREATE DATABASE teatr WITH ENCODING 'UTF8' TEMPLATE template0;

-- 3) Переключение на созданную базу
\connect teatr

SET client_encoding = 'UTF8';

-- 4) Структура
\ir schema.sql

-- 5) Данные
\ir data.sql

-- Итог
SELECT 'База teatr успешно сброшена и восстановлена.' AS результат;
