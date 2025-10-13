"""
Testes para as views do app Monitoring.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from freezegun import freeze_time
from apps.monitoring.models import MonitoringSystem
from apps.authentication.models import User
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle
from apps.routes.models import Route
from apps.devices.models import Device


@pytest.fixture
def api_client():
    """Cliente da API."""
    return APIClient()


@pytest.fixture
def gr_user(db):
    """Cria um usuário GR."""
    return User.objects.create_user(
        username='gr_user',
        email='gr@example.com',
        password='testpass123',
        user_type='GR',
        company_name='GR Logistics'
    )


@pytest.fixture
def transportadora1(db):
    """Cria uma transportadora."""
    return User.objects.create_user(
        username='transportadora1',
        email='transportadora1@example.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 1',
        cnpj='12.345.678/0001-90'
    )


@pytest.fixture
def transportadora2(db):
    """Cria outra transportadora."""
    return User.objects.create_user(
        username='transportadora2',
        email='transportadora2@example.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 2',
        cnpj='98.765.432/0001-10'
    )


@pytest.fixture
def driver(transportadora1):
    """Cria um motorista."""
    return Driver.objects.create(
        transportadora=transportadora1,
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
def vehicle(transportadora1):
    """Cria um veículo."""
    return Vehicle.objects.create(
        transportadora=transportadora1,
        placa='ABC1234',
        renavam='12345678901',
        chassi='9BWZZZ377VT004251',
        modelo='Caminhão Mercedes',
        ano=2020,
        cor='Branco',
        status='DISPONIVEL'
    )


@pytest.fixture
def route(transportadora1):
    """Cria uma rota."""
    return Route.objects.create(
        transportadora=transportadora1,
        name='São Paulo - Rio de Janeiro',
        origin_name='São Paulo',
        origin_address='Av. Paulista, 1000, São Paulo, SP',
        origin_latitude=Decimal('-23.550500'),
        origin_longitude=Decimal('-46.633300'),
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
    """Cria um device atualizado recentemente."""
    device = Device.objects.create(
        vehicle=vehicle,
        suntech_device_id=123456,
        suntech_vehicle_id=789,
        last_address='Av. Paulista, 1000',
        last_speed=Decimal('60.00'),
        is_active=True
    )
    device.last_system_date = timezone.now() - timedelta(minutes=15)
    device.save(update_fields=['last_system_date'])
    return device


@pytest.fixture
def monitoring_system(transportadora1, driver, vehicle, route, device_updated):
    """Cria um sistema de monitoramento."""
    return MonitoringSystem.objects.create(
        transportadora=transportadora1,
        route=route,
        driver=driver,
        vehicle=vehicle,
        name='Viagem SP-RJ',
        planned_start_date=timezone.now(),
        planned_end_date=timezone.now() + timedelta(days=2),
        device_validated_at=timezone.now(),
        created_by=transportadora1,
        status='PLANEJADO'
    )


@pytest.mark.django_db
class TestMonitoringSystemViewSet:
    """Testes para o MonitoringSystemViewSet."""
    
    def test_list_monitoring_systems_unauthenticated(self, api_client):
        """Testa que usuário não autenticado não pode listar SMs."""
        url = reverse('monitoring-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_monitoring_systems_as_gr(self, api_client, gr_user, monitoring_system):
        """Testa que GR vê todos os SMs."""
        api_client.force_authenticate(user=gr_user)
        url = reverse('monitoring-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['identifier'] == monitoring_system.identifier
    
    def test_list_monitoring_systems_as_transportadora(self, api_client, transportadora1, transportadora2, 
                                                        monitoring_system, driver, vehicle, route, device_updated):
        """Testa que transportadora vê apenas seus próprios SMs."""
        # Cria SM da transportadora2
        driver2 = Driver.objects.create(
            transportadora=transportadora2,
            nome='Pedro Santos',
            cpf='987.654.321-00',
            rg='98.765.432-1',
            cnh='98765432100',
            nome_da_mae='Ana Santos',
            tipo_de_veiculo='Caminhão',
            telefone='11987654322',
            is_active=True
        )
        vehicle2 = Vehicle.objects.create(
            transportadora=transportadora2,
            placa='XYZ5678',
            renavam='98765432100',
            chassi='9BWZZZ377VT004252',
            modelo='Caminhão Volvo',
            ano=2021,
            cor='Azul',
            status='DISPONIVEL'
        )
        route2 = Route.objects.create(
            transportadora=transportadora2,
            name='Curitiba - Porto Alegre',
            origin_name='Curitiba',
            origin_address='Curitiba, PR',
            origin_latitude=Decimal('-25.4284000'),
            origin_longitude=Decimal('-49.2733000'),
            destination_name='Porto Alegre',
            destination_address='Porto Alegre, RS',
            destination_latitude=Decimal('-30.0346000'),
            destination_longitude=Decimal('-51.2177000'),
            distance_meters=711000,
            estimated_duration_seconds=28800,
            is_active=True
        )
        device2 = Device.objects.create(
            vehicle=vehicle2,
            suntech_device_id=654321,
            suntech_vehicle_id=987,
            last_address='Curitiba, PR',
            last_system_date=timezone.now() - timedelta(minutes=10),
            is_active=True
        )
        
        sm2 = MonitoringSystem.objects.create(
            transportadora=transportadora2,
            route=route2,
            driver=driver2,
            vehicle=vehicle2,
            name='Viagem CWB-POA',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=1),
            device_validated_at=timezone.now(),
            created_by=transportadora2
        )
        
        # Transportadora1 vê apenas seu SM
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['identifier'] == monitoring_system.identifier
    
    def test_create_monitoring_system_with_updated_device(self, api_client, transportadora1, 
                                                          driver, vehicle, route, device_updated):
        """Testa criação de SM com device atualizado."""
        api_client.force_authenticate(user=transportadora1)
        
        # Adiciona dados de posição ao device (max_digits=10, decimal_places=7)
        device_updated.last_latitude = Decimal('-23.5505')
        device_updated.last_longitude = Decimal('-46.6333')
        device_updated.last_address = 'São Paulo, SP'
        device_updated.save()
        
        url = reverse('monitoring-list')
        
        start_date = timezone.now()
        end_date = start_date + timedelta(days=2)
        
        data = {
            'transportadora': transportadora1.id,
            'route': route.id,
            'driver': driver.id,
            'vehicle': vehicle.id,
            'name': 'Nova Viagem',
            'planned_start_date': start_date.isoformat(),
            'planned_end_date': end_date.isoformat(),
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Nova Viagem'
        
        # Verificar que o SM foi criado com device_was_updated = True
        sm = MonitoringSystem.objects.get(name='Nova Viagem')
        assert sm.device_was_updated is True
        assert sm.device_validated_at is not None
    
    def test_create_monitoring_system_with_outdated_device(self, api_client, transportadora1, 
                                                           driver, vehicle, route):
        """Testa que criação de SM com device desatualizado FALHA."""
        # Cria device desatualizado
        device = Device.objects.create(
            vehicle=vehicle,
            suntech_device_id=123456,
            suntech_vehicle_id=789,
            last_address='Av. Paulista, 1000',
            last_system_date=timezone.now() - timedelta(minutes=45),
            is_active=True
        )
        
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-list')
        
        start_date = timezone.now()
        end_date = start_date + timedelta(days=2)
        
        data = {
            'transportadora': transportadora1.id,
            'route': route.id,
            'driver': driver.id,
            'vehicle': vehicle.id,
            'name': 'Nova Viagem',
            'planned_start_date': start_date.isoformat(),
            'planned_end_date': end_date.isoformat(),
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'não está atualizado' in str(response.data)
    
    def test_retrieve_monitoring_system(self, api_client, transportadora1, monitoring_system):
        """Testa recuperação de um SM específico."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-detail', kwargs={'pk': monitoring_system.pk})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['identifier'] == monitoring_system.identifier
        assert response.data['name'] == 'Viagem SP-RJ'
    
    def test_update_monitoring_system(self, api_client, transportadora1, monitoring_system):
        """Testa atualização de um SM."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-detail', kwargs={'pk': monitoring_system.pk})
        
        data = {
            'name': 'Viagem SP-RJ Atualizada',
            'observations': 'Observações atualizadas'
        }
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Viagem SP-RJ Atualizada'
        assert response.data['observations'] == 'Observações atualizadas'
    
    def test_delete_monitoring_system(self, api_client, transportadora1, monitoring_system):
        """Testa exclusão de um SM."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-detail', kwargs={'pk': monitoring_system.pk})
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not MonitoringSystem.objects.filter(pk=monitoring_system.pk).exists()
    
    def test_action_active_monitoring_systems(self, api_client, transportadora1, monitoring_system):
        """Testa ação para listar apenas SMs ativos."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-active')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['data']) == 1
    
    def test_action_in_progress_monitoring_systems(self, api_client, transportadora1, monitoring_system):
        """Testa ação para listar apenas SMs em andamento."""
        monitoring_system.status = 'EM_ANDAMENTO'
        monitoring_system.save()
        
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-in-progress')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['status'] == 'EM_ANDAMENTO'
    
    def test_action_completed_monitoring_systems(self, api_client, transportadora1, monitoring_system):
        """Testa ação para listar apenas SMs concluídos."""
        monitoring_system.status = 'CONCLUIDO'
        monitoring_system.save()
        
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-completed')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['status'] == 'CONCLUIDO'
    
    def test_action_start_monitoring(self, api_client, transportadora1, monitoring_system, vehicle):
        """Testa ação de iniciar monitoramento."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-start', kwargs={'pk': monitoring_system.pk})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        monitoring_system.refresh_from_db()
        assert monitoring_system.status == 'EM_ANDAMENTO'
        assert monitoring_system.actual_start_date is not None
        
        vehicle.refresh_from_db()
        assert vehicle.status == 'EM_VIAGEM'
    
    def test_action_complete_monitoring(self, api_client, transportadora1, monitoring_system, vehicle):
        """Testa ação de completar monitoramento."""
        # Inicia o monitoramento primeiro
        monitoring_system.start_monitoring()
        
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-complete', kwargs={'pk': monitoring_system.pk})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        monitoring_system.refresh_from_db()
        assert monitoring_system.status == 'CONCLUIDO'
        assert monitoring_system.actual_end_date is not None
        
        vehicle.refresh_from_db()
        assert vehicle.status == 'DISPONIVEL'
    
    def test_action_cancel_monitoring(self, api_client, transportadora1, monitoring_system, vehicle):
        """Testa ação de cancelar monitoramento."""
        # Inicia o monitoramento primeiro
        monitoring_system.start_monitoring()
        
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-cancel', kwargs={'pk': monitoring_system.pk})
        
        data = {'reason': 'Problema mecânico no veículo'}
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        monitoring_system.refresh_from_db()
        assert monitoring_system.status == 'CANCELADO'
        assert 'Problema mecânico' in monitoring_system.observations
        
        vehicle.refresh_from_db()
        assert vehicle.status == 'DISPONIVEL'
    
    def test_action_vehicle_position(self, api_client, transportadora1, monitoring_system, device_updated):
        """Testa ação para obter posição atual do veículo."""
        # Adiciona dados de posição ao device (max_digits=10, decimal_places=7)
        device_updated.last_latitude = Decimal('-23.5505')
        device_updated.last_longitude = Decimal('-46.6333')
        device_updated.last_address = 'São Paulo, SP'
        device_updated.save()
        
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-vehicle-position', kwargs={'pk': monitoring_system.pk})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'position' in response.data
        assert float(response.data['position']['latitude']) == -23.5505
    
    def test_filter_by_status(self, api_client, transportadora1, monitoring_system):
        """Testa filtro por status."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-list')
        response = api_client.get(url, {'status': 'PLANEJADO'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == 'PLANEJADO'
    
    def test_filter_by_driver(self, api_client, transportadora1, monitoring_system, driver):
        """Testa filtro por motorista."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-list')
        response = api_client.get(url, {'driver': driver.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_filter_by_vehicle(self, api_client, transportadora1, monitoring_system, vehicle):
        """Testa filtro por veículo."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-list')
        response = api_client.get(url, {'vehicle': vehicle.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_search_by_identifier(self, api_client, transportadora1, monitoring_system):
        """Testa busca por identificador."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-list')
        response = api_client.get(url, {'search': monitoring_system.identifier})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_search_by_driver_name(self, api_client, transportadora1, monitoring_system):
        """Testa busca por nome do motorista."""
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-list')
        response = api_client.get(url, {'search': 'João'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_ordering_by_created_at(self, api_client, transportadora1, monitoring_system, 
                                     driver, vehicle, route, device_updated):
        """Testa ordenação por data de criação."""
        # Cria outro SM
        sm2 = MonitoringSystem.objects.create(
            transportadora=transportadora1,
            route=route,
            driver=driver,
            vehicle=vehicle,
            name='Viagem 2',
            planned_start_date=timezone.now(),
            planned_end_date=timezone.now() + timedelta(days=1),
            device_validated_at=timezone.now(),
            created_by=transportadora1
        )
        
        api_client.force_authenticate(user=transportadora1)
        url = reverse('monitoring-list')
        response = api_client.get(url, {'ordering': '-created_at'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        # Mais recente primeiro
        assert response.data['results'][0]['name'] == 'Viagem 2'
    
    def test_transportadora_cannot_access_other_sm(self, api_client, transportadora1, transportadora2, 
                                                    monitoring_system):
        """Testa que transportadora não pode acessar SM de outra transportadora."""
        api_client.force_authenticate(user=transportadora2)
        url = reverse('monitoring-detail', kwargs={'pk': monitoring_system.pk})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
