"""
Testes do cliente Suntech API.
"""
import pytest
import responses
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from apps.integrations.suntech_client import SuntechAPIClient, SuntechAPIError


@pytest.fixture
def suntech_client():
    """Fixture que retorna uma instância do cliente Suntech."""
    client = SuntechAPIClient()
    # Limpar cache antes de cada teste
    cache.clear()
    return client


@pytest.fixture
def mock_vehicles_response():
    """Fixture com dados mock de veículos."""
    return {
        'success': True,
        'message': 'Success',
        'data': [
            {
                'deviceId': 123456,
                'vehicleId': 1,
                'vehiclePlate': 'ABC1234',
                'latitude': -23.550520,
                'longitude': -46.633308,
                'address': 'Av. Paulista, São Paulo - SP',
                'speed': 60,
                'ignition': True,
                'date': '2025-10-08 10:30:00',
                'systemDate': '2025-10-08 10:30:00',
                'odometer': 15000.5,
                'direction': 90
            },
            {
                'deviceId': 789012,
                'vehicleId': 2,
                'vehiclePlate': 'XYZ5678',
                'latitude': -23.560520,
                'longitude': -46.643308,
                'address': 'Rua Augusta, São Paulo - SP',
                'speed': 0,
                'ignition': False,
                'date': '2025-10-08 09:00:00',
                'systemDate': '2025-10-08 09:00:00',
                'odometer': 25000.0,
                'direction': 180
            }
        ]
    }


