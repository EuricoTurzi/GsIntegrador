"""
Testes das views de veículos.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.vehicles.models import Vehicle
from apps.vehicles.tests.factories import VehicleFactory
from apps.authentication.tests.factories import UserTransportadoraFactory


@pytest.mark.django_db
class TestVehicleViewSet:
    """Testes do ViewSet de veículos."""
    
    def test_list_vehicles_as_gr(self, authenticated_client_gr):
        """Testa que GR pode listar todos os veículos."""
        VehicleFactory.create_batch(3)
        
        url = reverse('vehicles:vehicle-list')
        response = authenticated_client_gr.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 3
    
    def test_list_vehicles_as_transportadora_sees_only_own(self, authenticated_client_transportadora, user_transportadora):
        """Testa que Transportadora vê apenas seus próprios veículos."""
        # Veículos da transportadora autenticada
        VehicleFactory.create_batch(2, transportadora=user_transportadora)
        
        # Veículos de outra transportadora (não devem aparecer)
        other_transportadora = UserTransportadoraFactory()
        VehicleFactory.create_batch(3, transportadora=other_transportadora)
        
        url = reverse('vehicles:vehicle-list')
        response = authenticated_client_transportadora.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_list_vehicles_unauthenticated_fails(self, api_client):
        """Testa que não autenticado não pode listar."""
        url = reverse('vehicles:vehicle-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_vehicle_as_transportadora(self, authenticated_client_transportadora, user_transportadora):
        """Testa criação de veículo por transportadora."""
        url = reverse('vehicles:vehicle-list')
        data = {
            'placa': 'XYZ9876',
            'ano': 2020,
            'cor': 'Branco',
            'modelo': 'Scania R450',
            'renavam': '98765432101',
            'chassi': '9BWZZZ377VT999999',
            'status': 'DISPONIVEL'
        }
        response = authenticated_client_transportadora.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['placa'] == 'XYZ9876'
        
        # Verifica que foi auto-atribuído à transportadora autenticada
        vehicle = Vehicle.objects.get(placa='XYZ9876')
        assert vehicle.transportadora == user_transportadora
    
    def test_create_vehicle_duplicate_placa_fails(self, authenticated_client_transportadora):
        """Testa que não pode criar veículo com placa duplicada."""
        VehicleFactory(placa='DUP1234')
        
        url = reverse('vehicles:vehicle-list')
        data = {
            'placa': 'DUP1234',  # Placa já existe
            'ano': 2020,
            'cor': 'Branco',
            'modelo': 'Scania R450',
            'renavam': '98765432102',
            'chassi': '9BWZZZ377VT999998',
            'status': 'DISPONIVEL'
        }
        response = authenticated_client_transportadora.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'placa' in str(response.data).lower()
    
    def test_retrieve_vehicle_as_owner(self, authenticated_client_transportadora, user_transportadora):
        """Testa obter detalhes de veículo próprio."""
        vehicle = VehicleFactory(transportadora=user_transportadora)
        
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': vehicle.id})
        response = authenticated_client_transportadora.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == vehicle.id
        assert response.data['placa'] == vehicle.placa
    
    def test_retrieve_vehicle_as_gr(self, authenticated_client_gr):
        """Testa que GR pode ver qualquer veículo."""
        vehicle = VehicleFactory()
        
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': vehicle.id})
        response = authenticated_client_gr.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == vehicle.id
    
    def test_retrieve_vehicle_from_other_transportadora_fails(self, authenticated_client_transportadora):
        """Testa que transportadora não pode ver veículo de outra."""
        other_transportadora = UserTransportadoraFactory()
        vehicle = VehicleFactory(transportadora=other_transportadora)
        
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': vehicle.id})
        response = authenticated_client_transportadora.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_vehicle_as_owner(self, authenticated_client_transportadora, user_transportadora):
        """Testa atualização de veículo próprio."""
        vehicle = VehicleFactory(transportadora=user_transportadora, cor='Preto')
        
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': vehicle.id})
        data = {
            'placa': vehicle.placa,
            'ano': vehicle.ano,
            'cor': 'Branco',  # Alterando cor
            'modelo': vehicle.modelo,
            'renavam': vehicle.renavam,
            'chassi': vehicle.chassi,
            'status': vehicle.status
        }
        response = authenticated_client_transportadora.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cor'] == 'Branco'
        
        vehicle.refresh_from_db()
        assert vehicle.cor == 'Branco'
    
    def test_delete_vehicle_as_owner(self, authenticated_client_transportadora, user_transportadora):
        """Testa exclusão de veículo próprio."""
        vehicle = VehicleFactory(transportadora=user_transportadora)
        
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': vehicle.id})
        response = authenticated_client_transportadora.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Vehicle.objects.filter(id=vehicle.id).exists()
    
    def test_filter_vehicles_by_status(self, authenticated_client_gr):
        """Testa filtro por status."""
        VehicleFactory.create_batch(2, status='DISPONIVEL')
        VehicleFactory.create_batch(3, status='EM_VIAGEM')
        
        url = reverse('vehicles:vehicle-list')
        response = authenticated_client_gr.get(url, {'status': 'DISPONIVEL'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        for vehicle_data in response.data['results']:
            assert vehicle_data['status'] == 'DISPONIVEL'
    
    def test_filter_vehicles_by_active_status(self, authenticated_client_gr):
        """Testa filtro por status ativo."""
        VehicleFactory.create_batch(2, is_active=True)
        VehicleFactory.create_batch(3, is_active=False)
        
        url = reverse('vehicles:vehicle-list')
        response = authenticated_client_gr.get(url, {'is_active': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        for vehicle_data in response.data['results']:
            assert vehicle_data['is_active'] is True
    
    def test_search_vehicles_by_placa(self, authenticated_client_gr):
        """Testa busca por placa."""
        VehicleFactory(placa='AAA1111')
        VehicleFactory(placa='BBB2222')
        VehicleFactory(placa='CCC3333')
        
        url = reverse('vehicles:vehicle-list')
        response = authenticated_client_gr.get(url, {'search': 'AAA'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert 'AAA' in response.data['results'][0]['placa']
    
    def test_search_vehicles_by_modelo(self, authenticated_client_gr):
        """Testa busca por modelo."""
        VehicleFactory(modelo='Scania R450')
        VehicleFactory(modelo='Volvo FH 460')
        
        url = reverse('vehicles:vehicle-list')
        response = authenticated_client_gr.get(url, {'search': 'Scania'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert 'Scania' in response.data['results'][0]['modelo']


@pytest.mark.django_db
class TestVehicleCustomActions:
    """Testes das ações customizadas do ViewSet."""
    
    def test_available_vehicles_action(self, authenticated_client_gr):
        """Testa action que lista apenas veículos disponíveis."""
        VehicleFactory.create_batch(2, status='DISPONIVEL', is_active=True)
        VehicleFactory(status='EM_VIAGEM', is_active=True)
        VehicleFactory(status='DISPONIVEL', is_active=False)
        
        url = reverse('vehicles:vehicle-available')
        response = authenticated_client_gr.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        for vehicle_data in response.data:
            assert vehicle_data['status'] == 'DISPONIVEL'
            assert vehicle_data['is_active'] is True
    
    def test_activate_vehicle_action(self, authenticated_client_transportadora, user_transportadora):
        """Testa action de ativar veículo."""
        vehicle = VehicleFactory(transportadora=user_transportadora, is_active=False)
        
        url = reverse('vehicles:vehicle-activate', kwargs={'pk': vehicle.id})
        response = authenticated_client_transportadora.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        
        vehicle.refresh_from_db()
        assert vehicle.is_active is True
    
    def test_deactivate_vehicle_action(self, authenticated_client_transportadora, user_transportadora):
        """Testa action de desativar veículo."""
        vehicle = VehicleFactory(transportadora=user_transportadora, is_active=True)
        
        url = reverse('vehicles:vehicle-deactivate', kwargs={'pk': vehicle.id})
        response = authenticated_client_transportadora.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        
        vehicle.refresh_from_db()
        assert vehicle.is_active is False
    
    def test_change_status_action_success(self, authenticated_client_transportadora, user_transportadora):
        """Testa action de alterar status do veículo."""
        vehicle = VehicleFactory(transportadora=user_transportadora, status='DISPONIVEL')
        
        url = reverse('vehicles:vehicle-change-status', kwargs={'pk': vehicle.id})
        data = {'status': 'EM_VIAGEM'}
        response = authenticated_client_transportadora.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        
        vehicle.refresh_from_db()
        assert vehicle.status == 'EM_VIAGEM'
    
    def test_change_status_action_without_status_fails(self, authenticated_client_transportadora, user_transportadora):
        """Testa que alterar status sem fornecer status falha."""
        vehicle = VehicleFactory(transportadora=user_transportadora)
        
        url = reverse('vehicles:vehicle-change-status', kwargs={'pk': vehicle.id})
        response = authenticated_client_transportadora.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_change_status_action_invalid_status_fails(self, authenticated_client_transportadora, user_transportadora):
        """Testa que alterar para status inválido falha."""
        vehicle = VehicleFactory(transportadora=user_transportadora)
        
        url = reverse('vehicles:vehicle-change-status', kwargs={'pk': vehicle.id})
        data = {'status': 'INVALID_STATUS'}
        response = authenticated_client_transportadora.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
