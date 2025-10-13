@echo off
REM Script para gerenciar o Integrador via Docker no Windows

if "%1"=="start" (
    echo 🚀 Iniciando Integrador...
    docker-compose up -d
    echo ✅ Integrador iniciado!
    echo 🌐 Acesse: http://localhost:8000
    goto :eof
)

if "%1"=="stop" (
    echo 🛑 Parando Integrador...
    docker-compose down
    echo ✅ Integrador parado!
    goto :eof
)

if "%1"=="build" (
    echo 🏗️ Building Integrador...
    docker-compose up --build
    goto :eof
)

if "%1"=="logs" (
    if "%2"=="" (
        docker-compose logs -f
    ) else (
        docker-compose logs -f %2
    )
    goto :eof
)

if "%1"=="status" (
    docker-compose ps
    goto :eof
)

if "%1"=="shell" (
    docker-compose exec web python manage.py shell
    goto :eof
)

if "%1"=="bash" (
    docker-compose exec web bash
    goto :eof
)

if "%1"=="migrate" (
    echo 📦 Executando migrações...
    docker-compose exec web python manage.py migrate
    goto :eof
)

if "%1"=="clean" (
    echo 🧹 Limpando containers e volumes...
    docker-compose down -v
    echo ✅ Limpeza completa!
    goto :eof
)

echo 🚚 Integrador - Docker Helper (Windows)
echo.
echo Comandos disponíveis:
echo   start   - Iniciar containers
echo   stop    - Parar containers
echo   build   - Build e iniciar (primeira vez ou após mudanças)
echo   logs    - Ver logs (opcional: logs web, logs celery)
echo   status  - Ver status dos containers
echo   shell   - Django shell
echo   bash    - Terminal bash no container
echo   migrate - Executar migrações
echo   clean   - Limpar tudo (CUIDADO: apaga dados!)
echo.
echo Exemplos:
echo   docker.bat start
echo   docker.bat logs web
echo   docker.bat build
