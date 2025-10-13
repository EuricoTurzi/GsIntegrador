# Integrador - Especificação do Projeto

## 📋 Visão Geral

Este projeto visa desenvolver um **sistema integrador** similar ao Trafegus, focado inicialmente na **integração de dispositivos de rastreamento** (rastreadores/trackers) e posteriormente expandindo para módulos de gerenciamento financeiro e operacional.

O desenvolvimento será **incremental e modular**, começando pela base sólida de integração com APIs de fabricantes de rastreadores, com foco inicial na **API da Suntech**.

## 🎯 Objetivos Principais

### Fase Atual: Integração de Dispositivos

1. **Integração com APIs de Rastreadores**: Começando com Suntech
2. **Recebimento de Posições**: Processar dados de telemetria em tempo real
3. **Gerenciamento de Dispositivos**: CRUD completo de equipamentos
4. **Comandos para Dispositivos**: Enviar comandos remotos (bloqueio, configuração, etc.)
5. **Armazenamento de Dados**: Histórico de posições e eventos
6. **API RESTful**: Endpoints para consumo dos dados processados

### Fases Futuras

7. **Sistema de Monitoramento (SM)**: Rastreamento em tempo real, alertas, cercas virtuais
8. **Módulo Financeiro**: Gestão de cobranças, planos, faturas
9. **Módulo de Clientes**: CRM integrado
10. **Relatórios e Analytics**: Dashboards e relatórios operacionais

## 🛠️ Stack Tecnológica

- **Linguagem**: Python 3.11+
- **Framework Web**: Django 5.x
- **API**: Django REST Framework
- **Banco de Dados**: PostgreSQL (produção) / SQLite (desenvolvimento)
- **Filas de Tarefas**: Celery + Redis
- **Cache**: Redis
- **Containerização**: Docker + Docker Compose

