# Suntech API - Documentação Completa

## 📋 Visão Geral

A API Suntech fornece acesso aos dados dos dispositivos de rastreamento registrados na plataforma. Esta documentação detalha todos os endpoints, estruturas de dados e métodos de integração.

**Base URL**: `https://ap3.stc.srv.br/integration/prod/ws/`

**Protocolo**: HTTP POST (JSON)

**Autenticação**: Credenciais enviadas no body de cada requisição

---

## 🔐 Autenticação

Todas as requisições requerem credenciais de autenticação enviadas no body da requisição:

```json
{
  "key": "d548f2c076480dcc2bd69fcbf8e6be61",
  "user": "euricoint",
  "pass": "89f18a66d567c5ab73fe500bb4f336d8"
}
```

### Parâmetros de Autenticação

| Campo  | Tipo   | Obrigatório | Descrição                        |
| ------ | ------ | ----------- | -------------------------------- |
| `key`  | string | Sim         | Chave API fornecida pela Suntech |
| `user` | string | Sim         | Nome de usuário da conta         |
| `pass` | string | Sim         | Senha criptografada (MD5)        |

⚠️ **Importante**: A senha deve ser enviada em formato MD5 hash.

---

## 📡 Endpoints Disponíveis

### 1. GET CLIENT VEHICLES (Listar Dispositivos)

Retorna todos os dispositivos/veículos registrados na conta com suas últimas posições e dados de telemetria.

#### Endpoint

```
POST https://ap3.stc.srv.br/integration/prod/ws/getClientVehicles
```

#### Request Body

```json
{
  "key": "d548f2c076480dcc2bd69fcbf8e6be61",
  "user": "euricoint",
  "pass": "89f18a66d567c5ab73fe500bb4f336d8"
}
```

#### Response (Success)

```json
{
  "success": true,
  "error": 0,
  "data": [
    {
      "vehicleId": 4,
      "plate": "ABC1234",
      "label": "Carro da Frota A",
      "positionId": 16145844,
      "date": "2018-09-26 11:19:27",
      "systemDate": "2018-09-26 11:20:01",
      "ignition": "OFF",
      "speed": "0",
      "output1": "OFF",
      "output2": "OFF",
      "latitude": "-22.846837",
      "longitude": "-47.083258",
      "address": "ALAMEDA PRAÇA CAPITAL - LOT. CENTER SANTA GENEBRA, CAMPINAS - SP, 13080-650",
      "deviceId": 123456,
      "mainBattery": "13.10",
      "backupBattery": "4.1",
      "driverId": "1F00CA1221AA31",
      "vehicleType": 5,
      "odometer": "61747659",
      "horimeter": "085059",
      "rpm": "1000",
      "temp1": "30",
      "temp2": "22",
      "temp3": "14",
      "direction": "000.00"
    }
  ]
}
```

#### Response (Error)

```json
{
  "success": false,
  "error": 1,
  "message": "Invalid credentials"
}
```

#### Estrutura de Dados - Vehicle

| Campo           | Tipo     | Descrição                                  |
| --------------- | -------- | ------------------------------------------ |
| `vehicleId`     | integer  | ID único do veículo na plataforma Suntech  |
| `plate`         | string   | Placa do veículo                           |
| `label`         | string   | Nome/identificação do veículo              |
| `positionId`    | integer  | ID da última posição registrada            |
| `date`          | datetime | Data/hora da posição (timestamp do GPS)    |
| `systemDate`    | datetime | Data/hora de recebimento no servidor       |
| `ignition`      | string   | Status da ignição ("ON" / "OFF")           |
| `speed`         | string   | Velocidade em km/h                         |
| `output1`       | string   | Status da saída digital 1 ("ON" / "OFF")   |
| `output2`       | string   | Status da saída digital 2 ("ON" / "OFF")   |
| `latitude`      | string   | Latitude em formato decimal                |
| `longitude`     | string   | Longitude em formato decimal               |
| `address`       | string   | Endereço geocodificado (reverse geocoding) |
| `deviceId`      | integer  | ID único do dispositivo                    |
| `mainBattery`   | string   | Tensão da bateria principal (volts)        |
| `backupBattery` | string   | Tensão da bateria backup (volts)           |
| `driverId`      | string   | ID do motorista (iButton ou tag RFID)      |
| `vehicleType`   | integer  | Tipo de veículo (código numérico)          |
| `odometer`      | string   | Odômetro em metros                         |
| `horimeter`     | string   | Horímetro (tempo de uso) em formato HHMMSS |
| `rpm`           | string   | Rotações por minuto do motor               |
| `temp1`         | string   | Temperatura sensor 1 (°C)                  |
| `temp2`         | string   | Temperatura sensor 2 (°C)                  |
| `temp3`         | string   | Temperatura sensor 3 (°C)                  |
| `direction`     | string   | Direção em graus (0-360)                   |

