"""
Testes para as views de geocoding.
"""
import pytest
import responses
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User
from apps.routes.osm_service import OSMServiceError


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


@pytest.mark.django_db
class TestGeocodeView:
    """Testes para GeocodeView."""
    
    @responses.activate
    def test_geocode_success(self, api_client, gr_user):
        """Testa geocodificação bem-sucedida."""
        nominatim_response = [
            {
                'lat': '-23.5505199',
                'lon': '-46.6333094',
                'display_name': 'Avenida Paulista, São Paulo, SP'
            }
        ]
        
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/search',
            json=nominatim_response,
            status=200
        )
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/geocode/'
        
        data = {
            'address': 'Av. Paulista, 1000, São Paulo, SP'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['latitude'] == pytest.approx(-23.5505199, abs=0.0001)
        assert response.data['longitude'] == pytest.approx(-46.6333094, abs=0.0001)
    
    def test_geocode_unauthenticated(self, api_client):
        """Testa que usuário não autenticado não pode geocodificar."""
        url = '/api/routes/geocode/'
        
        data = {
            'address': 'Av. Paulista, 1000'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_geocode_empty_address(self, api_client, gr_user):
        """Testa validação de endereço vazio."""
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/geocode/'
        
        data = {
            'address': '   '
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @responses.activate
    def test_geocode_not_found(self, api_client, gr_user):
        """Testa quando endereço não é encontrado."""
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/search',
            json=[],
            status=200
        )
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/geocode/'
        
        data = {
            'address': 'Endereço Inexistente 99999'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
    
    @patch('apps.routes.views.geocode_address')
    def test_geocode_service_error(self, mock_geocode, api_client, gr_user):
        """Testa erro no serviço de geocodificação."""
        mock_geocode.side_effect = OSMServiceError('Service unavailable')
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/geocode/'
        
        data = {
            'address': 'Av. Paulista, 1000'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data['success'] is False


@pytest.mark.django_db
class TestReverseGeocodeView:
    """Testes para ReverseGeocodeView."""
    
    @responses.activate
    def test_reverse_geocode_success(self, api_client, gr_user):
        """Testa reverse geocoding bem-sucedido."""
        nominatim_response = {
            'display_name': 'Avenida Paulista, 1000, São Paulo, SP, Brasil'
        }
        
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/reverse',
            json=nominatim_response,
            status=200
        )
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/reverse-geocode/'
        
        data = {
            'latitude': -23.5505,
            'longitude': -46.6333
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'Avenida Paulista' in response.data['address']
    
    def test_reverse_geocode_unauthenticated(self, api_client):
        """Testa que usuário não autenticado não pode usar reverse geocode."""
        url = '/api/routes/reverse-geocode/'
        
        data = {
            'latitude': -23.5505,
            'longitude': -46.6333
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_reverse_geocode_invalid_latitude(self, api_client, gr_user):
        """Testa validação de latitude inválida."""
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/reverse-geocode/'
        
        data = {
            'latitude': 91.0,  # Inválido
            'longitude': -46.6333
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_reverse_geocode_invalid_longitude(self, api_client, gr_user):
        """Testa validação de longitude inválida."""
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/reverse-geocode/'
        
        data = {
            'latitude': -23.5505,
            'longitude': 181.0  # Inválido
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @responses.activate
    def test_reverse_geocode_not_found(self, api_client, gr_user):
        """Testa quando coordenadas não são encontradas."""
        nominatim_response = {
            'error': 'Unable to geocode'
        }
        
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/reverse',
            json=nominatim_response,
            status=200
        )
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/reverse-geocode/'
        
        data = {
            'latitude': 0.0,
            'longitude': 0.0
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
    
    @patch('apps.routes.views.reverse_geocode')
    def test_reverse_geocode_service_error(self, mock_reverse, api_client, gr_user):
        """Testa erro no serviço de reverse geocoding."""
        mock_reverse.side_effect = OSMServiceError('Service unavailable')
        
        api_client.force_authenticate(user=gr_user)
        url = '/api/routes/reverse-geocode/'
        
        data = {
            'latitude': -23.5505,
            'longitude': -46.6333
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data['success'] is False
