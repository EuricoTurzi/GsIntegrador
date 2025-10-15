# 🚛 Integrador - Sistema de Rastreamento e Monitoramento

Sistema integrador de rastreamento veicular em tempo real com foco em transportadoras, desenvolvido em Django.

## ✨ Funcionalidades Principais

### 🔐 Autenticação e Gestão de Usuários

- ✅ Sistema completo de login/registro
- ✅ Tipos de usuário: GR (Gerente de Risco) e Transportadora
- ✅ Gestão de perfis e permissões

### 📊 Gerenciamento

- ✅ Cadastro de motoristas
- ✅ Cadastro de veículos
- ✅ Gestão de rastreadores (devices)
- ✅ Criação e visualização de rotas

### 🎯 Monitoramento em Tempo Real

- ✅ **WebSocket** para atualizações em tempo real
- ✅ **Detecção de desvios de rota** (alertas contínuos a cada 2 minutos)
- ✅ **Detecção de paradas prolongadas** (alertas após 5 minutos)
- ✅ Mapas interativos com Leaflet.js
- ✅ Histórico de posições e alertas
- ✅ Dashboard com visão geral da frota

### 🔗 Integrações

- ✅ **Suntech API** - Sincronização de dados de rastreadores
- ✅ **OpenRouteService** - Cálculo de rotas otimizadas

## 🛠️ Tecnologias

**Backend:**

- Python 3.11+
- Django 4.2.7
- Django REST Framework 3.14
- Django Channels (WebSocket)
- Celery 5.3 (tarefas assíncronas)

**Frontend:**

- Tailwind CSS
- Alpine.js
- Leaflet.js (mapas)

**Infraestrutura:**

- PostgreSQL 15
- Redis 7
- Docker & Docker Compose

## 🚀 Quick Start

### Pré-requisitos

- Docker e Docker Compose instalados
- Git configurado

### Instalação (Docker - Recomendado)

```bash
# Clone o repositório
git clone <repository-url>
cd Integrador

# Copie o arquivo de ambiente
cp .env.example .env

# Edite o .env com suas configurações
nano .env

# Inicie os containers
docker-compose up -d

# Execute as migrations
docker-compose exec web python manage.py migrate

# Crie um superusuário
docker-compose exec web python manage.py createsuperuser

# Acesse: http://localhost:8000
```

> 📖 **Para instruções detalhadas de setup**, veja [docs/SETUP_DEV.md](docs/SETUP_DEV.md)

## 📁 Estrutura do Projeto

```
integrador/
├── apps/                    # Aplicações Django
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
├── docs/                   # 📚 Documentação completa
├── docker-compose.yml      # Orquestração de containers
└── requirements.txt        # Dependências Python
```

## 📚 Documentação

### Documentação Completa

- 📘 [**Guia de Setup para Desenvolvedores**](docs/SETUP_DEV.md) - Como configurar o ambiente de desenvolvimento
- 📗 [**Especificação do Projeto**](docs/PROJECT_SPEC.md) - Requisitos e arquitetura
- 📙 [**Estrutura do Projeto**](docs/STRUCTURE.md) - Organização do código
- 📕 [**API de Autenticação**](docs/API_AUTH.md) - Endpoints de auth e JWT
- 📔 [**API Suntech**](docs/SUNTECH_API.md) - Integração com Suntech
- 🐳 [**Guia Docker**](docs/GUIA_DOCKER.md) - Usando Docker e Docker Compose

### Acessos Rápidos

Após iniciar o servidor:

- 🏠 **Frontend**: http://localhost:8000
- 🔧 **Admin Django**: http://localhost:8000/admin
- 🚀 **API Root**: http://localhost:8000/api/

## 🛠️ Comandos Úteis

```bash
# Ver logs em tempo real
docker-compose logs -f web

# Reiniciar um serviço
docker-compose restart celery

# Acessar shell Django
docker-compose exec web python manage.py shell

# Executar migrations
docker-compose exec web python manage.py migrate
```

## 🤝 Contribuindo

1. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
2. Commit suas mudanças (`git commit -m 'feat: adiciona nova feature'`)
3. Push para a branch (`git push origin feature/nova-feature`)
4. Abra um Pull Request

## 📝 Licença

Proprietary - Todos os direitos reservados

---

**Desenvolvido com ❤️ pela equipe de desenvolvimento**