---

### 2. GET VEHICLE POSITIONS (Histórico de Posições)

Retorna o histórico de posições de um veículo específico em um período de tempo.

#### Endpoint

```
POST https://ap3.stc.srv.br/integration/prod/ws/getVehiclePositions
```

#### Request Body

```json
{
  "key": "d548f2c076480dcc2bd69fcbf8e6be61",
  "user": "euricoint",
  "pass": "89f18a66d567c5ab73fe500bb4f336d8",
  "vehicleId": 4,
  "startDate": "2024-01-01 00:00:00",
  "endDate": "2024-01-01 23:59:59"
}
```

#### Parâmetros Adicionais

| Campo       | Tipo     | Obrigatório | Descrição                                        |
| ----------- | -------- | ----------- | ------------------------------------------------ |
| `vehicleId` | integer  | Sim         | ID do veículo                                    |
| `startDate` | datetime | Sim         | Data/hora inicial (formato: YYYY-MM-DD HH:MM:SS) |
| `endDate`   | datetime | Sim         | Data/hora final (formato: YYYY-MM-DD HH:MM:SS)   |

#### Response

```json
{
  "success": true,
  "error": 0,
  "data": [
    {
      "positionId": 16145844,
      "vehicleId": 4,
      "date": "2024-01-01 10:30:15",
      "systemDate": "2024-01-01 10:30:20",
      "latitude": "-22.846837",
      "longitude": "-47.083258",
      "speed": "45",
      "ignition": "ON",
      "address": "Rua Exemplo, 123 - São Paulo",
      "odometer": "61747659",
      "direction": "125.50"
    }
  ]
}
```

---

### 3. SEND COMMAND (Enviar Comando)

Envia um comando para um dispositivo específico (bloqueio, desbloqueio, configuração, etc.).

#### Endpoint

```
POST https://ap3.stc.srv.br/integration/prod/ws/sendCommand
```

#### Request Body

```json
{
  "key": "d548f2c076480dcc2bd69fcbf8e6be61",
  "user": "euricoint",
  "pass": "89f18a66d567c5ab73fe500bb4f336d8",
  "deviceId": 123456,
  "command": "LOCK",
  "parameters": {}
}
```

#### Parâmetros Adicionais

| Campo        | Tipo    | Obrigatório | Descrição                                    |
| ------------ | ------- | ----------- | -------------------------------------------- |
| `deviceId`   | integer | Sim         | ID do dispositivo                            |
| `command`    | string  | Sim         | Tipo de comando (LOCK, UNLOCK, REBOOT, etc.) |
| `parameters` | object  | Não         | Parâmetros específicos do comando            |

#### Comandos Disponíveis

| Comando    | Descrição                                      | Parâmetros          |
| ---------- | ---------------------------------------------- | ------------------- |
| `LOCK`     | Bloqueia o veículo (corta combustível/ignição) | -                   |
| `UNLOCK`   | Desbloqueia o veículo                          | -                   |
| `REBOOT`   | Reinicia o dispositivo                         | -                   |
| `POSITION` | Solicita posição imediata                      | -                   |
| `CONFIG`   | Configura parâmetros do dispositivo            | `settings` (object) |

