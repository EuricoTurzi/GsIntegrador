"""
Testes para o modelo MonitoringSystem (SM).
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from freezegun import freeze_time
from apps.monitoring.models import MonitoringSystem
from apps.authentication.models import User
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle
from apps.routes.models import Route
from apps.devices.models import Device


@pytest.fixture
def transportadora():
    """Cria um usuário transportadora."""
    return User.objects.create_user(
        username='transportadora1',
        email='transportadora1@example.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 1'
    )


@pytest.fixture
def gr_user():
    """Cria um usuário GR."""
    return User.objects.create_user(
        username='gr_user',
        email='gr@example.com',
        password='testpass123',
        user_type='GR',
        company_name='GR Logistics'
    )


@pytest.fixture
def driver(transportadora):
    """Cria um motorista."""
    return Driver.objects.create(
        transportadora=transportadora,
        nome='João Silva',
        cpf='123.456.789-01',
        rg='12.345.678-9',
        cnh='12345678901',
        nome_da_mae='Maria Silva',
        tipo_de_veiculo='Caminhão',
        telefone='11987654321',
        is_active=True
    )


@pytest.fixture
def vehicle(transportadora):
    """Cria um veículo."""
    return Vehicle.objects.create(
        transportadora=transportadora,
        placa='ABC1234',
        renavam='12345678901',
        chassi='9BWZZZ377VT004251',
        modelo='Caminhão Mercedes',
        ano=2020,
        cor='Branco',
        status='DISPONIVEL'
    )


@pytest.fixture
def route(transportadora):
    """Cria uma rota."""
    return Route.objects.create(
        transportadora=transportadora,
        name='São Paulo - Rio de Janeiro',
        origin_name='São Paulo',
        origin_address='Av. Paulista, 1000, São Paulo, SP',
        origin_latitude=Decimal('-23.5505000'),
        origin_longitude=Decimal('-46.6333000'),
        destination_name='Rio de Janeiro',
        destination_address='Av. Atlântica, 1000, Rio de Janeiro, RJ',
        destination_latitude=Decimal('-22.9068000'),
        destination_longitude=Decimal('-43.1729000'),
        distance_meters=430000,
        estimated_duration_seconds=18000,
        is_active=True
    )


@pytest.fixture
def device_updated(vehicle):
    """Cria um device atualizado recentemente (15 min atrás)."""
    device = Device.objects.create(
        vehicle=vehicle,
        suntech_device_id=123456,
        suntech_vehicle_id=789,
        last_address='Av. Paulista, 1000',
        last_speed=Decimal('60.00'),
        is_active=True
    )
    # Define última atualização como 15 minutos atrás
    device.last_system_date = timezone.now() - timedelta(minutes=15)
    device.save(update_fields=['last_system_date'])
    return device


@pytest.fixture
def device_outdated(vehicle):
    """Cria um device desatualizado (45 min atrás)."""
    device = Device.objects.create(
        vehicle=vehicle,
        suntech_device_id=123456,
        suntech_vehicle_id=789,
        last_address='Av. Paulista, 1000',
        last_speed=Decimal('60.00'),
        is_active=True
    )
    # Define última atualização como 45 minutos atrás
    device.last_system_date = timezone.now() - timedelta(minutes=45)
    device.save(update_fields=['last_system_date'])
    return device


@pytest.mark.django_db
class TestMonitoringSystemModel:
    """Testes para o modelo MonitoringSystem."""
    
    def test_create_sm_with_updated_device(self, transportadora, driver, vehicle, route, device_updated):
        """Testa criação de SM com device atualizado (deve funcionar)."""
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Monitoramento Teste',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            created_by=transportadora
        )
        
        assert sm.id is not None
        assert sm.identifier.startswith('SM-')
        assert sm.status == 'PLANEJADO'
        assert sm.device_was_updated is True
    
    def test_create_sm_with_outdated_device_fails(self, transportadora, driver, vehicle, route, device_outdated):
        """Testa que criação de SM com device desatualizado FALHA."""
        with pytest.raises(ValidationError) as exc_info:
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Monitoramento Teste',
                planned_start_date=timezone.now(),
                planned_end_date=timezone.now() + timedelta(days=2),
                device_validated_at=timezone.now()
            )
            sm.save()
        
        assert 'vehicle' in exc_info.value.message_dict
        assert 'não está atualizado' in str(exc_info.value)
        assert '45' in str(exc_info.value)  # minutos desde última atualização
    
    def test_create_sm_without_device_fails(self, transportadora, driver, vehicle, route):
        """Testa que criação de SM sem device FALHA."""
        with pytest.raises(ValidationError) as exc_info:
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Monitoramento Teste',
                planned_start_date=timezone.now(),
                planned_end_date=timezone.now() + timedelta(days=2),
                device_validated_at=timezone.now()
            )
            sm.save()
        
        assert 'vehicle' in exc_info.value.message_dict
        assert 'rastreador vinculado' in str(exc_info.value)
    
    def test_create_sm_with_inactive_device_fails(self, transportadora, driver, vehicle, route, device_updated):
        """Testa que criação de SM com device inativo FALHA."""
        device_updated.is_active = False
        device_updated.save()
        
        with pytest.raises(ValidationError) as exc_info:
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Monitoramento Teste',
                planned_start_date=timezone.now(),
                planned_end_date=timezone.now() + timedelta(days=2),
                device_validated_at=timezone.now()
            )
            sm.save()
        
        assert 'vehicle' in exc_info.value.message_dict
        assert 'inativo' in str(exc_info.value)
    
    @freeze_time("2025-01-15 10:00:00")
    def test_device_validation_at_30_minute_boundary(self, transportadora, driver, vehicle, route):
        """Testa validação exatamente no limite de 30 minutos."""
        device = Device.objects.create(
            vehicle=vehicle,
            suntech_device_id=123456,
            suntech_vehicle_id=789,
            last_system_date=timezone.now() - timedelta(minutes=30),
            last_address='Av. Paulista, 1000',
            is_active=True
        )
        
        # Exatamente 30 minutos deve falhar (threshold é < 30, não <=)
        with pytest.raises(ValidationError):
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Monitoramento Teste',
                planned_start_date=timezone.now(),
                planned_end_date=timezone.now() + timedelta(days=2),
                device_validated_at=timezone.now()
            )
            sm.save()
    
    @freeze_time("2025-01-15 10:00:00")
    def test_device_validation_at_29_minutes(self, transportadora, driver, vehicle, route):
        """Testa validação com 29 minutos (deve passar)."""
        device = Device.objects.create(
            vehicle=vehicle,
            suntech_device_id=123456,
            suntech_vehicle_id=789,
            last_system_date=timezone.now() - timedelta(minutes=29),
            last_address='Av. Paulista, 1000',
            is_active=True
        )
        
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Monitoramento Teste',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            created_by=transportadora
        )
        
        assert sm.id is not None
        assert sm.device_was_updated is True
    
    def test_sm_str(self, transportadora, driver, vehicle, route, device_updated):
        """Testa a representação em string do SM."""
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Viagem SP-RJ',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            created_by=transportadora
        )
        
        assert 'SM-' in str(sm)
        assert 'Viagem SP-RJ' in str(sm)
    
    def test_sm_identifier_auto_generation(self, transportadora, driver, vehicle, route, device_updated):
        """Testa geração automática do identifier."""
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Test',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            created_by=transportadora
        )
        
        assert sm.identifier.startswith('SM-2025-')  # Ano atual
        assert len(sm.identifier.split('-')) == 3
    
    def test_sm_duration_days_property(self, transportadora, driver, vehicle, route, device_updated):
        """Testa propriedade duration_days."""
        start = timezone.now()
        end = start + timedelta(days=3)
        
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Test',
            planned_start_date=start,
            planned_end_date=end,
            device_validated_at=timezone.now(),
            created_by=transportadora
        )
        
        assert sm.duration_days == 3
    
    def test_sm_is_in_progress_property(self, transportadora, driver, vehicle, route, device_updated):
        """Testa propriedade is_in_progress."""
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Test',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            status='PLANEJADO',
            created_by=transportadora
        )
        
        assert sm.is_in_progress is False
        
        sm.status = 'EM_ANDAMENTO'
        sm.save()
        
        assert sm.is_in_progress is True
    
    def test_sm_device_status_property(self, transportadora, driver, vehicle, route, device_updated):
        """Testa propriedade device_status."""
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Test',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            created_by=transportadora
        )
        
        assert sm.device_status is True  # Device foi atualizado recentemente
    
    def test_start_monitoring(self, transportadora, driver, vehicle, route, device_updated):
        """Testa método start_monitoring."""
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Test',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            created_by=transportadora
        )
        
        sm.start_monitoring()
        
        assert sm.status == 'EM_ANDAMENTO'
        assert sm.actual_start_date is not None
        
        vehicle.refresh_from_db()
        assert vehicle.status == 'EM_VIAGEM'
    
    def test_complete_monitoring(self, transportadora, driver, vehicle, route, device_updated):
        """Testa método complete_monitoring."""
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Test',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            status='EM_ANDAMENTO',
            created_by=transportadora
        )
        
        vehicle.status = 'EM_VIAGEM'
        vehicle.save()
        
        sm.complete_monitoring()
        
        assert sm.status == 'CONCLUIDO'
        assert sm.actual_end_date is not None
        
        vehicle.refresh_from_db()
        assert vehicle.status == 'DISPONIVEL'
    
    def test_cancel_monitoring(self, transportadora, driver, vehicle, route, device_updated):
        """Testa método cancel_monitoring."""
        sm = MonitoringSystem.objects.create(
            transportadora=transportadora,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Test',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=2),
            device_validated_at=timezone.now(),
            status='EM_ANDAMENTO',
            created_by=transportadora
        )
        
        vehicle.status = 'EM_VIAGEM'
        vehicle.save()
        
        sm.cancel_monitoring(reason='Problema mecânico')
        
        assert sm.status == 'CANCELADO'
        assert 'Problema mecânico' in sm.observations
        
        vehicle.refresh_from_db()
        assert vehicle.status == 'DISPONIVEL'
    
    def test_validation_different_transportadora_route(self, transportadora, driver, vehicle, route, device_updated):
        """Testa validação de rota de outra transportadora."""
        other_transportadora = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            user_type='TRANSPORTADORA',
            company_name='Other'
        )
        
        route.transportadora = other_transportadora
        route.save()
        
        with pytest.raises(ValidationError) as exc_info:
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Test',
                planned_start_date=timezone.now(),
                planned_end_date=timezone.now() + timedelta(days=2),
                device_validated_at=timezone.now()
            )
            sm.save()
        
        assert 'route' in exc_info.value.message_dict
    
    def test_validation_inactive_driver(self, transportadora, driver, vehicle, route, device_updated):
        """Testa validação de motorista inativo."""
        driver.is_active = False
        driver.save()
        
        with pytest.raises(ValidationError) as exc_info:
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Test',
                planned_start_date=timezone.now(),
                planned_end_date=timezone.now() + timedelta(days=2),
                device_validated_at=timezone.now()
            )
            sm.save()
        
        assert 'driver' in exc_info.value.message_dict
    
    def test_validation_vehicle_in_maintenance(self, transportadora, driver, vehicle, route, device_updated):
        """Testa validação de veículo em manutenção."""
        vehicle.status = 'MANUTENCAO'
        vehicle.save()
        
        with pytest.raises(ValidationError) as exc_info:
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Test',
                planned_start_date=timezone.now(),
                planned_end_date=timezone.now() + timedelta(days=2),
                device_validated_at=timezone.now()
            )
            sm.save()
        
        assert 'vehicle' in exc_info.value.message_dict
    
    def test_validation_inactive_route(self, transportadora, driver, vehicle, route, device_updated):
        """Testa validação de rota inativa."""
        route.is_active = False
        route.save()
        
        with pytest.raises(ValidationError) as exc_info:
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Test',
                planned_start_date=timezone.now(),
                planned_end_date=timezone.now() + timedelta(days=2),
                device_validated_at=timezone.now()
            )
            sm.save()
        
        assert 'route' in exc_info.value.message_dict
    
    def test_validation_end_date_before_start_date(self, transportadora, driver, vehicle, route, device_updated):
        """Testa validação de data de término antes do início."""
        start = timezone.now()
        end = start - timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            sm = MonitoringSystem(
                transportadora=transportadora,
                route=route,
                driver=driver,
                vehicle=vehicle,
                name='Test',
                planned_start_date=start,
                planned_end_date=end,
                device_validated_at=timezone.now()
            )
            sm.save()
        
        assert 'planned_end_date' in exc_info.value.message_dict
