"""
Testes para as views do app Routes.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from apps.routes.models import Route
from apps.authentication.models import User


@pytest.fixture
def api_client():
    """Retorna um API client."""
    return APIClient()


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
def transportadora1():
    """Cria transportadora 1."""
    return User.objects.create_user(
        username='transportadora1',
        email='transportadora1@example.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 1'
    )


@pytest.fixture
def transportadora2():
    """Cria transportadora 2."""
    return User.objects.create_user(
        username='transportadora2',
        email='transportadora2@example.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 2'
    )


@pytest.fixture
def route1(transportadora1):
    """Cria rota para transportadora 1."""
    return Route.objects.create(
        transportadora=transportadora1,
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
def route2(transportadora2):
    """Cria rota para transportadora 2."""
    return Route.objects.create(
        transportadora=transportadora2,
        name='Campinas - Santos',
        origin_name='Campinas',
        origin_address='Centro, Campinas, SP',
        origin_latitude=Decimal('-22.9056700'),
        origin_longitude=Decimal('-47.0608300'),
        destination_name='Santos',
        destination_address='Centro, Santos, SP',
        destination_latitude=Decimal('-23.9608700'),
        destination_longitude=Decimal('-46.3335300'),
        is_active=True
    )


@pytest.mark.django_db
class TestRouteViewSet:
    """Testes para RouteViewSet."""
    
    def test_list_routes_unauthenticated(self, api_client):
        """Testa que usuário não autenticado não pode listar rotas."""
        url = '/api/routes/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_routes_as_gr(self, api_client, gr_user, route1, route2):
        """Testa que GR pode ver todas as rotas."""
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_list_routes_as_transportadora(self, api_client, transportadora1, route1, route2):
        """Testa que transportadora vê apenas suas rotas."""
        api_client.force_authenticate(user=transportadora1)
        url = '/api/routes/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'São Paulo - Rio de Janeiro'
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_create_route_as_gr(self, mock_calculate, api_client, gr_user, transportadora1):
        """Testa criação de rota como GR."""
        mock_calculate.return_value = {
            'distance': 100000,
            'duration': 3600,
            'geometry': {'type': 'LineString', 'coordinates': []}
        }
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/'
        
        data = {
            'transportadora': transportadora1.id,
            'name': 'Teste Rota',
            'origin_name': 'A',
            'origin_address': 'Address A',
            'origin_latitude': '-23.5505000',
            'origin_longitude': '-46.6333000',
            'destination_name': 'B',
            'destination_address': 'Address B',
            'destination_latitude': '-22.9068000',
            'destination_longitude': '-43.1729000'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Teste Rota'
        assert response.data['transportadora'] == transportadora1.id
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_create_route_as_transportadora(self, mock_calculate, api_client, transportadora1):
        """Testa criação de rota como transportadora."""
        mock_calculate.return_value = {
            'distance': 100000,
            'duration': 3600,
            'geometry': {'type': 'LineString', 'coordinates': []}
        }
        
        api_client.force_authenticate(user=transportadora1)
        url = '/api/routes/'
        
        data = {
            'transportadora': transportadora1.id,  # Necessário no serializer
            'name': 'Minha Rota',
            'origin_name': 'A',
            'origin_address': 'Address A',
            'origin_latitude': '-23.5505000',
            'origin_longitude': '-46.6333000',
            'destination_name': 'B',
            'destination_address': 'Address B',
            'destination_latitude': '-22.9068000',
            'destination_longitude': '-43.1729000'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['transportadora'] == transportadora1.id
    
    def test_create_route_same_origin_destination(self, api_client, gr_user, transportadora1):
        """Testa validação de origem e destino iguais."""
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/'
        
        data = {
            'transportadora': transportadora1.id,
            'name': 'Rota Inválida',
            'origin_name': 'A',
            'origin_address': 'Address A',
            'origin_latitude': '-23.5505000',
            'origin_longitude': '-46.6333000',
            'destination_name': 'A',
            'destination_address': 'Address A',
            'destination_latitude': '-23.5505000',
            'destination_longitude': '-46.6333000'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'diferentes' in str(response.data).lower()
    
    def test_retrieve_route(self, api_client, gr_user, route1):
        """Testa recuperação de detalhes da rota."""
        api_client.force_authenticate(user=gr_user)
        url = f'/api/routes/{route1.id}/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'São Paulo - Rio de Janeiro'
        assert 'distance_km' in response.data
        assert 'estimated_duration_formatted' in response.data
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_update_route(self, mock_calculate, api_client, gr_user, route1):
        """Testa atualização de rota."""
        mock_calculate.return_value = {
            'distance': 450000,
            'duration': 19000,
            'geometry': {'type': 'LineString', 'coordinates': []}
        }
        
        api_client.force_authenticate(user=gr_user)
        url = f'/api/routes/{route1.id}/'
        
        data = {
            'name': 'SP - RJ Atualizado',
            'destination_latitude': '-22.9100000'
        }
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'SP - RJ Atualizado'
    
    def test_delete_route(self, api_client, gr_user, route1):
        """Testa deleção de rota."""
        api_client.force_authenticate(user=gr_user)
        url = f'/api/routes/{route1.id}/'
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Route.objects.filter(id=route1.id).count() == 0
    
    def test_action_active_routes(self, api_client, gr_user, route1, route2):
        """Testa action de rotas ativas."""
        # Desativar route2
        route2.is_active = False
        route2.save()
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/active/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['data'][0]['name'] == 'São Paulo - Rio de Janeiro'
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_action_calculate_route_success(self, mock_calculate, api_client, gr_user, route1):
        """Testa action de calcular rota com sucesso."""
        mock_calculate.return_value = {
            'distance': 450000,
            'duration': 20000,
            'geometry': {'type': 'LineString', 'coordinates': []}
        }
        
        api_client.force_authenticate(user=gr_user)
        url = f'/api/routes/{route1.id}/calculate/'
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'calculada com sucesso' in response.data['message']
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_action_calculate_route_failure(self, mock_calculate, api_client, gr_user, route1):
        """Testa action de calcular rota com erro."""
        mock_calculate.side_effect = Exception('OSRM error')
        
        api_client.force_authenticate(user=gr_user)
        url = f'/api/routes/{route1.id}/calculate/'
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data['success'] is False
    
    def test_action_activate_route(self, api_client, gr_user, route1):
        """Testa action de ativar rota."""
        route1.is_active = False
        route1.save()
        
        api_client.force_authenticate(user=gr_user)
        url = f'/api/routes/{route1.id}/activate/'
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'ativada com sucesso' in response.data['message']
        
        route1.refresh_from_db()
        assert route1.is_active is True
    
    def test_action_deactivate_route(self, api_client, gr_user, route1):
        """Testa action de desativar rota."""
        api_client.force_authenticate(user=gr_user)
        url = f'/api/routes/{route1.id}/deactivate/'
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'desativada com sucesso' in response.data['message']
        
        route1.refresh_from_db()
        assert route1.is_active is False
    
    def test_search_route_by_name(self, api_client, gr_user, route1, route2):
        """Testa busca de rotas por nome."""
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/?search=Paulo'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert 'Paulo' in response.data['results'][0]['name']
    
    def test_filter_route_by_active_status(self, api_client, gr_user, route1, route2):
        """Testa filtro de rotas por status ativo."""
        route2.is_active = False
        route2.save()
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/?is_active=true'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_filter_route_by_transportadora(self, api_client, gr_user, route1, route2, transportadora1):
        """Testa filtro de rotas por transportadora."""
        api_client.force_authenticate(user=gr_user)
        url = f'/api/routes/?transportadora={transportadora1.id}'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'São Paulo - Rio de Janeiro'
    
    def test_ordering_routes(self, api_client, gr_user, route1, route2):
        """Testa ordenação de rotas."""
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/?ordering=name'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        names = [r['name'] for r in response.data['results']]
        assert names == sorted(names)
    
    def test_transportadora_cannot_access_other_routes(self, api_client, transportadora1, route2):
        """Testa que transportadora não pode acessar rotas de outros."""
        api_client.force_authenticate(user=transportadora1)
        url = f'/api/routes/{route2.id}/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
