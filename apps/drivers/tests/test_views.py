"""
Testes das views de motoristas.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.drivers.models import Driver
from apps.drivers.tests.factories import DriverFactory
from apps.authentication.tests.factories import UserTransportadoraFactory


@pytest.mark.django_db
class TestDriverViewSet:
    """Testes do ViewSet de motoristas."""
    
    def test_list_drivers_as_gr(self, authenticated_client_gr):
        """Testa que GR pode listar todos os motoristas."""
        DriverFactory.create_batch(3)
        
        url = reverse('drivers:driver-list')
        response = authenticated_client_gr.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 3
    
    def test_list_drivers_as_transportadora_sees_only_own(self, authenticated_client_transportadora, user_transportadora):
        """Testa que Transportadora vê apenas seus próprios motoristas."""
        # Motoristas da transportadora autenticada
        DriverFactory.create_batch(2, transportadora=user_transportadora)
        
        # Motoristas de outra transportadora (não devem aparecer)
        other_transportadora = UserTransportadoraFactory()
        DriverFactory.create_batch(3, transportadora=other_transportadora)
        
        url = reverse('drivers:driver-list')
        response = authenticated_client_transportadora.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        
        # Todos motoristas retornados devem pertencer à transportadora autenticada
        for driver_data in response.data['results']:
            assert driver_data['transportadora_nome'] == user_transportadora.company_name
    
    def test_list_drivers_unauthenticated_fails(self, api_client):
        """Testa que não autenticado não pode listar."""
        url = reverse('drivers:driver-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_driver_as_transportadora(self, authenticated_client_transportadora, user_transportadora):
        """Testa criação de motorista por transportadora."""
        url = reverse('drivers:driver-list')
        data = {
            'nome': 'José da Silva',
            'cpf': '123.456.789-00',
            'rg': '12.345.678-9',
            'cnh': '12345678901',
            'nome_do_pai': 'João da Silva',
            'nome_da_mae': 'Maria da Silva',
            'tipo_de_veiculo': 'Caminhão',
            'data_nascimento': '1985-05-15',
            'telefone': '(11) 98765-4321',
            'email': 'jose@test.com',
            'endereco': 'Rua Teste, 123'
        }
        response = authenticated_client_transportadora.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nome'] == 'José da Silva'
        assert response.data['cpf'] == '123.456.789-00'
        
        # Verifica que foi auto-atribuído à transportadora autenticada
        driver = Driver.objects.get(cpf='123.456.789-00')
        assert driver.transportadora == user_transportadora
    
    def test_create_driver_duplicate_cpf_fails(self, authenticated_client_transportadora):
        """Testa que não pode criar motorista com CPF duplicado."""
        DriverFactory(cpf='123.456.789-00')
        
        url = reverse('drivers:driver-list')
        data = {
            'nome': 'José da Silva',
            'cpf': '123.456.789-00',  # CPF já existe
            'rg': '12.345.678-9',
            'cnh': '12345678901',
            'nome_do_pai': 'João da Silva',
            'nome_da_mae': 'Maria da Silva',
            'tipo_de_veiculo': 'Caminhão',
            'data_nascimento': '1985-05-15',
            'telefone': '(11) 98765-4321',
            'endereco': 'Rua Teste, 123'
        }
        response = authenticated_client_transportadora.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'cpf' in str(response.data).lower()
    
    def test_retrieve_driver_as_owner(self, authenticated_client_transportadora, user_transportadora):
        """Testa obter detalhes de motorista próprio."""
        driver = DriverFactory(transportadora=user_transportadora)
        
        url = reverse('drivers:driver-detail', kwargs={'pk': driver.id})
        response = authenticated_client_transportadora.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == driver.id
        assert response.data['nome'] == driver.nome
    
    def test_retrieve_driver_as_gr(self, authenticated_client_gr):
        """Testa que GR pode ver qualquer motorista."""
        driver = DriverFactory()
        
        url = reverse('drivers:driver-detail', kwargs={'pk': driver.id})
        response = authenticated_client_gr.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == driver.id
    
    def test_retrieve_driver_from_other_transportadora_fails(self, authenticated_client_transportadora):
        """Testa que transportadora não pode ver motorista de outra."""
        other_transportadora = UserTransportadoraFactory()
        driver = DriverFactory(transportadora=other_transportadora)
        
        url = reverse('drivers:driver-detail', kwargs={'pk': driver.id})
        response = authenticated_client_transportadora.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_driver_as_owner(self, authenticated_client_transportadora, user_transportadora):
        """Testa atualização de motorista próprio."""
        driver = DriverFactory(transportadora=user_transportadora, nome='Nome Original')
        
        url = reverse('drivers:driver-detail', kwargs={'pk': driver.id})
        data = {
            'nome': 'Nome Atualizado',
            'cpf': driver.cpf,
            'rg': driver.rg,
            'cnh': driver.cnh,
            'nome_do_pai': driver.nome_do_pai,
            'nome_da_mae': driver.nome_da_mae,
            'tipo_de_veiculo': driver.tipo_de_veiculo,
            'data_nascimento': str(driver.data_nascimento),
            'telefone': driver.telefone,
            'endereco': driver.endereco
        }
        response = authenticated_client_transportadora.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nome'] == 'Nome Atualizado'
        
        driver.refresh_from_db()
        assert driver.nome == 'Nome Atualizado'
    
    def test_delete_driver_as_owner(self, authenticated_client_transportadora, user_transportadora):
        """Testa exclusão de motorista próprio."""
        driver = DriverFactory(transportadora=user_transportadora)
        
        url = reverse('drivers:driver-detail', kwargs={'pk': driver.id})
        response = authenticated_client_transportadora.delete(url)
        
        # A view personalizada retorna 200 com mensagem
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert not Driver.objects.filter(id=driver.id).exists()
    
    def test_filter_drivers_by_active_status(self, authenticated_client_gr):
        """Testa filtro por status ativo."""
        DriverFactory.create_batch(2, is_active=True)
        DriverFactory.create_batch(3, is_active=False)
        
        url = reverse('drivers:driver-list')
        response = authenticated_client_gr.get(url, {'is_active': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        for driver_data in response.data['results']:
            assert driver_data['is_active'] is True
    
    def test_filter_drivers_by_tipo_veiculo(self, authenticated_client_gr):
        """Testa filtro por tipo de veículo."""
        DriverFactory.create_batch(2, tipo_de_veiculo='Caminhão')
        DriverFactory.create_batch(3, tipo_de_veiculo='Carreta')
        
        url = reverse('drivers:driver-list')
        response = authenticated_client_gr.get(url, {'tipo_de_veiculo': 'Caminhão'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        for driver_data in response.data['results']:
            assert driver_data['tipo_de_veiculo'] == 'Caminhão'
    
    def test_search_drivers_by_name(self, authenticated_client_gr):
        """Testa busca por nome."""
        DriverFactory(nome='João Silva')
        DriverFactory(nome='Maria Santos')
        DriverFactory(nome='Pedro Oliveira')
        
        url = reverse('drivers:driver-list')
        response = authenticated_client_gr.get(url, {'search': 'João'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert 'João' in response.data['results'][0]['nome']
    
    def test_search_drivers_by_cpf(self, authenticated_client_gr):
        """Testa busca por CPF."""
        driver = DriverFactory(cpf='123.456.789-00')
        DriverFactory(cpf='987.654.321-00')
        
        url = reverse('drivers:driver-list')
        response = authenticated_client_gr.get(url, {'search': '123.456'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['cpf'] == '123.456.789-00'


@pytest.mark.django_db
class TestDriverCustomActions:
    """Testes das ações customizadas do ViewSet."""
    
    def test_active_drivers_action(self, authenticated_client_gr):
        """Testa action que lista apenas motoristas ativos."""
        DriverFactory.create_batch(3, is_active=True)
        DriverFactory.create_batch(2, is_active=False)
        
        url = reverse('drivers:driver-active')
        response = authenticated_client_gr.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # A action retorna uma lista direta, sem paginação
        assert len(response.data) == 3
        for driver_data in response.data:
            assert driver_data['is_active'] is True
    
    def test_activate_driver_action(self, authenticated_client_transportadora, user_transportadora):
        """Testa action de ativar motorista."""
        driver = DriverFactory(transportadora=user_transportadora, is_active=False)
        
        url = reverse('drivers:driver-activate', kwargs={'pk': driver.id})
        response = authenticated_client_transportadora.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        driver.refresh_from_db()
        assert driver.is_active is True
    
    def test_deactivate_driver_action(self, authenticated_client_transportadora, user_transportadora):
        """Testa action de desativar motorista."""
        driver = DriverFactory(transportadora=user_transportadora, is_active=True)
        
        url = reverse('drivers:driver-deactivate', kwargs={'pk': driver.id})
        response = authenticated_client_transportadora.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        driver.refresh_from_db()
        assert driver.is_active is False