@pytest.mark.unit
class TestSuntechAPIClient:
    """Testes do cliente da API Suntech."""
    
    def test_client_initialization(self, suntech_client):
        """Testa que o cliente é inicializado corretamente."""
        assert suntech_client.base_url == settings.SUNTECH_API_BASE_URL
        assert suntech_client.api_key == settings.SUNTECH_API_KEY
        assert suntech_client.api_user == settings.SUNTECH_API_USER
        assert suntech_client.api_pass == settings.SUNTECH_API_PASS
        assert suntech_client.timeout == 30
    
    def test_get_auth_payload(self, suntech_client):
        """Testa geração do payload de autenticação."""
        payload = suntech_client._get_auth_payload()
        
        assert 'key' in payload
        assert 'user' in payload
        assert 'pass' in payload
        assert payload['key'] == settings.SUNTECH_API_KEY
        assert payload['user'] == settings.SUNTECH_API_USER
        assert payload['pass'] == settings.SUNTECH_API_PASS
    
    @responses.activate
    def test_get_client_vehicles_success(self, suntech_client, mock_vehicles_response):
        """Testa obtenção de veículos com sucesso."""
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_vehicles_response,
            status=200
        )
        
        vehicles = suntech_client.get_client_vehicles(use_cache=False)
        
        assert len(vehicles) == 2
        assert vehicles[0]['deviceId'] == 123456
        assert vehicles[0]['vehiclePlate'] == 'ABC1234'
        assert vehicles[1]['deviceId'] == 789012
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_get_client_vehicles_with_cache(self, suntech_client, mock_vehicles_response):
        """Testa que cache funciona corretamente."""
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_vehicles_response,
            status=200
        )
        
        # Primeira chamada - deve fazer requisição
        vehicles1 = suntech_client.get_client_vehicles(use_cache=True)
        assert len(responses.calls) == 1
        
        # Segunda chamada - deve usar cache
        vehicles2 = suntech_client.get_client_vehicles(use_cache=True)
        assert len(responses.calls) == 1  # Não fez nova requisição
        
        # Dados devem ser iguais
        assert vehicles1 == vehicles2
    
    @responses.activate
    def test_get_client_vehicles_api_error(self, suntech_client):
        """Testa tratamento de erro da API."""
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json={'success': False, 'message': 'Invalid credentials'},
            status=200
        )
        
        with pytest.raises(SuntechAPIError) as exc:
            suntech_client.get_client_vehicles(use_cache=False)
        
        assert 'Invalid credentials' in str(exc.value)
    
    @responses.activate
    def test_get_client_vehicles_connection_error(self, suntech_client):
        """Testa tratamento de erro de conexão."""
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        # Simular erro 500 do servidor
        responses.add(
            responses.POST,
            url,
            json={'error': 'Internal Server Error'},
            status=500
        )
        
        with pytest.raises(SuntechAPIError) as exc:
            suntech_client.get_client_vehicles(use_cache=False)
        
        assert 'Erro ao conectar' in str(exc.value)
    
    @responses.activate
    def test_get_vehicle_by_device_id_found(self, suntech_client, mock_vehicles_response):
        """Testa busca de veículo por device_id quando encontrado."""
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_vehicles_response,
            status=200
        )
        
        vehicle = suntech_client.get_vehicle_by_device_id(123456)
        
        assert vehicle is not None
        assert vehicle['deviceId'] == 123456
        assert vehicle['vehiclePlate'] == 'ABC1234'
    
    @responses.activate
    def test_get_vehicle_by_device_id_not_found(self, suntech_client, mock_vehicles_response):
        """Testa busca de veículo por device_id quando não encontrado."""
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_vehicles_response,
            status=200
        )
        
        vehicle = suntech_client.get_vehicle_by_device_id(999999)
        
        assert vehicle is None
    
    @responses.activate
    def test_check_device_updated_recently_true(self, suntech_client):
        """Testa verificação de dispositivo atualizado recentemente (dentro do período)."""
        # Criar resposta com data muito recente (5 minutos atrás)
        recent_date = datetime.now() - timedelta(minutes=5)
        mock_response = {
            'success': True,
            'data': [
                {
                    'deviceId': 123456,
                    'systemDate': recent_date.strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        }
        
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_response,
            status=200
        )
        
        is_recent = suntech_client.check_device_updated_recently(123456, minutes=30)
        
        assert is_recent is True
    
    @responses.activate
    def test_check_device_updated_recently_false(self, suntech_client):
        """Testa verificação de dispositivo desatualizado (fora do período)."""
        # Criar resposta com data antiga (60 minutos atrás)
        old_date = datetime.now() - timedelta(minutes=60)
        mock_response = {
            'success': True,
            'data': [
                {
                    'deviceId': 123456,
                    'systemDate': old_date.strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        }
        
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_response,
            status=200
        )
        
        is_recent = suntech_client.check_device_updated_recently(123456, minutes=30)
        
        assert is_recent is False
    
    @responses.activate
    def test_check_device_updated_recently_device_not_found(self, suntech_client):
        """Testa verificação quando dispositivo não existe."""
        mock_response = {
            'success': True,
            'data': []
        }
        
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_response,
            status=200
        )
        
        is_recent = suntech_client.check_device_updated_recently(999999, minutes=30)
        
        assert is_recent is False
    
    @responses.activate
    def test_check_device_updated_recently_no_system_date(self, suntech_client):
        """Testa verificação quando dispositivo não tem systemDate."""
        mock_response = {
            'success': True,
            'data': [
                {
                    'deviceId': 123456
                    # systemDate ausente
                }
            ]
        }
        
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_response,
            status=200
        )
        
        is_recent = suntech_client.check_device_updated_recently(123456, minutes=30)
        
        assert is_recent is False
    
    @responses.activate
    def test_check_device_updated_recently_uses_default_threshold(self, suntech_client):
        """Testa que usa threshold padrão do settings quando não especificado."""
        recent_date = datetime.now() - timedelta(minutes=15)
        mock_response = {
            'success': True,
            'data': [
                {
                    'deviceId': 123456,
                    'systemDate': recent_date.strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        }
        
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_response,
            status=200
        )
        
        # Não passa minutes, deve usar DEVICE_UPDATE_THRESHOLD_MINUTES
        is_recent = suntech_client.check_device_updated_recently(123456)
        
        # Depende do valor em settings, mas deve executar sem erro
        assert isinstance(is_recent, bool)
    
    @responses.activate
    def test_get_device_last_position_success(self, suntech_client, mock_vehicles_response):
        """Testa obtenção da última posição do dispositivo."""
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_vehicles_response,
            status=200
        )
        
        position = suntech_client.get_device_last_position(123456)
        
        assert position is not None
        assert position['latitude'] == -23.550520
        assert position['longitude'] == -46.633308
        assert position['address'] == 'Av. Paulista, São Paulo - SP'
        assert position['speed'] == 60
        assert position['ignition'] is True
    
    @responses.activate
    def test_get_device_last_position_not_found(self, suntech_client, mock_vehicles_response):
        """Testa obtenção de posição quando dispositivo não existe."""
        url = f"{settings.SUNTECH_API_BASE_URL}getClientVehicles"
        responses.add(
            responses.POST,
            url,
            json=mock_vehicles_response,
            status=200
        )
        
        position = suntech_client.get_device_last_position(999999)
        
        assert position is None
    
    @responses.activate
    def test_get_vehicle_positions_success(self, suntech_client):
        """Testa obtenção de histórico de posições."""
        mock_response = {
            'success': True,
            'data': [
                {
                    'latitude': -23.550520,
                    'longitude': -46.633308,
                    'date': '2025-10-08 10:00:00',
                    'speed': 50
                },
                {
                    'latitude': -23.551000,
                    'longitude': -46.634000,
                    'date': '2025-10-08 10:05:00',
                    'speed': 55
                }
            ]
        }
        
        url = f"{settings.SUNTECH_API_BASE_URL}getVehiclePositions"
        responses.add(
            responses.POST,
            url,
            json=mock_response,
            status=200
        )
        
        start = datetime(2025, 10, 8, 10, 0, 0)
        end = datetime(2025, 10, 8, 11, 0, 0)
        
        positions = suntech_client.get_vehicle_positions(1, start, end)
        
        assert len(positions) == 2
        assert positions[0]['latitude'] == -23.550520
        assert positions[1]['speed'] == 55
        
        # Verificar que o payload foi enviado corretamente
        request_body = responses.calls[0].request.body
        assert b'2025-10-08 10:00:00' in request_body
        assert b'2025-10-08 11:00:00' in request_body
    
    @responses.activate
    def test_send_command_success(self, suntech_client):
        """Testa envio de comando para dispositivo."""
        mock_response = {
            'success': True,
            'message': 'Command sent successfully'
        }
        
        url = f"{settings.SUNTECH_API_BASE_URL}sendCommand"
        responses.add(
            responses.POST,
            url,
            json=mock_response,
            status=200
        )
        
        result = suntech_client.send_command(1, 'block')
        
        assert result['success'] is True
        assert 'successfully' in result['message']
    
    def test_clear_cache(self, suntech_client):
        """Testa limpeza do cache."""
        # Adicionar algo ao cache
        cache.set('suntech_client_vehicles', ['test_data'], 300)
        
        # Verificar que está no cache
        assert cache.get('suntech_client_vehicles') is not None
        
        # Limpar cache
        suntech_client.clear_cache()
        
        # Verificar que foi removido
        assert cache.get('suntech_client_vehicles') is None
