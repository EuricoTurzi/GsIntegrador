# 🚀 QUICKSTART - Como rodar o projeto

## 📋 Pré-requisitos

Você precisa ter instalado:

- **Docker Desktop** - [Download aqui](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download aqui](https://git-scm.com/downloads)

> ⚠️ **Importante**: Certifique-se de que o Docker Desktop está rodando antes de começar!

---

## 🏃 Começar em 5 Passos

### 1️⃣ Clone o repositório

```bash
git clone <URL-DO-REPOSITORIO>
cd Integrador
```

### 2️⃣ Configure as variáveis de ambiente

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

**Linux/Mac:**

```bash
cp .env.example .env
```

**Depois, edite o arquivo `.env` e configure:**

- As chaves da API Suntech (se tiver)
- A chave da OpenRouteService (se tiver)

> 💡 **Dica**: Se não tiver as chaves ainda, o sistema vai funcionar mas sem as integrações externas.

### 3️⃣ Suba os containers Docker

```bash
docker-compose up -d
```

Isso vai:

- ✅ Baixar as imagens necessárias
- ✅ Criar o banco PostgreSQL
- ✅ Criar o Redis
- ✅ Subir o Django
- ✅ Subir o Celery (tarefas em background)

**Aguarde uns 2-3 minutos na primeira vez!**

### 4️⃣ Execute as migrations (banco de dados)

```bash
docker-compose exec web python manage.py migrate
```

### 5️⃣ Crie um usuário administrador

```bash
docker-compose exec web python manage.py createsuperuser
```

Vai pedir:

- Username (ex: admin)
- Email (ex: admin@example.com)
- Senha (digite 2 vezes)

---

## 🎉 Pronto! Acesse o sistema

Abra seu navegador e acesse:

### 🏠 **Sistema Principal**

http://localhost:8000

Faça login com o usuário que você criou!

### 🔧 **Admin Django** (para gerenciar tudo)

http://localhost:8000/admin

---

## 📝 Comandos Úteis

### Ver os logs (se der algum erro)

```bash
docker-compose logs -f web
```

_Pressione Ctrl+C para sair_

### Ver se tudo está rodando

```bash
docker-compose ps
```

Deve mostrar 5 containers rodando:

- `web` - Django
- `db` - PostgreSQL
- `redis` - Redis
- `celery` - Celery Worker
- `celery-beat` - Celery Beat (agendador)

### Reiniciar tudo (se der problema)

```bash
docker-compose restart
```

### Parar tudo

```bash
docker-compose down
```

### Iniciar novamente (depois de parar)

```bash
docker-compose up -d
```

---

## 🆘 Problemas Comuns

### "Docker não está rodando"

✅ Abra o Docker Desktop e aguarde ele iniciar completamente

### "Porta 8000 já está em uso"

✅ Você tem outro programa usando a porta 8000

```bash
# Windows
netstat -ano | findstr :8000
# Linux/Mac
lsof -i :8000
```

Mate o processo ou mude a porta no `docker-compose.yml`

### "Error: password authentication failed"

✅ Delete os volumes e comece de novo:

```bash
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### "Página não carrega"

✅ Verifique se todos os containers estão rodando:

```bash
docker-compose ps
```

✅ Veja os logs:

```bash
docker-compose logs -f web
```

---

## 🎯 Próximos Passos

Depois que estiver funcionando:

1. 📖 Leia a [**Documentação Completa**](docs/SETUP_DEV.md)
2. 🔍 Explore o código em `apps/`
3. 🗺️ Acesse o sistema e crie sua primeira viagem de teste

---

## 💡 Dicas Importantes

### Para Desenvolvimento

- Sempre use `docker-compose logs -f [service]` para debugar
- Alterações no código Python são recarregadas automaticamente
- Alterações nos templates também são automáticas
- Se mudar o `requirements.txt`, precisa rebuild: `docker-compose up -d --build`

### Celery (Tarefas em Background)

- O Celery monitora viagens a cada 30 segundos
- O Celery Beat agenda as tarefas periódicas
- Se precisar reiniciar: `docker-compose restart celery celery-beat`

### Banco de Dados

- PostgreSQL rodando na porta 5432
- Dados persistem mesmo se parar os containers
- Para resetar tudo: `docker-compose down -v` (⚠️ apaga os dados!)

---

## 🤝 Precisa de Ajuda?

1. Veja os logs: `docker-compose logs -f`
2. Consulte a [documentação completa](docs/SETUP_DEV.md)
3. Entre em contato com a equipe

---

**Desenvolvido com ❤️ - Boa sorte! 🚀**
