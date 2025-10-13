# Estrutura do Projeto Integrador

## 📦 Apps Criados

### 1. **authentication**

- Sistema de autenticação
- Tipos de usuário: GR e Transportadora
- JWT para autenticação

### 2. **drivers** (Motoristas)

- Nome
- Tipo_de_Veiculo
- CPF
- RG
- CNH
- Nome_do_Pai
- Nome_da_Mae

### 3. **vehicles** (Veículos)

- Status
- Placa
- Ano
- Cor
- Modelo
- Renavam
- Chassi

### 4. **devices** (Rastreadores/Dispositivos)

- Vinculação ao veículo
- Status de atualização
- Dados de telemetria

### 5. **integrations** (Integrações)

- API Suntech
- Listar dispositivos
- Verificar última atualização (30 min)

### 6. **routes** (Rotas)

- Ponto A
- Ponto B
- OpenStreetMap

### 7. **monitoring** (SM - Sistema de Monitoramento)

- Integra: Rota + Motorista + Veículo
- Validação de rastreador

---

## 🎯 Status Atual

✅ **CONCLUÍDO**:

- Ambiente virtual criado
- Dependências instaladas (Django 4.2.7, DRF, Celery, Redis, etc.)
- Projeto Django criado
- 7 apps criados e configurados
- `settings.py` configurado com:
  - REST Framework
  - JWT Authentication
  - CORS
  - Celery
  - Suntech API settings
  - Debug Toolbar
  - Internacionalização (pt-BR)
  - Timezone (America/Sao_Paulo)
- Arquivo `.env` criado
- Diretórios necessários criados (static, media, templates, logs)

---

## 📁 Estrutura de Diretórios

```
Integrador/
├── integrador/              # Configurações principais
│   ├── settings.py         # ✅ Configurado
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                    # ✅ Todos os apps criados
│   ├── authentication/     # Sistema de usuários
│   ├── drivers/           # Motoristas
│   ├── vehicles/          # Veículos
│   ├── devices/           # Rastreadores
│   ├── integrations/      # API Suntech
│   ├── routes/            # Rotas OpenStreetMap
│   └── monitoring/        # Sistema de Monitoramento (SM)
├── static/                 # Arquivos estáticos
├── media/                  # Upload de arquivos
├── templates/              # Templates HTML
├── logs/                   # Logs da aplicação
├── venv/                   # Ambiente virtual
├── requirements.txt        # Dependências
├── .env                    # Variáveis de ambiente
├── .env.example           # Exemplo de .env
├── .gitignore             # Git ignore
├── docker-compose.yml     # Docker Compose
├── Dockerfile             # Dockerfile
├── README.md              # Documentação
└── manage.py              # Django manage
```

---

## 🔄 Próximos Passos

1. **App Authentication**: Criar modelo de User customizado
2. **App Drivers**: Criar modelo de Motorista
3. **App Vehicles**: Criar modelo de Veículo
4. **App Devices**: Criar modelo de Device
5. **App Integrations**: Implementar cliente da API Suntech
6. **App Routes**: Criar modelo de Rota + integração OpenStreetMap
7. **App Monitoring**: Criar modelo de SM

---

## 🚀 Como Executar

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Fazer migrations
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Executar servidor
python manage.py runserver

# Acessar
http://localhost:8000/admin
```

---

## 📝 Variáveis de Ambiente (.env)

- SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- DB\_\* (Database)
- REDIS_URL
- CELERY\_\*
- SUNTECH*API*\* (Key, User, Pass)
- CORS_ALLOWED_ORIGINS
- TIME_ZONE