#### Response

```json
{
  "success": true,
  "error": 0,
  "commandId": "CMD123456",
  "status": "SENT",
  "message": "Command sent successfully"
}
```

---

### 4. GET DEVICE INFO (Informações do Dispositivo)

Retorna informações detalhadas de um dispositivo específico.

#### Endpoint

```
POST https://ap3.stc.srv.br/integration/prod/ws/getDeviceInfo
```

#### Request Body

```json
{
  "key": "d548f2c076480dcc2bd69fcbf8e6be61",
  "user": "euricoint",
  "pass": "89f18a66d567c5ab73fe500bb4f336d8",
  "deviceId": 123456
}
```

#### Response

```json
{
  "success": true,
  "error": 0,
  "data": {
    "deviceId": 123456,
    "imei": "860123456789012",
    "model": "ST4340",
    "firmware": "3.2.5",
    "serialNumber": "SN123456",
    "simCard": "55119987654321",
    "operator": "Vivo",
    "status": "ACTIVE",
    "lastCommunication": "2024-01-07 15:30:00"
  }
}
```

---

## 🔄 Fluxo de Integração Recomendado

### 1. Sincronização Inicial

```
┌─────────────────────────────────────────┐
│  1. Chamar getClientVehicles()          │
│     - Obter todos os dispositivos       │
│     - Salvar no banco local             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  2. Para cada dispositivo:              │
│     - Criar/Atualizar registro Device   │
│     - Salvar última posição             │
│     - Atualizar status                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  3. Agendar sincronização periódica     │
│     - Celery task a cada 30 segundos    │
└─────────────────────────────────────────┘
```

### 2. Atualização Periódica

```python
# Pseudo-código da task Celery
@periodic_task(run_every=timedelta(seconds=30))
def sync_suntech_devices():
    """
    Sincroniza dados dos dispositivos Suntech
    """
    # 1. Buscar dados atualizados
    response = suntech_api.get_client_vehicles()

    # 2. Processar cada veículo
    for vehicle_data in response['data']:
        # Atualizar ou criar dispositivo
        device = Device.objects.update_or_create(
            device_id_external=vehicle_data['deviceId'],
            defaults={
                'plate': vehicle_data['plate'],
                'label': vehicle_data['label'],
                'last_communication': vehicle_data['systemDate']
            }
        )

        # Salvar nova posição
        Position.objects.create(
            device=device,
            timestamp=vehicle_data['date'],
            latitude=vehicle_data['latitude'],
            longitude=vehicle_data['longitude'],
            speed=vehicle_data['speed'],
            # ... outros campos
        )
```

### 3. Busca de Histórico

```python
# Buscar histórico quando necessário
def get_vehicle_history(vehicle_id, start_date, end_date):
    """
    Busca histórico de posições de um veículo
    """
    response = suntech_api.get_vehicle_positions(
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date
    )

    # Processar e salvar posições históricas
    for position in response['data']:
        Position.objects.get_or_create(
            position_id_external=position['positionId'],
            defaults={
                # ... dados da posição
            }
        )
```

---

## 🛠️ Implementação Python

### Classe Base do Conector

