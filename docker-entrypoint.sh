#!/bin/bash

set -e

echo "🚀 Iniciando Integrador..."

# Aguardar PostgreSQL estar pronto
echo "⏳ Aguardando PostgreSQL..."
while ! pg_isready -h db -p 5432 -U postgres; do
  sleep 1
done
echo "✅ PostgreSQL pronto!"

# Aguardar Redis estar pronto (skip - Redis já está UP)
echo "⏳ Aguardando Redis..."
sleep 3
echo "✅ Redis pronto! (assumido)"# Executar migrações
echo "📦 Executando migrações..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Criar superusuário se não existir
echo "👤 Verificando superusuário..."
python manage.py shell -c "
from apps.authentication.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@integrador.com', 'admin123', user_type='GR')
    print('✅ Superusuário criado: admin / admin123')
else:
    print('✅ Superusuário já existe')
"

echo "🎉 Integrador pronto!"

# Executar comando passado como argumento
exec "$@"
