"""
Testes para os models do app devices.
"""
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from freezegun import freeze_time

from apps.devices.models import Device
from apps.vehicles.models import Vehicle
from apps.authentication.models import User
from apps.integrations.suntech_client import SuntechAPIError


@pytest.fixture
def transportadora():
    """Fixture para criar uma transportadora."""
    return User.objects.create_user(
        username='trans_test',
        email='trans@test.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora Teste'
    )


@pytest.fixture
def vehicle(transportadora):
    """Fixture para criar um veículo."""
    return Vehicle.objects.create(
        placa='ABC1234',
        renavam='12345678901',
        chassi='1HGBH41JXMN109186',
        modelo='Caminhão Mercedes',
        ano=2020,
        cor='Branco',
        transportadora=transportadora,
        status='DISPONIVEL'
    )


@pytest.fixture
def device(vehicle):
    """Fixture para criar um dispositivo."""
    return Device.objects.create(
        vehicle=vehicle,
        suntech_device_id=123456,
        suntech_vehicle_id=789012,
        imei='123456789012345',
        label='Rastreador Teste',
        is_active=True
    )


@pytest.mark.django_db
class TestDeviceModel:
    """Testes para o modelo Device."""
    
    def test_create_device(self, vehicle):
        """Testa criação básica de um dispositivo."""
        device = Device.objects.create(
            vehicle=vehicle,
            suntech_device_id=123456,
            suntech_vehicle_id=789012,
            imei='123456789012345',
            label='Rastreador Test'
        )
        
        assert device.id is not None
        assert device.vehicle == vehicle
        assert device.suntech_device_id == 123456
        assert device.suntech_vehicle_id == 789012
        assert device.imei == '123456789012345'
        assert device.label == 'Rastreador Test'
        assert device.is_active is True
    
    def test_device_str(self, device):
        """Testa representação string do dispositivo."""
        assert str(device) == f"Device {device.suntech_device_id} - {device.vehicle.placa}"
    
    def test_device_unique_suntech_id(self, vehicle, transportadora):
        """Testa que suntech_device_id deve ser único."""
        Device.objects.create(
            vehicle=vehicle,
            suntech_device_id=123456,
            suntech_vehicle_id=789012
        )
        
        # Criar outro veículo
        vehicle2 = Vehicle.objects.create(
            placa='XYZ5678',
            renavam='98765432109',
            chassi='2HGBH41JXMN109187',
            modelo='Caminhão Volvo',
            ano=2021,
            cor='Azul',
            transportadora=transportadora,
            status='DISPONIVEL'
        )
        
        # Tentar criar dispositivo com mesmo suntech_device_id
        with pytest.raises(ValidationError) as exc_info:
            Device.objects.create(
                vehicle=vehicle2,
                suntech_device_id=123456,  # ID duplicado
                suntech_vehicle_id=111111
            )
        
        assert 'suntech_device_id' in str(exc_info.value)
    
    def test_device_one_per_vehicle(self, vehicle):
        """Testa que cada veículo pode ter apenas um dispositivo."""
        Device.objects.create(
            vehicle=vehicle,
            suntech_device_id=123456,
            suntech_vehicle_id=789012
        )
        
        # Tentar criar outro dispositivo para o mesmo veículo
        with pytest.raises(ValidationError) as exc_info:
            Device.objects.create(
                vehicle=vehicle,
                suntech_device_id=654321,
                suntech_vehicle_id=210987
            )
        
        assert 'vehicle' in str(exc_info.value)
    
    @freeze_time("2025-01-15 10:00:00")
    def test_is_updated_recently_true(self, device):
        """Testa property is_updated_recently quando atualizado há menos de 30 minutos."""
        # Dispositivo atualizado há 15 minutos
        device.last_system_date = timezone.now() - timedelta(minutes=15)
        device.save()
        
        assert device.is_updated_recently is True
    
    @freeze_time("2025-01-15 10:00:00")
    def test_is_updated_recently_false(self, device):
        """Testa property is_updated_recently quando atualizado há mais de 30 minutos."""
        # Dispositivo atualizado há 45 minutos
        device.last_system_date = timezone.now() - timedelta(minutes=45)
        device.save()
        
        assert device.is_updated_recently is False
    
    def test_is_updated_recently_no_date(self, device):
        """Testa property is_updated_recently quando não há data de atualização."""
        device.last_system_date = None
        device.save()
        
        assert device.is_updated_recently is False
    
    @freeze_time("2025-01-15 10:00:00")
    def test_minutes_since_last_update(self, device):
        """Testa property minutes_since_last_update."""
        # Dispositivo atualizado há 25 minutos
        device.last_system_date = timezone.now() - timedelta(minutes=25)
        device.save()
        
        assert device.minutes_since_last_update == 25.0
    
    def test_minutes_since_last_update_no_date(self, device):
        """Testa property minutes_since_last_update quando não há data."""
        device.last_system_date = None
        device.save()
        
        assert device.minutes_since_last_update is None
    
    def test_odometer_km_conversion(self, device):
        """Testa conversão de odômetro de metros para km."""
        device.odometer = 150000  # 150000 metros
        device.save()
        
        assert device.odometer_km == 150.0
    
    def test_odometer_km_none(self, device):
        """Testa property odometer_km quando odômetro é None."""
        device.odometer = None
        device.save()
        
        assert device.odometer_km is None
    
    @patch('apps.devices.models.suntech_client')
    def test_sync_with_suntech_success(self, mock_client, device):
        """Testa sincronização bem-sucedida com Suntech."""
        mock_vehicle_data = {
            'vehicleId': 789012,
            'deviceId': 123456,
            'label': 'Rastreador Atualizado',
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
        
        result = device.sync_with_suntech()
        
        assert result is True
        mock_client.get_vehicle_by_device_id.assert_called_once_with(123456)
        
        device.refresh_from_db()
        assert device.suntech_vehicle_id == 789012
        assert device.label == 'Rastreador Atualizado'
        assert device.last_address == 'Rua Augusta, 2000'
        assert device.last_speed == 75.5
        assert device.last_ignition_status == 'OFF'
        assert device.odometer == 200000
        assert device.last_sync_at is not None
    
    @patch('apps.devices.models.suntech_client')
    def test_sync_with_suntech_device_not_found(self, mock_client, device):
        """Testa sincronização quando dispositivo não é encontrado na API."""
        mock_client.get_vehicle_by_device_id.return_value = None
        
        result = device.sync_with_suntech()
        
        assert result is False
        mock_client.get_vehicle_by_device_id.assert_called_once_with(123456)
    
    @patch('apps.devices.models.suntech_client')
    def test_sync_with_suntech_api_error(self, mock_client, device):
        """Testa sincronização quando há erro na API."""
        mock_client.get_vehicle_by_device_id.side_effect = SuntechAPIError("API Error")
        
        result = device.sync_with_suntech()
        
        assert result is False
    
    @patch('apps.devices.models.suntech_client')
    def test_check_suntech_status_true(self, mock_client, device):
        """Testa check_suntech_status quando dispositivo está atualizado."""
        mock_client.check_device_updated_recently.return_value = True
        
        result = device.check_suntech_status()
        
        assert result is True
        mock_client.check_device_updated_recently.assert_called_once_with(123456)
    
    @patch('apps.devices.models.suntech_client')
    def test_check_suntech_status_false(self, mock_client, device):
        """Testa check_suntech_status quando dispositivo está desatualizado."""
        mock_client.check_device_updated_recently.return_value = False
        
        result = device.check_suntech_status()
        
        assert result is False
    
    @patch('apps.devices.models.suntech_client')
    def test_check_suntech_status_api_error(self, mock_client, device):
        """Testa check_suntech_status quando há erro na API."""
        mock_client.check_device_updated_recently.side_effect = SuntechAPIError("API Error")
        
        result = device.check_suntech_status()
        
        assert result is False
    
    def test_device_telemetry_fields(self, device):
        """Testa campos de telemetria do dispositivo."""
        device.last_position_date = timezone.now()
        device.last_system_date = timezone.now()
        device.last_address = 'Rua Augusta, 2000'
        device.last_speed = 75.50  # Apenas 2 casas decimais
        device.last_ignition_status = 'OFF'
        device.odometer = 200000
        device.save()
        
        device.refresh_from_db()
        assert device.last_address == 'Rua Augusta, 2000'
        assert device.last_speed == 75.50
        assert device.last_ignition_status == 'OFF'
        assert device.odometer == 200000
    
    def test_device_activation(self, device):
        """Testa ativação e desativação de dispositivo."""
        device.is_active = True
        device.save()
        assert device.is_active is True
        
        device.is_active = False
        device.save()
        assert device.is_active is False
    
    def test_device_observacoes(self, device):
        """Testa campo de observações."""
        device.observacoes = 'Dispositivo instalado em 15/01/2025'
        device.save()
        
        device.refresh_from_db()
        assert device.observacoes == 'Dispositivo instalado em 15/01/2025'
    
    def test_device_relationship_with_vehicle(self, device, vehicle):
        """Testa relacionamento OneToOne com Vehicle."""
        assert device.vehicle == vehicle
        assert vehicle.device == device
    
    def test_device_cascade_delete(self, device, vehicle):
        """Testa que dispositivo é deletado quando veículo é deletado."""
        device_id = device.id
        vehicle.delete()
        
        assert not Device.objects.filter(id=device_id).exists()