```python
import hashlib
import requests
from typing import Dict, List, Optional
from datetime import datetime


class SuntechAPIClient:
    """
    Cliente para integração com API Suntech
    """

    BASE_URL = "https://ap3.stc.srv.br/integration/prod/ws/"

    def __init__(self, api_key: str, username: str, password: str):
        """
        Inicializa o cliente da API

        Args:
            api_key: Chave de API fornecida pela Suntech
            username: Nome de usuário
            password: Senha em texto plano (será convertida para MD5)
        """
        self.api_key = api_key
        self.username = username
        self.password_hash = hashlib.md5(password.encode()).hexdigest()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _get_auth_payload(self) -> Dict:
        """Retorna payload de autenticação"""
        return {
            "key": self.api_key,
            "user": self.username,
            "pass": self.password_hash
        }

    def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """
        Faz requisição para API

        Args:
            endpoint: Nome do endpoint (ex: 'getClientVehicles')
            payload: Dados adicionais além da autenticação

        Returns:
            Resposta JSON da API

        Raises:
            SuntechAPIError: Em caso de erro na API
        """
        url = f"{self.BASE_URL}{endpoint}"
        full_payload = {**self._get_auth_payload(), **payload}

        try:
            response = self.session.post(url, json=full_payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data.get('success'):
                error_code = data.get('error', 'unknown')
                error_msg = data.get('message', 'Unknown error')
                raise SuntechAPIError(f"API Error {error_code}: {error_msg}")

            return data

        except requests.exceptions.RequestException as e:
            raise SuntechAPIError(f"Request failed: {str(e)}")

    def get_client_vehicles(self) -> List[Dict]:
        """
        Obtém todos os veículos/dispositivos da conta

        Returns:
            Lista de veículos com suas posições atuais
        """
        response = self._make_request('getClientVehicles', {})
        return response.get('data', [])

    def get_vehicle_positions(
        self,
        vehicle_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Obtém histórico de posições de um veículo

        Args:
            vehicle_id: ID do veículo
            start_date: Data/hora inicial
            end_date: Data/hora final

        Returns:
            Lista de posições no período
        """
        payload = {
            'vehicleId': vehicle_id,
            'startDate': start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'endDate': end_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        response = self._make_request('getVehiclePositions', payload)
        return response.get('data', [])

    def send_command(
        self,
        device_id: int,
        command: str,
        parameters: Optional[Dict] = None
    ) -> Dict:
        """
        Envia comando para dispositivo

        Args:
            device_id: ID do dispositivo
            command: Tipo de comando (LOCK, UNLOCK, etc.)
            parameters: Parâmetros adicionais do comando

        Returns:
            Resposta do comando
        """
        payload = {
            'deviceId': device_id,
            'command': command,
            'parameters': parameters or {}
        }
        return self._make_request('sendCommand', payload)

    def get_device_info(self, device_id: int) -> Dict:
        """
        Obtém informações detalhadas de um dispositivo

        Args:
            device_id: ID do dispositivo

        Returns:
            Informações do dispositivo
        """
        payload = {'deviceId': device_id}
        response = self._make_request('getDeviceInfo', payload)
        return response.get('data', {})


class SuntechAPIError(Exception):
    """Exceção customizada para erros da API Suntech"""
    pass
```

### Exemplo de Uso

```python
# Inicializar cliente
client = SuntechAPIClient(
    api_key="d548f2c076480dcc2bd69fcbf8e6be61",
    username="euricoint",
    password="sua_senha_aqui"  # Em texto plano, será convertida para MD5
)

# Obter todos os veículos
vehicles = client.get_client_vehicles()
for vehicle in vehicles:
    print(f"Veículo: {vehicle['label']} - Placa: {vehicle['plate']}")
    print(f"Última posição: {vehicle['latitude']}, {vehicle['longitude']}")

# Obter histórico
from datetime import datetime, timedelta
end_date = datetime.now()
start_date = end_date - timedelta(days=1)

positions = client.get_vehicle_positions(
    vehicle_id=4,
    start_date=start_date,
    end_date=end_date
)

# Enviar comando
result = client.send_command(
    device_id=123456,
    command="LOCK"
)
print(f"Comando enviado: {result['status']}")
```

---

## 📊 Mapeamento de Campos

### De Suntech para Modelo Local

