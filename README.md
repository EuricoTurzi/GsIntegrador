# Integrador - Sistema de Rastreamento e Monitoramento

Sistema integrador de rastreamento veicular com foco em transportadoras, desenvolvido em Django.

## 🚀 Funcionalidades

### Fase 1 - MVP

- ✅ Gerenciamento de usuários (GR e Transportadora)
- ✅ Cadastro de motoristas
- ✅ Cadastro de veículos
- ✅ Integração com API Suntech
- ✅ Gestão de rastreadores
- ✅ Criação de rotas (OpenStreetMap)
- ✅ Sistema de Monitoramento (SM)

## 🛠️ Stack Tecnológica

- **Python** 3.11+
- **Django** 5.0
- **Django REST Framework** 3.14
- **PostgreSQL** 15
- **Redis** 7
- **Celery** 5.3
- **Docker** & Docker Compose

## 📋 Pré-requisitos

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (opcional)

## 🔧 Instalação

### Opção 1: Com Docker (Recomendado)

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

### Opção 2: Instalação Local

```bash
# Clone o repositório
git clone <repository-url>
cd Integrador

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Copie o arquivo de ambiente
cp .env.example .env

# Edite o .env com suas configurações
nano .env

# Execute as migrations
python manage.py migrate

# Crie um superusuário
python manage.py createsuperuser

# Inicie o servidor
python manage.py runserver

# Em outro terminal, inicie o Celery
celery -A integrador worker --loglevel=info

# Acesse: http://localhost:8000
```

## 📁 Estrutura do Projeto

```
Integrador/
├── integrador/              # Configurações principais do Django
│   ├── settings/
│   │   ├── base.py         # Configurações base
│   │   ├── development.py  # Configurações de desenvolvimento
│   │   └── production.py   # Configurações de produção
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
├── apps/
│   ├── authentication/     # Gerenciamento de usuários e autenticação
│   ├── drivers/           # Gestão de motoristas
│   ├── vehicles/          # Gestão de veículos
│   ├── devices/           # Gestão de rastreadores
│   ├── integrations/      # Integrações (Suntech API)
│   ├── routes/            # Gestão de rotas
│   └── monitoring/        # Sistema de Monitoramento (SM)
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

## 🔑 Variáveis de Ambiente

Consulte o arquivo `.env.example` para todas as variáveis necessárias.

### Principais variáveis:

- `SECRET_KEY`: Chave secreta do Django
- `DEBUG`: Modo debug (True/False)
- `DB_*`: Configurações do PostgreSQL
- `REDIS_URL`: URL do Redis
- `SUNTECH_API_*`: Credenciais da API Suntech

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- Admin: http://localhost:8000/admin
- API Root: http://localhost:8000/api/
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Com coverage
coverage run --source='.' manage.py test
coverage report
```

## 📝 Licença

Proprietary - Todos os direitos reservados

## 👥 Contato

Para mais informações, entre em contato com a equipe de desenvolvimento.
