# 🚚 Integrador - Sistema de Gestão de Transporte

Sistema completo de gestão de transportes com rastreamento em tempo real, integração com API Suntech, e WebSocket para atualizações live.

## 🐳 Rodando com Docker

### Pré-requisitos

- Docker
- Docker Compose

### Instalação Rápida

1. **Clone o repositório**

```bash
git clone <repo-url>
cd Integrador
```

2. **Configure as variáveis de ambiente**

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

3. **Inicie os containers**

```bash
docker-compose up --build
```

4. **Acesse a aplicação**

- Web: http://localhost:8000
- Admin: http://localhost:8000/admin
- Credenciais padrão: `admin` / `admin123`

### Comandos Úteis

**Parar os containers:**

```bash
docker-compose down
```

**Ver logs:**

```bash
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f redis
```

**Executar comandos Django:**

```bash
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

**Rebuild após mudanças:**

```bash
docker-compose up --build -d
```

## 🏗️ Arquitetura

### Serviços Docker

- **web** (Django + Daphne): Servidor ASGI para HTTP e WebSocket
- **db** (PostgreSQL 15): Banco de dados principal
- **redis**: Cache e broker para Celery/Channels
- **celery**: Worker para tarefas assíncronas
- **celery-beat**: Scheduler para tarefas periódicas

### Tecnologias

- **Backend**: Django 4.2.7
- **WebSocket**: Django Channels + Daphne
- **Cache/Broker**: Redis
- **Database**: PostgreSQL
- **Tasks**: Celery
- **API REST**: Django Rest Framework
- **Frontend**: TailwindCSS + Leaflet.js

## 📡 WebSocket Endpoints

### Tracking de Viagem Individual

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/monitoring/<trip_id>/");

ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  if (data.type === "position_update") {
    // Atualizar posição no mapa
    console.log(data.data);
  }
};
```

### Tracking de Frota Completa

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/monitoring/fleet/");

ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  if (data.type === "fleet_update") {
    // Atualizar todos veículos no mapa
    console.log(data.data); // Array de posições
  }
};
```

## ⚙️ Tarefas Celery Periódicas

- **sync_all_devices** (a cada 5 min): Sincroniza posições com API Suntech
- **broadcast_fleet_positions** (a cada 30s): Envia posições via WebSocket
- **check_monitoring_device_status** (diário): Verifica dispositivos desatualizados

## 🧪 Desenvolvimento Local (sem Docker)

Se preferir rodar sem Docker:

```bash
# Instalar dependências
pip install -r requirements.txt
pip install channels channels-redis daphne celery redis

# Iniciar Redis (precisa estar instalado)
redis-server

# Iniciar Django
python manage.py runserver

# Em outro terminal: Celery Worker
celery -A integrador worker --loglevel=info

# Em outro terminal: Celery Beat
celery -A integrador beat --loglevel=info
```

## 📝 Estrutura do Projeto

```
Integrador/
├── apps/
│   ├── authentication/       # Autenticação e usuários
│   ├── drivers/             # Gestão de motoristas
│   ├── vehicles/            # Gestão de veículos
│   ├── devices/             # Rastreadores GPS
│   ├── routes/              # Rotas de viagem
│   ├── monitoring/          # Sistema de monitoramento
│   │   ├── consumers.py     # WebSocket consumers
│   │   ├── routing.py       # WebSocket URL routing
│   │   ├── tasks.py         # Celery tasks
│   │   └── models.py        # Models (MonitoringSystem)
│   └── integrations/        # Integração Suntech API
├── integrador/
│   ├── asgi.py             # Configuração ASGI
│   ├── celery.py           # Configuração Celery
│   └── settings.py         # Settings Django
├── docker-compose.yml       # Orquestração Docker
├── Dockerfile              # Imagem Docker
└── docker-entrypoint.sh    # Script de inicialização
```

## 🔒 Segurança

- Nunca commite o arquivo `.env` com credenciais reais
- Use secrets do Docker para produção
- Configure CORS adequadamente
- Use HTTPS em produção
- Implemente rate limiting em produção

## 📚 Documentação API

- API REST: http://localhost:8000/api/
- Swagger: http://localhost:8000/api/docs/

## 🐛 Troubleshooting

**Erro de conexão com Redis:**

```bash
docker-compose restart redis
```

**Erro de permissão no PostgreSQL:**

```bash
docker-compose down -v
docker-compose up -d
```

**Celery não processa tasks:**

```bash
docker-compose logs celery
docker-compose restart celery
```

**WebSocket não conecta:**

- Verifique se Daphne está rodando: `docker-compose logs web`
- Verifique se Redis está acessível
- Confirme que está usando `ws://` (não `http://`)

## 📄 Licença

MIT License