| Campo Suntech   | Campo Local (Model)   | Transformação         |
| --------------- | --------------------- | --------------------- |
| `vehicleId`     | `vehicle_id_external` | Direct                |
| `deviceId`      | `device_id_external`  | Direct                |
| `plate`         | `plate`               | Upper case            |
| `label`         | `label`               | Trim                  |
| `date`          | `timestamp`           | Parse datetime        |
| `systemDate`    | `received_at`         | Parse datetime        |
| `latitude`      | `latitude`            | Decimal(10, 7)        |
| `longitude`     | `longitude`           | Decimal(10, 7)        |
| `speed`         | `speed`               | Float                 |
| `ignition`      | `ignition`            | Boolean (ON=True)     |
| `mainBattery`   | `power_voltage`       | Float                 |
| `backupBattery` | `battery_voltage`     | Float                 |
| `odometer`      | `odometer`            | Float / 1000 (m → km) |
| `direction`     | `heading`             | Float                 |

---

## ⚠️ Tratamento de Erros

### Códigos de Erro Comuns

| Código | Descrição                | Solução                           |
| ------ | ------------------------ | --------------------------------- |
| 0      | Sucesso                  | -                                 |
| 1      | Credenciais inválidas    | Verificar key, user e pass        |
| 2      | Veículo não encontrado   | Verificar vehicleId               |
| 3      | Período inválido         | Verificar datas (formato e range) |
| 4      | Dispositivo offline      | Aguardar dispositivo conectar     |
| 5      | Comando não suportado    | Verificar modelo do dispositivo   |
| 99     | Erro interno do servidor | Retry após alguns segundos        |

### Estratégia de Retry

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def safe_api_call():
    """Chamada com retry automático"""
    return client.get_client_vehicles()
```

---

## 🔒 Segurança e Boas Práticas

### 1. Armazenamento de Credenciais

```python
# ❌ NUNCA fazer:
API_KEY = "d548f2c076480dcc2bd69fcbf8e6be61"  # hardcoded

# ✅ Usar variáveis de ambiente:
import os
API_KEY = os.getenv('SUNTECH_API_KEY')
```

### 2. Rate Limiting

- Máximo: 1 requisição por segundo
- Recomendado: Sincronização a cada 30-60 segundos
- Usar cache para dados que não mudam frequentemente

### 3. Logging

```python
import logging

logger = logging.getLogger('suntech_api')

logger.info(f"Fetching vehicles for user: {username}")
logger.error(f"API Error: {error_code} - {error_message}")
```

### 4. Timeout

- Sempre definir timeout nas requisições (recomendado: 30s)
- Implementar circuit breaker para falhas consecutivas

---

## 📝 Changelog da API

### Versão Atual: 1.0

- Endpoint `getClientVehicles` disponível
- Suporte a múltiplos sensores de temperatura
- Campo `driverId` para identificação de motorista

### Futuras Implementações (Pendentes)

- [ ] Webhook para recebimento em tempo real
- [ ] Suporte a cercas virtuais (geofences)
- [ ] Relatórios de consumo de combustível
- [ ] API de gestão de alertas

---

## 🧪 Testes

### Testar Conexão

```bash
curl -X POST https://ap3.stc.srv.br/integration/prod/ws/getClientVehicles \
  -H "Content-Type: application/json" \
  -d '{
    "key": "d548f2c076480dcc2bd69fcbf8e6be61",
    "user": "euricoint",
    "pass": "89f18a66d567c5ab73fe500bb4f336d8"
  }'
```

### Testes Unitários

```python
import pytest
from unittest.mock import Mock, patch

def test_get_client_vehicles():
    """Testa obtenção de veículos"""
    client = SuntechAPIClient("key", "user", "pass")

    with patch.object(client.session, 'post') as mock_post:
        mock_post.return_value.json.return_value = {
            'success': True,
            'error': 0,
            'data': [{'vehicleId': 1}]
        }

        vehicles = client.get_client_vehicles()
        assert len(vehicles) == 1
        assert vehicles[0]['vehicleId'] == 1
```

---

## 📞 Suporte Suntech

- **Email**: suporte@suntech.com.br
- **Telefone**: +55 (11) 1234-5678
- **Documentação Oficial**: https://api.suntech.com.br/docs
- **Status da API**: https://status.suntech.com.br

---

_Documento criado em: 07/10/2025_
_Última atualização: 07/10/2025_
_Versão: 1.0_