## 📐 Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────┐
│          Interface Web (Django Admin)       │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              API REST (DRF)                 │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Camada de Negócios (Services)       │
├─────────────────────────────────────────────┤
│  - Gerenciador de Integrações              │
│  - Processador de Dados                     │
│  - Mapeamento e Transformação               │
│  - Validação de Dados                       │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│      Camada de Persistência (Models)        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           Banco de Dados (PostgreSQL)       │
└─────────────────────────────────────────────┘
```

## 📦 Estrutura de Módulos

### MÓDULOS - FASE 1 (Prioridade Atual)

#### 1. Core (Núcleo)

- Configurações base do Django
- Autenticação e autorização
- Middlewares customizados
- Utilities compartilhados
- Timezone management (UTC)

#### 2. Devices (Dispositivos) - **FOCO PRINCIPAL**

- Modelos de dispositivos (rastreadores)
- Cadastro de equipamentos (IMEI, modelo, fabricante)
- Status e estado dos dispositivos
- Associação dispositivo-veículo
- Gerenciamento de SIM cards

#### 3. Positions (Posições)

- Armazenamento de posições GPS
- Dados de telemetria (velocidade, ignição, bateria, etc.)
- Eventos do dispositivo
- Histórico de trajetos

#### 4. Integrations (Integrações com APIs)

- Conector base para fabricantes
- **Suntech API Integration** (PRIORIDADE)
- Factory pattern para múltiplos fabricantes
- Gerenciamento de credenciais API
- Tratamento de protocolos específicos

#### 5. Commands (Comandos)

- Envio de comandos para dispositivos
- Fila de comandos pendentes
- Histórico de comandos executados
- Respostas e confirmações

#### 6. API (REST API)

- Endpoints para dispositivos
- Endpoints para posições
- Endpoints para comandos
- Autenticação e permissões

### MÓDULOS - FASES FUTURAS

#### 7. Monitoring (Sistema de Monitoramento - SM)

- Rastreamento em tempo real
- Alertas e notificações
- Cercas virtuais (geofences)
- Dashboard de monitoramento

#### 8. Financial (Financeiro)

- Planos e assinaturas
- Cobranças e faturas
- Gestão de pagamentos
- Relatórios financeiros

#### 9. Customers (Clientes)

- Cadastro de clientes
- Gestão de veículos
- Contratos
- CRM básico

## 🗄️ Modelo de Dados

### FASE 1 - Entidades para Integração de Dispositivos

#### Device (Dispositivo)

```python
- id: UUID (PK)
- imei: String (15 digits, unique, indexed)
- serial_number: String (unique)
- manufacturer: String (Suntech, Queclink, etc.)
- model: String (ST4340, ST4955, etc.)
- firmware_version: String
- status: Enum (ACTIVE, INACTIVE, MAINTENANCE, BLOCKED)
- sim_card_number: String
- sim_card_operator: String
- last_communication: DateTime
- registration_date: DateTime
- notes: Text
- configuration: JSON (configurações específicas do fabricante)
- created_at: DateTime
- updated_at: DateTime
```

#### Position (Posição)

```python
- id: BigInt (PK, auto-increment)
- device: ForeignKey(Device, indexed)
- timestamp: DateTime (indexed)
- latitude: Decimal(10, 7)
- longitude: Decimal(10, 7)
- altitude: Float (metros)
- speed: Float (km/h)
- heading: Integer (0-360 graus)
- satellites: Integer
- hdop: Float (precisão horizontal)
- odometer: Float (km)
- ignition: Boolean
- power_voltage: Float (volts)
- battery_level: Integer (%)
- gsm_signal: Integer (%)
- event_code: String
- raw_data: Text (dados brutos do protocolo)
- created_at: DateTime
```

#### Command (Comando)

```python
- id: UUID (PK)
- device: ForeignKey(Device)
- command_type: Enum (LOCK, UNLOCK, REBOOT, CONFIG, POSITION_REQUEST)
- command_text: String
- parameters: JSON
- status: Enum (PENDING, SENT, CONFIRMED, FAILED, TIMEOUT)
- sent_at: DateTime
- confirmed_at: DateTime
- response: Text
- error_message: Text
- created_by: ForeignKey(User)
- created_at: DateTime
- updated_at: DateTime
```

#### DeviceIntegration (Integração do Dispositivo)

```python
- id: UUID (PK)
- device: ForeignKey(Device)
- api_provider: String (suntech, queclink, etc.)
- api_endpoint: String
- api_credentials: EncryptedField (JSON)
- protocol: String (HTTP, TCP, UDP)
- port: Integer
- is_active: Boolean
- last_sync: DateTime
- sync_interval: Integer (segundos)
- configuration: JSON
- created_at: DateTime
- updated_at: DateTime
```

#### Event (Evento)

```python
- id: UUID (PK)
- device: ForeignKey(Device, indexed)
- position: ForeignKey(Position, null=True)
- event_type: Enum (IGNITION_ON, IGNITION_OFF, OVERSPEED, GEOFENCE, SOS, LOW_BATTERY, etc.)
- severity: Enum (INFO, WARNING, CRITICAL)
- message: Text
- data: JSON
- timestamp: DateTime (indexed)
- acknowledged: Boolean
- acknowledged_at: DateTime
- acknowledged_by: ForeignKey(User, null=True)
- created_at: DateTime
```

### FASES FUTURAS - Entidades

#### Vehicle (Veículo)

```python
- id: UUID
- device: OneToOne(Device)
- plate: String
- brand: String
- model: String
- year: Integer
- color: String
- customer: ForeignKey(Customer)
```

#### Customer (Cliente)

```python
- id: UUID
- name: String
- document: String (CPF/CNPJ)
- email: String
- phone: String
- address: Text
- is_active: Boolean
```

#### Subscription (Assinatura)

```python
- id: UUID
- customer: ForeignKey(Customer)
- plan: ForeignKey(Plan)
- device: ForeignKey(Device)
- status: Enum
- start_date: Date
- end_date: Date
```

## 🚀 Fases de Desenvolvimento

### Fase 1: Setup e Infraestrutura Básica ✅

**Objetivo**: Configurar ambiente e estrutura base do projeto

- [ ] Criar ambiente virtual Python
- [ ] Instalar Django e dependências básicas
- [ ] Configurar estrutura de diretórios
- [ ] Configurar banco de dados
- [ ] Criar aplicação `core`
- [ ] Configurar settings (dev/prod)
- [ ] Setup Docker e Docker Compose
- [ ] Configurar `.gitignore` e `.env`

**Entregáveis**: Projeto Django funcionando localmente

---

### Fase 2: Modelos de Dados e Admin ⏳

**Objetivo**: Criar estrutura de dados e interface administrativa

- [ ] Criar models para `Integration`
- [ ] Criar models para `Mapping`
- [ ] Criar models para `Job`
- [ ] Criar models para `IntegrationLog`
- [ ] Configurar Django Admin para todos os models
- [ ] Criar migrations
- [ ] Popular banco com dados de teste
- [ ] Criar custom admin actions

**Entregáveis**: Sistema de gerenciamento via Django Admin

---

### Fase 3: API REST ⏳

**Objetivo**: Desenvolver API para consumo externo

- [ ] Instalar e configurar Django REST Framework
- [ ] Criar serializers para todas as entidades
- [ ] Criar ViewSets para CRUD
- [ ] Implementar autenticação (Token/JWT)
- [ ] Criar permissions customizadas
- [ ] Implementar paginação
- [ ] Criar filtros e ordenação
- [ ] Documentar API (Swagger/OpenAPI)

**Entregáveis**: API RESTful completa e documentada

---

### Fase 4: Camada de Serviços ⏳

**Objetivo**: Implementar lógica de negócio

- [ ] Criar service layer architecture
- [ ] Implementar `IntegrationService`
- [ ] Implementar `MappingService`
- [ ] Implementar `DataTransformationService`
- [ ] Criar validators customizados
- [ ] Implementar exception handling
- [ ] Criar utils para conectores
- [ ] Testes unitários dos services

**Entregáveis**: Camada de negócio robusta e testada

---

### Fase 5: Conectores e Integrações ⏳

**Objetivo**: Implementar conectores para sistemas externos

- [ ] Criar interface base `BaseConnector`
- [ ] Implementar `APIConnector` (REST/SOAP)
- [ ] Implementar `FileConnector` (CSV, JSON, XML)
- [ ] Implementar `DatabaseConnector` (SQL)
- [ ] Implementar `WebhookConnector`
- [ ] Criar factory pattern para conectores
- [ ] Implementar retry logic
- [ ] Tratamento de timeouts e erros

**Entregáveis**: Conectores funcionais para diferentes tipos de integração

---

### Fase 6: Processamento Assíncrono ⏳

**Objetivo**: Implementar sistema de filas e tarefas

- [ ] Configurar Celery + Redis
- [ ] Criar tasks para sincronização
- [ ] Implementar agendamento (Celery Beat)
- [ ] Criar worker configuration
- [ ] Implementar monitoramento (Flower)
- [ ] Configurar retry policies
- [ ] Implementar task chaining
- [ ] Logs de execução de tasks

**Entregáveis**: Sistema de processamento assíncrono operacional

---

### Fase 7: Sistema de Logs e Monitoramento ⏳

**Objetivo**: Implementar rastreabilidade e observabilidade

- [ ] Configurar logging estruturado
- [ ] Criar dashboard de monitoramento
- [ ] Implementar métricas de performance
- [ ] Criar alertas para falhas
- [ ] Implementar auditoria de operações
- [ ] Criar relatórios de execução
- [ ] Implementar health checks
- [ ] Configurar integração com Sentry (opcional)

**Entregáveis**: Sistema de monitoramento e logs completo

---

### Fase 8: Interface Frontend (Opcional) ⏳

**Objetivo**: Criar interface web para gerenciamento

- [ ] Definir tecnologia frontend (React/Vue)
- [ ] Criar dashboard de integrações
- [ ] Interface para configurar mapeamentos
- [ ] Visualização de logs em tempo real
- [ ] Gráficos e métricas
- [ ] Gerenciamento de jobs
- [ ] Notificações em tempo real

**Entregáveis**: Interface web moderna e responsiva

---

### Fase 9: Testes e Qualidade ⏳

**Objetivo**: Garantir qualidade e confiabilidade

- [ ] Configurar pytest
- [ ] Testes unitários (>80% coverage)
- [ ] Testes de integração
- [ ] Testes de API
- [ ] Testes de performance
- [ ] Configurar CI/CD (GitHub Actions)
- [ ] Code linting (flake8, black)
- [ ] Security scanning

**Entregáveis**: Suite de testes completa com alta cobertura

---

### Fase 10: Deploy e Produção ⏳

**Objetivo**: Preparar para ambiente de produção

- [ ] Configurar ambiente de produção
- [ ] Setup de servidor (AWS/GCP/Azure)
- [ ] Configurar NGINX/Gunicorn
- [ ] SSL/TLS certificates
- [ ] Backup automatizado
- [ ] Monitoring em produção
- [ ] Documentação de deploy
- [ ] Runbook operacional

**Entregáveis**: Sistema em produção com documentação completa

---

## 🔐 Segurança

- Autenticação robusta (JWT tokens)
- Criptografia de credenciais sensíveis
- Rate limiting nas APIs
- Validação de inputs
- CORS configurado adequadamente
- SQL injection prevention
- XSS protection

## 📚 Documentação

- README.md com instruções de instalação
- API documentation (Swagger)
- Diagramas de arquitetura
- Guia de contribuição
- Changelog
- Documentação de código (docstrings)

## 🧪 Estratégia de Testes

- **Unit Tests**: Testes isolados de funções e métodos
- **Integration Tests**: Testes de fluxo completo
- **API Tests**: Testes de endpoints
- **Performance Tests**: Testes de carga e stress

## 📝 Convenções de Código

- **PEP 8**: Style guide para Python
- **Type Hints**: Uso de type annotations
- **Docstrings**: Documentação em todas as funções
- **Git Flow**: Branch strategy (main, develop, feature/_, hotfix/_)
- **Commits**: Conventional Commits pattern

## 🔄 Fluxo de Trabalho

1. Criar branch feature
2. Desenvolver funcionalidade
3. Escrever testes
4. Code review
5. Merge para develop
6. Deploy em staging
7. Testes de aceitação
8. Deploy em produção

## 📞 Suporte e Manutenção

- Monitoramento 24/7
- Logs centralizados
- Sistema de alertas
- Backup diário
- Documentação atualizada

---

## 🎓 Instruções para IA

Ao desenvolver este projeto:

1. **Siga as fases na ordem**: Cada fase depende da anterior
2. **Teste cada componente**: Antes de avançar, garanta que está funcionando
3. **Documente o código**: Use docstrings e comentários quando necessário
4. **Siga as convenções**: PEP 8, type hints, e boas práticas Django
5. **Pense em escalabilidade**: O código deve suportar crescimento
6. **Segurança primeiro**: Sempre valide inputs e proteja dados sensíveis
7. **Código limpo**: Prefira legibilidade sobre "cleverness"
8. **DRY**: Don't Repeat Yourself - reutilize código
9. **SOLID**: Siga princípios de design orientado a objetos
10. **Pergunte quando necessário**: Se algo não está claro, peça esclarecimentos

---

## 📅 Próximos Passos Imediatos

**INICIAR FASE 1**: Setup e Infraestrutura Básica

Começaremos criando:

1. Ambiente virtual Python
2. Instalação do Django e dependências
3. Estrutura básica do projeto
4. Configuração inicial

**Comando**: "Vamos começar a Fase 1"

---

_Documento criado em: 07/10/2025_
_Última atualização: 07/10/2025_
