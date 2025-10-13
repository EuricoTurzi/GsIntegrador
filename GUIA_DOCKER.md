# 🐳 GUIA RÁPIDO - Docker para Iniciantes

## ❓ O que é Docker?

Docker cria "containers" - tipo máquinas virtuais leves que rodam seu app isolado, com tudo que precisa (Python, PostgreSQL, Redis, etc).

## ✅ Pré-requisitos

### 1. Instalar Docker Desktop

- **Windows**: https://www.docker.com/products/docker-desktop/
- Baixe e instale (é Next → Next → Finish)
- Reinicie o PC se pedir
- Abra o Docker Desktop e deixe rodando em background

### 2. Verificar se instalou

Abra o terminal (PowerShell ou CMD) e digite:

```bash
docker --version
docker-compose --version
```

Se aparecer as versões, tá pronto! 🎉

---

## 🚀 PASSO A PASSO - Rodando o Integrador

### Passo 1: Abrir o terminal no projeto

```bash
cd C:\Users\eurico.dante\Desktop\Development\Integrador
```

### Passo 2: Usar o .env correto para Docker

```bash
# No Windows (PowerShell):
Copy-Item .env.docker .env -Force

# Ou no Git Bash:
cp .env.docker .env
```

### Passo 3: Buildar e iniciar TUDO de uma vez

```bash
docker-compose up --build
```

**O que vai acontecer:**

- 📦 Vai baixar as imagens (PostgreSQL, Redis, Python)
- 🏗️ Vai buildar sua aplicação
- 🚀 Vai iniciar 5 containers:
  - `integrador_web` - Django com WebSocket
  - `integrador_db` - PostgreSQL
  - `integrador_redis` - Redis (cache + filas)
  - `integrador_celery` - Worker de tarefas
  - `integrador_celery_beat` - Scheduler de tarefas

**Primeira vez demora uns 5-10 min!** ☕

### Passo 4: Aguardar tudo subir

Você vai ver MUITAS mensagens. Quando aparecer:

```
✅ PostgreSQL pronto!
✅ Redis pronto!
✅ Integrador pronto!
```

Significa que tá rodando! 🎉

### Passo 5: Acessar

Abra o navegador:

- **Sistema**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
  - Usuário: `admin`
  - Senha: `admin123`

---

## 🛑 COMANDOS ÚTEIS

### Parar tudo (mantém os dados)

```bash
Ctrl + C  (no terminal onde tá rodando)
# Ou em outro terminal:
docker-compose down
```

### Parar tudo e APAGAR dados (reset total)

```bash
docker-compose down -v
```

### Iniciar de novo (sem rebuild)

```bash
docker-compose up
```

### Rodar em background (não prende o terminal)

```bash
docker-compose up -d
```

### Ver os logs

```bash
# Todos os logs
docker-compose logs -f

# Log de um serviço específico
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f redis
```

### Ver o que tá rodando

```bash
docker-compose ps
```

### Entrar dentro do container (tipo SSH)

```bash
docker-compose exec web bash
```

### Executar comandos Django

```bash
# Migrations
docker-compose exec web python manage.py migrate

# Criar super usuário
docker-compose exec web python manage.py createsuperuser

# Django shell
docker-compose exec web python manage.py shell

# Testes
docker-compose exec web python manage.py test
```

---

## ⚠️ PROBLEMAS COMUNS

### Erro: "Port 8000 already in use"

Você já tem algo rodando na porta 8000 (provavelmente seu `python manage.py runserver`).

**Solução:** Pare o runserver antes:

```bash
# Procure o terminal onde tá rodando e dê Ctrl+C
# Ou mate o processo:
taskkill /F /IM python.exe  # Windows
```

### Erro: "Cannot connect to Docker daemon"

O Docker Desktop não está rodando.

**Solução:** Abra o Docker Desktop e aguarde ele iniciar.

### Containers não sobem

**Solução:** Rebuild do zero:

```bash
docker-compose down -v
docker-compose up --build
```

### Site não carrega

**Solução:**

1. Verifique se os containers estão UP: `docker-compose ps`
2. Veja os logs: `docker-compose logs web`
3. Aguarde mais um pouco (primeira vez demora!)

---

## 📊 MONITORANDO O SISTEMA

### Ver uso de recursos

```bash
docker stats
```

### Ver containers rodando

```bash
docker ps
```

### Ver todos os containers (incluindo parados)

```bash
docker ps -a
```

---

## 🧹 LIMPEZA

### Remover containers parados

```bash
docker-compose down
```

### Remover volumes (APAGA dados do banco!)

```bash
docker-compose down -v
```

### Limpar tudo do Docker (quando tá cheio)

```bash
docker system prune -a
```

---

## 💡 DICAS

1. **Primeira vez é lenta** - Docker baixa tudo. Depois é rápido! ⚡
2. **Deixe Docker Desktop rodando** - Senão nada funciona
3. **Use `docker-compose logs -f`** - Para ver o que tá acontecendo
4. **Mudou código?** - Só salvar! Docker detecta e recarrega (como runserver)
5. **Mudou requirements.txt?** - Precisa rebuild: `docker-compose up --build`

---

## 🎯 WORKFLOW NORMAL

```bash
# 1. Primeira vez (ou depois de muito tempo)
docker-compose up --build

# 2. Dia a dia (já buildou antes)
docker-compose up

# 3. Rodar em background e continuar trabalhando
docker-compose up -d

# 4. Ver se tá tudo ok
docker-compose ps

# 5. Ver logs se algo der errado
docker-compose logs -f web

# 6. Parar no final do dia
docker-compose down
```

---

## ✅ CHECKLIST - Tá tudo funcionando?

- [ ] Docker Desktop instalado e rodando
- [ ] `docker --version` funciona
- [ ] `docker-compose up --build` rodou sem erros
- [ ] http://localhost:8000 abre
- [ ] Login com admin/admin123 funciona
- [ ] `docker-compose ps` mostra 5 containers UP

Se tudo ✅, você tá pronto! 🚀

---

## 🆘 PRECISA DE AJUDA?

1. Copie o erro que aparece
2. Rode `docker-compose logs web` e copie a saída
3. Me manda que eu ajudo! 😉
