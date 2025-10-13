#!/bin/bash

# Script helper para gerenciar o Integrador via Docker

set -e

case "$1" in
    start)
        echo "🚀 Iniciando Integrador..."
        docker-compose up -d
        echo "✅ Integrador iniciado!"
        echo "🌐 Acesse: http://localhost:8000"
        ;;
    
    stop)
        echo "🛑 Parando Integrador..."
        docker-compose down
        echo "✅ Integrador parado!"
        ;;
    
    restart)
        echo "🔄 Reiniciando Integrador..."
        docker-compose restart
        echo "✅ Integrador reiniciado!"
        ;;
    
    build)
        echo "🏗️  Rebuilding Integrador..."
        docker-compose up --build -d
        echo "✅ Build completo!"
        ;;
    
    logs)
        docker-compose logs -f ${2:-web}
        ;;
    
    shell)
        docker-compose exec web python manage.py shell
        ;;
    
    bash)
        docker-compose exec web bash
        ;;
    
    migrate)
        echo "📦 Executando migrações..."
        docker-compose exec web python manage.py migrate
        ;;
    
    makemigrations)
        echo "📝 Criando migrações..."
        docker-compose exec web python manage.py makemigrations
        ;;
    
    test)
        echo "🧪 Executando testes..."
        docker-compose exec web python manage.py test ${2}
        ;;
    
    createsuperuser)
        docker-compose exec web python manage.py createsuperuser
        ;;
    
    collectstatic)
        docker-compose exec web python manage.py collectstatic --noinput
        ;;
    
    clean)
        echo "🧹 Limpando containers e volumes..."
        docker-compose down -v
        echo "✅ Limpeza completa!"
        ;;
    
    status)
        docker-compose ps
        ;;
    
    *)
        echo "🚚 Integrador - Docker Helper"
        echo ""
        echo "Comandos disponíveis:"
        echo "  start          - Iniciar containers"
        echo "  stop           - Parar containers"
        echo "  restart        - Reiniciar containers"
        echo "  build          - Rebuild e iniciar"
        echo "  logs [serviço] - Ver logs (web, celery, redis, db)"
        echo "  shell          - Django shell"
        echo "  bash           - Terminal bash no container"
        echo "  migrate        - Executar migrações"
        echo "  makemigrations - Criar migrações"
        echo "  test [app]     - Executar testes"
        echo "  createsuperuser - Criar superusuário"
        echo "  collectstatic  - Coletar arquivos estáticos"
        echo "  clean          - Limpar containers e volumes"
        echo "  status         - Ver status dos containers"
        echo ""
        echo "Exemplos:"
        echo "  ./docker.sh start"
        echo "  ./docker.sh logs celery"
        echo "  ./docker.sh test apps.monitoring"
        ;;
esac
