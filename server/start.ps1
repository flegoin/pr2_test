# Запуск REST API сервера (порт 8080).
# При необходимости сначала установите зависимости:
#   python -m pip install -r requirements.txt

$env:PGHOST     = if ($env:PGHOST)     { $env:PGHOST }     else { "localhost" }
$env:PGPORT     = if ($env:PGPORT)     { $env:PGPORT }     else { "5432" }
$env:PGDATABASE = if ($env:PGDATABASE) { $env:PGDATABASE } else { "teatr" }
$env:API_HOST   = if ($env:API_HOST)   { $env:API_HOST }   else { "127.0.0.1" }
$env:API_PORT   = if ($env:API_PORT)   { $env:API_PORT }   else { "8080" }

Write-Host "Старт REST API на http://$($env:API_HOST):$($env:API_PORT)/api"
python "$PSScriptRoot\rest_api.py"
