"""
Testes para os serializers do app devices.
"""
import pytest
from django.utils import timezone
from datetime import timedelta

from apps.devices.models import Device
from apps.devices.serializers import (
    DeviceSerializer,
    DeviceListSerializer,
    DeviceCreateUpdateSerializer
)
from apps.vehicles.models import Vehicle
from apps.authentication.models import User


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
    # Não definir coordenadas na fixture para evitar problemas de validação
    device = Device.objects.create(
        vehicle=vehicle,
        suntech_device_id=123456,
        suntech_vehicle_id=789012,
        imei='123456789012345',
        label='Rastreador Teste',
        last_system_date=timezone.now() - timedelta(minutes=15),
        last_address='Av. Paulista, 1000',
        last_speed=60.5,
        last_ignition_status='ON',
        odometer=150000,
        is_active=True
    )
    return device


@pytest.mark.django_db
class TestDeviceSerializer:
    """Testes para DeviceSerializer."""
    
    def test_device_serializer_fields(self, device):
        """Testa campos do DeviceSerializer."""
        serializer = DeviceSerializer(device)
        data = serializer.data
        
        assert data['id'] == device.id
        assert data['suntech_device_id'] == 123456
        assert data['suntech_vehicle_id'] == 789012
        assert data['imei'] == '123456789012345'
        assert data['label'] == 'Rastreador Teste'
        assert data['vehicle_placa'] == 'ABC1234'
        assert data['vehicle_modelo'] == 'Caminhão Mercedes'
        assert data['transportadora_nome'] == 'Transportadora Teste'
        assert data['is_active'] is True
    
    def test_device_serializer_computed_fields(self, device):
        """Testa campos computados do DeviceSerializer."""
        serializer = DeviceSerializer(device)
        data = serializer.data
        
        assert 'is_updated_recently' in data
        assert 'minutes_since_last_update' in data
        assert 'odometer_km' in data
        assert data['odometer_km'] == 150.0
    
    def test_device_serializer_telemetry_fields(self, device):
        """Testa campos de telemetria do DeviceSerializer."""
        serializer = DeviceSerializer(device)
        data = serializer.data
        
        assert data['last_address'] == 'Av. Paulista, 1000'
        assert data['last_speed'] == '60.50'
        assert data['last_ignition_status'] == 'ON'
        assert 'last_latitude' in data
        assert 'last_longitude' in data
    
    def test_device_serializer_read_only_fields(self, device):
        """Testa que campos read-only não podem ser atualizados."""
        original_speed = device.last_speed
        
        serializer = DeviceSerializer(device, data={
            'last_latitude': -22.000000,
            'last_longitude': -45.000000,
            'last_speed': 80.0
        }, partial=True)
        
        assert serializer.is_valid()
        # Campos read-only são ignorados na atualização
        serializer.save()
        
        device.refresh_from_db()
        assert device.last_speed == original_speed  # Não mudou


@pytest.mark.django_db
class TestDeviceListSerializer:
    """Testes para DeviceListSerializer."""
    
    def test_device_list_serializer_fields(self, device):
        """Testa campos resumidos do DeviceListSerializer."""
        serializer = DeviceListSerializer(device)
        data = serializer.data
        
        # Campos incluídos
        assert 'id' in data
        assert 'suntech_device_id' in data
        assert 'vehicle_placa' in data
        assert 'vehicle_modelo' in data
        assert 'label' in data
        assert 'is_active' in data
        assert 'is_updated_recently' in data
        assert 'minutes_since_last_update' in data
        
        # Campos excluídos (versão resumida)
        assert 'last_address' not in data
        assert 'odometer' not in data
        assert 'observacoes' not in data
    
    def test_device_list_serializer_multiple_devices(self, device, transportadora):
        """Testa serialização de múltiplos dispositivos."""
        # Criar outro veículo e dispositivo
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
        
        device2 = Device.objects.create(
            vehicle=vehicle2,
            suntech_device_id=654321,
            suntech_vehicle_id=210987,
            label='Rastreador 2'
        )
        
        devices = Device.objects.all()
        serializer = DeviceListSerializer(devices, many=True)
        
        assert len(serializer.data) == 2


@pytest.mark.django_db
class TestDeviceCreateUpdateSerializer:
    """Testes para DeviceCreateUpdateSerializer."""
    
    def test_create_device(self, vehicle):
        """Testa criação de dispositivo via serializer."""
        data = {
            'vehicle': vehicle.id,
            'suntech_device_id': 999999,
            'suntech_vehicle_id': 888888,
            'imei': '111222333444555',
            'label': 'Novo Rastreador'
        }
        
        serializer = DeviceCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        
        device = serializer.save()
        
        assert device.suntech_device_id == 999999
        assert device.suntech_vehicle_id == 888888
        assert device.imei == '111222333444555'
        assert device.label == 'Novo Rastreador'
        assert device.vehicle == vehicle
    
    def test_update_device(self, device):
        """Testa atualização de dispositivo via serializer."""
        data = {
            'label': 'Rastreador Atualizado',
            'observacoes': 'Atualizado em teste'
        }
        
        serializer = DeviceCreateUpdateSerializer(device, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_device = serializer.save()
        
        assert updated_device.label == 'Rastreador Atualizado'
        assert updated_device.observacoes == 'Atualizado em teste'
    
    def test_create_device_validation_duplicate_suntech_id(self, device, vehicle, transportadora):
        """Testa validação de suntech_device_id duplicado."""
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
        
        data = {
            'vehicle': vehicle2.id,
            'suntech_device_id': 123456,  # ID duplicado
            'suntech_vehicle_id': 888888
        }
        
        serializer = DeviceCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
    
    def test_create_device_validation_duplicate_vehicle(self, device, vehicle):
        """Testa validação de veículo já possuindo dispositivo."""
        data = {
            'vehicle': vehicle.id,  # Veículo já tem dispositivo
            'suntech_device_id': 999999,
            'suntech_vehicle_id': 888888
        }
        
        serializer = DeviceCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
    
    def test_create_device_minimal_data(self, vehicle):
        """Testa criação de dispositivo com dados mínimos."""
        data = {
            'vehicle': vehicle.id,
            'suntech_device_id': 777777,
            'suntech_vehicle_id': 666666
        }
        
        serializer = DeviceCreateUpdateSerializer(data=data)
        assert serializer.is_valid()
        
        device = serializer.save()
        
        assert device.suntech_device_id == 777777
        assert device.suntech_vehicle_id == 666666
        assert device.is_active is True  # Valor padrão
    
    def test_update_device_active_status(self, device):
        """Testa atualização do status ativo do dispositivo."""
        data = {
            'is_active': False
        }
        
        serializer = DeviceCreateUpdateSerializer(device, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_device = serializer.save()
        assert updated_device.is_active is False
