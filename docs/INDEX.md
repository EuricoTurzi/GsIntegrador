# 📚 Índice da Documentação

Bem-vindo à documentação do **Integrador** - Sistema de Rastreamento e Monitoramento.

## 🚀 Para Começar

### [**Guia de Setup para Desenvolvedores**](SETUP_DEV.md)
Guia completo para configurar o ambiente de desenvolvimento, incluindo:
- Instalação e configuração do Docker
- Variáveis de ambiente
- Comandos úteis
- Debugging e solução de problemas

### [**Preparação do Projeto para GitHub**](PREPARACAO_GITHUB.md)
Documentação sobre a preparação do projeto para compartilhamento:
- Arquivos organizados
- O que deve/não deve ir para o repositório
- Instruções para commitar

---

## 📖 Documentação Técnica

### [**Especificação do Projeto**](PROJECT_SPEC.md)
Especificação completa do sistema, incluindo:
- Objetivos e escopo
- Requisitos funcionais e não-funcionais
- Arquitetura do sistema
- Casos de uso

### [**Estrutura do Projeto**](STRUCTURE.md)
Organização do código e estrutura de diretórios:
- Apps Django e suas responsabilidades
- Modelos de dados
- Fluxo de trabalho

---

## 🔌 APIs e Integrações

### [**API de Autenticação**](API_AUTH.md)
Documentação dos endpoints de autenticação:
- Registro e login
- JWT tokens
- Gestão de usuários
- Permissões

### [**API Suntech**](SUNTECH_API.md)
Integração com a API Suntech:
- Endpoints disponíveis
- Sincronização de dados
- Formato dos dados de rastreamento
- Exemplos de uso

---

## 🐳 Docker

### [**Guia Docker**](GUIA_DOCKER.md)
Uso do Docker e Docker Compose:
- Configuração dos containers
- Comandos docker-compose
- Troubleshooting

### [**Docker README**](DOCKER_README.md)
Informações específicas sobre a configuração Docker do projeto.

---

## 📋 Organização da Documentação

```
docs/
├── INDEX.md                      # Este arquivo
├── SETUP_DEV.md                 # ⭐ Comece aqui!
├── PREPARACAO_GITHUB.md         # Preparação para Git
├── PROJECT_SPEC.md              # Especificação técnica
├── STRUCTURE.md                 # Estrutura do código
├── API_AUTH.md                  # API de autenticação
├── SUNTECH_API.md               # Integração Suntech
├── GUIA_DOCKER.md               # Guia Docker
└── DOCKER_README.md             # Docker README
```

---

## 🎯 Por Onde Começar?

### Para Desenvolvedores Novos
1. 📘 Leia o [**Guia de Setup**](SETUP_DEV.md)
2. 📗 Entenda o [**PROJECT_SPEC**](PROJECT_SPEC.md)
3. 📙 Explore a [**Estrutura do Projeto**](STRUCTURE.md)
4. 🚀 Comece a desenvolver!

### Para Configurar o Ambiente
1. 📘 Siga o [**Guia de Setup**](SETUP_DEV.md)
2. 🐳 Consulte o [**Guia Docker**](GUIA_DOCKER.md) se necessário

### Para Entender as APIs
1. 📕 [**API de Autenticação**](API_AUTH.md)
2. 📔 [**API Suntech**](SUNTECH_API.md)

---

## 💡 Dicas

- Use `Ctrl+F` ou `Cmd+F` para buscar dentro dos documentos
- Os exemplos de código podem ser copiados diretamente
- Sempre consulte o `.env.example` para variáveis de ambiente
- Em caso de dúvidas, consulte o README.md na raiz do projeto

---

**Última atualização:** Outubro 2025

