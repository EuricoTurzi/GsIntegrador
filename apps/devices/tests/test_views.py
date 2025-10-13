"""
Testes para as views do app devices.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from freezegun import freeze_time

from apps.devices.models import Device
from apps.vehicles.models import Vehicle
from apps.authentication.models import User


@pytest.fixture
def api_client():
    """Fixture para o cliente da API."""
    return APIClient()


@pytest.fixture
def gr_user():
    """Fixture para usuário do tipo GR."""
    return User.objects.create_user(
        username='gr_user',
        email='gr@test.com',
        password='testpass123',
        user_type='GR',
        company_name='GR Logística'
    )


@pytest.fixture
def transportadora1():
    """Fixture para primeira transportadora."""
    return User.objects.create_user(
        username='trans1',
        email='trans1@test.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 1'
    )


@pytest.fixture
def transportadora2():
    """Fixture para segunda transportadora."""
    return User.objects.create_user(
        username='trans2',
        email='trans2@test.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 2'
    )


@pytest.fixture
def vehicle1(transportadora1):
    """Fixture para veículo da transportadora 1."""
    return Vehicle.objects.create(
        placa='ABC1234',
        renavam='12345678901',
        chassi='1HGBH41JXMN109186',
        modelo='Caminhão Mercedes',
        ano=2020,
        cor='Branco',
        transportadora=transportadora1,
        status='DISPONIVEL'
    )


@pytest.fixture
def vehicle2(transportadora2):
    """Fixture para veículo da transportadora 2."""
    return Vehicle.objects.create(
        placa='XYZ5678',
        renavam='98765432109',
        chassi='2HGBH41JXMN109187',
        modelo='Caminhão Volvo',
        ano=2021,
        cor='Azul',
        transportadora=transportadora2,
        status='DISPONIVEL'
    )


@pytest.fixture
def device1(vehicle1):
    """Fixture para dispositivo da transportadora 1."""
    return Device.objects.create(
        vehicle=vehicle1,
        suntech_device_id=123456,
        suntech_vehicle_id=789012,
        imei='123456789012345',
        label='Rastreador 1',
        is_active=True
    )


@pytest.fixture
def device2(vehicle2):
    """Fixture para dispositivo da transportadora 2."""
    return Device.objects.create(
        vehicle=vehicle2,
        suntech_device_id=654321,
        suntech_vehicle_id=210987,
        imei='987654321098765',
        label='Rastreador 2',
        is_active=True
    )


@pytest.mark.django_db
class TestDeviceViewSet:
    """Testes para o DeviceViewSet."""
    
    def test_list_devices_unauthenticated(self, api_client):
        """Testa que usuário não autenticado não pode listar dispositivos."""
        url = reverse('device-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_devices_as_gr(self, api_client, gr_user, device1, device2):
        """Testa que GR pode ver todos os dispositivos."""
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_list_devices_as_transportadora(self, api_client, transportadora1, device1, device2):
        """Testa que transportadora vê apenas seus dispositivos."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('device-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['suntech_device_id'] == 123456
    
    def test_create_device_as_gr(self, api_client, gr_user, vehicle1):
        """Testa criação de dispositivo por GR."""
        # Remover dispositivo existente
        Device.objects.all().delete()
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-list')
        
        data = {
            'vehicle': vehicle1.id,
            'suntech_device_id': 999999,
            'suntech_vehicle_id': 888888,
            'imei': '111222333444555',
            'label': 'Novo Rastreador'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Device.objects.filter(suntech_device_id=999999).exists()
    
    def test_retrieve_device(self, api_client, gr_user, device1):
        """Testa detalhamento de um dispositivo."""
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-detail', kwargs={'pk': device1.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suntech_device_id'] == 123456
        assert response.data['vehicle_placa'] == 'ABC1234'
    
    def test_update_device(self, api_client, gr_user, device1):
        """Testa atualização de dispositivo."""
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-detail', kwargs={'pk': device1.id})
        
        data = {
            'vehicle': device1.vehicle.id,
            'suntech_device_id': 123456,
            'suntech_vehicle_id': 789012,
            'label': 'Rastreador Atualizado'
        }
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        device1.refresh_from_db()
        assert device1.label == 'Rastreador Atualizado'
    
    def test_delete_device(self, api_client, gr_user, device1):
        """Testa deleção de dispositivo."""
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-detail', kwargs={'pk': device1.id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Device.objects.filter(id=device1.id).exists()
    
    @freeze_time("2025-01-15 10:00:00")
    def test_action_updated_devices(self, api_client, gr_user, device1, device2):
        """Testa action para listar dispositivos atualizados."""
        # Configurar device1 atualizado há 15 min (atualizado)
        device1.last_system_date = timezone.now() - timedelta(minutes=15)
        device1.save()
        
        # Configurar device2 atualizado há 45 min (desatualizado)
        device2.last_system_date = timezone.now() - timedelta(minutes=45)
        device2.save()
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-updated')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['data'][0]['suntech_device_id'] == 123456
    
    @freeze_time("2025-01-15 10:00:00")
    def test_action_outdated_devices(self, api_client, gr_user, device1, device2):
        """Testa action para listar dispositivos desatualizados."""
        # Configurar device1 atualizado há 15 min (atualizado)
        device1.last_system_date = timezone.now() - timedelta(minutes=15)
        device1.save()
        
        # Configurar device2 atualizado há 45 min (desatualizado)
        device2.last_system_date = timezone.now() - timedelta(minutes=45)
        device2.save()
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-outdated')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['data'][0]['suntech_device_id'] == 654321
    
    @patch('apps.devices.models.suntech_client')
    def test_action_sync_device_success(self, mock_client, api_client, gr_user, device1):
        """Testa sincronização de dispositivo com sucesso."""
        mock_vehicle_data = {
            'vehicleId': 789012,
            'deviceId': 123456,
            'label': 'Rastreador Sincronizado',
            'date': '2025-01-15 10:00:00',
            'systemDate': '2025-01-15 10:00:05',
            'latitude': None,  # Evitar problemas de validação
            'longitude': None,
            'address': 'Rua Augusta, 2000',
            'speed': 75.5,
            'ignition': 'OFF',
            'odometer': 200000
        }
        
        mock_client.get_vehicle_by_device_id.return_value = mock_vehicle_data
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-sync', kwargs={'pk': device1.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'sincronizado com sucesso' in response.data['message']
    
    @patch('apps.devices.models.suntech_client')
    def test_action_sync_device_failure(self, mock_client, api_client, gr_user, device1):
        """Testa sincronização de dispositivo com falha."""
        mock_client.get_vehicle_by_device_id.return_value = None
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-sync', kwargs={'pk': device1.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data['success'] is False
    
    def test_action_device_status(self, api_client, gr_user, device1):
        """Testa action para verificar status do dispositivo."""
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-status', kwargs={'pk': device1.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['device_id'] == device1.id
        assert response.data['suntech_device_id'] == 123456
        assert response.data['vehicle_placa'] == 'ABC1234'
        assert 'is_updated' in response.data
        assert 'minutes_since_update' in response.data
        assert 'threshold_minutes' in response.data
    
    def test_action_activate_device(self, api_client, gr_user, device1):
        """Testa action para ativar dispositivo."""
        device1.is_active = False
        device1.save()
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-activate', kwargs={'pk': device1.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'ativado com sucesso' in response.data['message']
        
        device1.refresh_from_db()
        assert device1.is_active is True
    
    def test_action_deactivate_device(self, api_client, gr_user, device1):
        """Testa action para desativar dispositivo."""
        device1.is_active = True
        device1.save()
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-deactivate', kwargs={'pk': device1.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'desativado com sucesso' in response.data['message']
        
        device1.refresh_from_db()
        assert device1.is_active is False
    
    @patch('apps.devices.models.suntech_client')
    def test_action_sync_all_as_gr(self, mock_client, api_client, gr_user, device1, device2):
        """Testa sincronização de todos dispositivos como GR."""
        mock_vehicle_data = {
            'vehicleId': 789012,
            'deviceId': 123456,
            'label': 'Rastreador',
            'date': '2025-01-15 10:00:00',
            'systemDate': '2025-01-15 10:00:05'
        }
        
        mock_client.get_vehicle_by_device_id.return_value = mock_vehicle_data
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-sync-all')
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['total'] == 2
        assert response.data['synced'] == 2
    
    def test_action_sync_all_as_transportadora_forbidden(self, api_client, transportadora1, device1):
        """Testa que transportadora não pode sincronizar todos dispositivos."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('device-sync-all')
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_search_device_by_placa(self, api_client, gr_user, device1, device2):
        """Testa busca de dispositivo por placa do veículo."""
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-list')
        response = api_client.get(url, {'search': 'ABC1234'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['vehicle_placa'] == 'ABC1234'
    
    def test_filter_device_by_active_status(self, api_client, gr_user, device1, device2):
        """Testa filtro por status ativo."""
        device2.is_active = False
        device2.save()
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-list')
        response = api_client.get(url, {'is_active': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['suntech_device_id'] == 123456
    
    def test_filter_device_by_ignition_status(self, api_client, gr_user, device1, device2):
        """Testa filtro por status de ignição."""
        device1.last_ignition_status = 'ON'
        device1.save()
        
        device2.last_ignition_status = 'OFF'
        device2.save()
        
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-list')
        response = api_client.get(url, {'last_ignition_status': 'ON'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['last_ignition_status'] == 'ON'
    
    def test_ordering_devices(self, api_client, gr_user, device1, device2):
        """Testa ordenação de dispositivos."""
        api_client.force_authenticate(user=gr_user)
        url = reverse('device-list')
        response = api_client.get(url, {'ordering': 'suntech_device_id'})
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert results[0]['suntech_device_id'] < results[1]['suntech_device_id']
    
    def test_transportadora_cannot_access_other_devices(self, api_client, transportadora1, device2):
        """Testa que transportadora não pode acessar dispositivos de outra transportadora."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('device-detail', kwargs={'pk': device2.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
