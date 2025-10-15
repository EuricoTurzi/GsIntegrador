# 🚀 Guia de Setup para Desenvolvimento

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Git configurado
- Editor de código (recomendado: VS Code)

## 🔧 Configuração Inicial

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd Integrador
```

### 2. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_NAME=integrador_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=db
DATABASE_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Suntech API
SUNTECH_API_URL=https://api.suntech.com.br
SUNTECH_API_KEY=your-api-key
SUNTECH_API_SECRET=your-api-secret

# OpenRouteService
OPENROUTESERVICE_API_KEY=your-ors-api-key
```

### 3. Inicie os containers Docker

**Windows:**

```bash
docker-compose up -d
```

**Linux/Mac:**

```bash
./docker.sh up
```

### 4. Execute as migrations

```bash
docker-compose exec web python manage.py migrate
```

### 5. Crie um superusuário

```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Acesse a aplicação

- **Frontend**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/

## 🏗️ Estrutura do Projeto

```
integrador/
├── apps/                    # Apps Django
│   ├── authentication/      # Sistema de autenticação
│   ├── devices/            # Gerenciamento de rastreadores
│   ├── drivers/            # Cadastro de motoristas
│   ├── integrations/       # Integrações externas (Suntech, ORS)
│   ├── monitoring/         # Sistema de monitoramento em tempo real
│   ├── routes/             # Gerenciamento de rotas
│   └── vehicles/           # Cadastro de veículos
├── integrador/             # Configurações Django
├── templates/              # Templates HTML
├── static/                 # Arquivos estáticos
├── docker-compose.yml      # Orquestração de containers
└── requirements.txt        # Dependências Python
```

## 🔑 Funcionalidades Principais

### 1. **Sistema de Autenticação**

- Login/Registro de usuários
- Tipos de usuário: GR (Admin) e Transportadora
- Perfil de usuário e gerenciamento

### 2. **Monitoramento em Tempo Real**

- WebSocket para atualizações em tempo real
- Detecção de desvios de rota (alerta a cada 2 minutos se continuar desviado)
- Detecção de paradas prolongadas (alerta após 5 minutos parado)
- Mapas interativos com Leaflet.js
- Histórico de posições

### 3. **Gerenciamento**

- Motoristas
- Veículos
- Rastreadores (devices)
- Rotas (com integração OpenRouteService)

### 4. **Integrações**

- **Suntech**: Sincronização de dados de rastreadores
- **OpenRouteService**: Cálculo de rotas

## 🛠️ Comandos Úteis

### Docker

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f [web|celery|celery-beat|redis|db]

# Reiniciar um serviço
docker-compose restart [service-name]

# Parar todos os serviços
docker-compose down

# Rebuild após mudanças no Dockerfile
docker-compose up -d --build
```

### Django

```bash
# Executar migrations
docker-compose exec web python manage.py migrate

# Criar migrations
docker-compose exec web python manage.py makemigrations

# Shell Django
docker-compose exec web python manage.py shell

# Coletar arquivos estáticos
docker-compose exec web python manage.py collectstatic --noinput
```

### Celery

```bash
# Ver tarefas em execução
docker-compose exec celery celery -A integrador inspect active

# Ver workers
docker-compose exec celery celery -A integrador inspect stats

# Purgar fila de tarefas
docker-compose exec celery celery -A integrador purge
```

## 🧪 Sistema de Monitoramento

### Alertas Implementados

1. **Desvio de Rota**

   - Primeiro alerta: "Veículo desviou da rota"
   - Alertas contínuos: A cada 2 minutos se continuar desviado
   - Alerta de retorno: "Veículo retornou à rota"

2. **Paradas Prolongadas**
   - Alerta após 5 minutos parado
   - Alertas adicionais a cada 5 minutos se continuar parado
   - Alerta de movimento: "Veículo retomou movimento" (com duração da parada)

### Como Testar o Monitoramento

1. Acesse o admin: http://localhost:8000/admin
2. Vá em "Monitoring Systems"
3. Crie uma nova viagem com status "EM_ANDAMENTO"
4. O sistema começará a monitorar automaticamente via Celery Beat
5. Veja os alertas em tempo real na página de detalhes da viagem

## 📊 Celery Tasks

### Tasks Principais

1. **`broadcast_fleet_positions`** (a cada 30s)

   - Busca posições atualizadas dos rastreadores
   - Analisa desvios de rota e paradas
   - Envia atualizações via WebSocket

2. **`sync_all_devices_data`** (a cada 5 min)
   - Sincroniza dados dos rastreadores com Suntech

## 🔍 Debugging

### Ver logs do Celery

```bash
docker-compose logs -f celery
```

### Ver logs do WebSocket

```bash
docker-compose logs -f web | grep "WebSocket"
```

### Django Shell para testes

```bash
docker-compose exec web python manage.py shell

# Exemplo: Testar análise de desvio
from apps.monitoring.models import MonitoringSystem
trip = MonitoringSystem.objects.get(id=1)
trip.analyze_current_position()
```

## 📝 Boas Práticas

1. **Sempre crie uma branch para novas features**

   ```bash
   git checkout -b feature/nome-da-feature
   ```

2. **Teste localmente antes de commitar**

   - Verifique se não há erros no console
   - Teste as funcionalidades afetadas

3. **Mantenha o código limpo**

   - Use formatadores (Black, djLint)
   - Siga as convenções PEP8

4. **Documente mudanças importantes**
   - Atualize este documento se necessário
   - Comente código complexo

## 🐛 Problemas Comuns

### Celery não está executando tarefas

```bash
# Reinicie o worker
docker-compose restart celery celery-beat
```

### WebSocket não conecta

```bash
# Verifique se o Redis está rodando
docker-compose ps redis

# Reinicie o web server
docker-compose restart web
```

### Migrations não aplicadas

```bash
# Execute as migrations
docker-compose exec web python manage.py migrate

# Se necessário, crie novas migrations
docker-compose exec web python manage.py makemigrations
```

## 📞 Suporte

Em caso de dúvidas, entre em contato com a equipe de desenvolvimento.

---

**Última atualização:** Outubro 2025
