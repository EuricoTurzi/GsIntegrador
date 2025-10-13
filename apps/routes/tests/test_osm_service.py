"""
Testes para o serviço OSM (OpenStreetMap/OSRM).
"""
import pytest
import responses
from unittest.mock import patch
from apps.routes.osm_service import (
    calculate_route_osm,
    geocode_address,
    reverse_geocode,
    calculate_distance_haversine,
    OSMServiceError
)


@pytest.mark.django_db
class TestCalculateRouteOSM:
    """Testes para calculate_route_osm."""
    
    @responses.activate
    def test_calculate_route_success(self):
        """Testa cálculo de rota bem-sucedido."""
        # Mock da resposta do OSRM
        osrm_response = {
            'code': 'Ok',
            'routes': [
                {
                    'distance': 430000,
                    'duration': 18000,
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [
                            [-46.6333, -23.5505],
                            [-43.1729, -22.9068]
                        ]
                    }
                }
            ]
        }
        
        responses.add(
            responses.GET,
            'http://router.project-osrm.org/route/v1/driving/-46.6333,-23.5505;-43.1729,-22.9068',
            json=osrm_response,
            status=200
        )
        
        origin = (-23.5505, -46.6333)
        destination = (-22.9068, -43.1729)
        
        result = calculate_route_osm(origin, destination)
        
        assert result is not None
        assert result['distance'] == 430000
        assert result['duration'] == 18000
        assert result['geometry']['type'] == 'LineString'
    
    @responses.activate
    def test_calculate_route_with_profile(self):
        """Testa cálculo de rota com perfil específico."""
        osrm_response = {
            'code': 'Ok',
            'routes': [
                {
                    'distance': 100000,
                    'duration': 7200,
                    'geometry': {'type': 'LineString', 'coordinates': []}
                }
            ]
        }
        
        responses.add(
            responses.GET,
            'http://router.project-osrm.org/route/v1/walking/-46.6333,-23.5505;-43.1729,-22.9068',
            json=osrm_response,
            status=200
        )
        
        origin = (-23.5505, -46.6333)
        destination = (-22.9068, -43.1729)
        
        result = calculate_route_osm(origin, destination, profile='walking')
        
        assert result is not None
        assert result['distance'] == 100000
    
    @responses.activate
    def test_calculate_route_osrm_error(self):
        """Testa erro retornado pelo OSRM."""
        osrm_response = {
            'code': 'NoRoute',
            'message': 'Nenhuma rota encontrada'
        }
        
        responses.add(
            responses.GET,
            'http://router.project-osrm.org/route/v1/driving/-46.6333,-23.5505;-43.1729,-22.9068',
            json=osrm_response,
            status=200
        )
        
        origin = (-23.5505, -46.6333)
        destination = (-22.9068, -43.1729)
        
        with pytest.raises(OSMServiceError) as exc_info:
            calculate_route_osm(origin, destination)
        
        assert 'Erro ao calcular rota' in str(exc_info.value)
    
    @responses.activate
    def test_calculate_route_no_routes(self):
        """Testa quando nenhuma rota é encontrada."""
        osrm_response = {
            'code': 'Ok',
            'routes': []
        }
        
        responses.add(
            responses.GET,
            'http://router.project-osrm.org/route/v1/driving/-46.6333,-23.5505;-43.1729,-22.9068',
            json=osrm_response,
            status=200
        )
        
        origin = (-23.5505, -46.6333)
        destination = (-22.9068, -43.1729)
        
        with pytest.raises(OSMServiceError) as exc_info:
            calculate_route_osm(origin, destination)
        
        assert 'Nenhuma rota encontrada' in str(exc_info.value)
    
    @patch('apps.routes.osm_service.requests.get')
    def test_calculate_route_timeout(self, mock_get):
        """Testa timeout na requisição."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout('Timeout')
        
        origin = (-23.5505, -46.6333)
        destination = (-22.9068, -43.1729)
        
        with pytest.raises(OSMServiceError) as exc_info:
            calculate_route_osm(origin, destination)
        
        assert 'Timeout' in str(exc_info.value)
    
    @responses.activate
    def test_calculate_route_http_error(self):
        """Testa erro HTTP na requisição."""
        responses.add(
            responses.GET,
            'http://router.project-osrm.org/route/v1/driving/-46.6333,-23.5505;-43.1729,-22.9068',
            status=500
        )
        
        origin = (-23.5505, -46.6333)
        destination = (-22.9068, -43.1729)
        
        with pytest.raises(OSMServiceError) as exc_info:
            calculate_route_osm(origin, destination)
        
        assert 'Erro ao conectar' in str(exc_info.value)


@pytest.mark.django_db
class TestGeocodeAddress:
    """Testes para geocode_address."""
    
    @responses.activate
    def test_geocode_address_success(self):
        """Testa geocodificação bem-sucedida."""
        nominatim_response = [
            {
                'lat': '-23.5505199',
                'lon': '-46.6333094',
                'display_name': 'Avenida Paulista, São Paulo, SP',
                'address': {}
            }
        ]
        
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/search',
            json=nominatim_response,
            status=200
        )
        
        result = geocode_address('Av. Paulista, 1000, São Paulo, SP')
        
        assert result is not None
        assert result[0] == pytest.approx(-23.5505199, abs=0.0001)
        assert result[1] == pytest.approx(-46.6333094, abs=0.0001)
    
    @responses.activate
    def test_geocode_address_not_found(self):
        """Testa quando endereço não é encontrado."""
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/search',
            json=[],
            status=200
        )
        
        result = geocode_address('Endereço Inexistente 99999')
        
        assert result is None
    
    @patch('apps.routes.osm_service.requests.get')
    def test_geocode_address_timeout(self, mock_get):
        """Testa timeout na geocodificação."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout('Timeout')
        
        with pytest.raises(OSMServiceError) as exc_info:
            geocode_address('Av. Paulista, 1000')
        
        assert 'Timeout' in str(exc_info.value)
    
    @responses.activate
    def test_geocode_address_http_error(self):
        """Testa erro HTTP na geocodificação."""
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/search',
            status=503
        )
        
        with pytest.raises(OSMServiceError) as exc_info:
            geocode_address('Av. Paulista, 1000')
        
        assert 'Erro ao geocodificar' in str(exc_info.value)
    
    @responses.activate
    def test_geocode_address_invalid_response(self):
        """Testa resposta inválida do Nominatim."""
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/search',
            json=[{'invalid': 'data'}],
            status=200
        )
        
        with pytest.raises(OSMServiceError) as exc_info:
            geocode_address('Av. Paulista, 1000')
        
        assert 'Resposta inválida' in str(exc_info.value)


@pytest.mark.django_db
class TestReverseGeocode:
    """Testes para reverse_geocode."""
    
    @responses.activate
    def test_reverse_geocode_success(self):
        """Testa reverse geocoding bem-sucedido."""
        nominatim_response = {
            'display_name': 'Avenida Paulista, 1000, São Paulo, SP, Brasil',
            'address': {
                'road': 'Avenida Paulista',
                'city': 'São Paulo',
                'state': 'SP'
            }
        }
        
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/reverse',
            json=nominatim_response,
            status=200
        )
        
        result = reverse_geocode(-23.5505, -46.6333)
        
        assert result is not None
        assert 'Avenida Paulista' in result
        assert 'São Paulo' in result
    
    @responses.activate
    def test_reverse_geocode_not_found(self):
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
        
        result = reverse_geocode(0.0, 0.0)
        
        assert result is None
    
    @patch('apps.routes.osm_service.requests.get')
    def test_reverse_geocode_timeout(self, mock_get):
        """Testa timeout no reverse geocoding."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout('Timeout')
        
        with pytest.raises(OSMServiceError) as exc_info:
            reverse_geocode(-23.5505, -46.6333)
        
        assert 'Timeout' in str(exc_info.value)
    
    @responses.activate
    def test_reverse_geocode_http_error(self):
        """Testa erro HTTP no reverse geocoding."""
        responses.add(
            responses.GET,
            'https://nominatim.openstreetmap.org/reverse',
            status=500
        )
        
        with pytest.raises(OSMServiceError) as exc_info:
            reverse_geocode(-23.5505, -46.6333)
        
        assert 'Erro ao buscar' in str(exc_info.value)


@pytest.mark.django_db
class TestCalculateDistanceHaversine:
    """Testes para calculate_distance_haversine."""
    
    def test_calculate_distance_same_point(self):
        """Testa distância entre o mesmo ponto."""
        coord = (-23.5505, -46.6333)
        
        distance = calculate_distance_haversine(coord, coord)
        
        assert distance == pytest.approx(0, abs=1)
    
    def test_calculate_distance_sp_rj(self):
        """Testa distância entre São Paulo e Rio de Janeiro."""
        sp = (-23.5505, -46.6333)
        rj = (-22.9068, -43.1729)
        
        distance = calculate_distance_haversine(sp, rj)
        
        # Distância aproximada: ~357 km (em linha reta)
        assert distance == pytest.approx(357000, rel=0.1)
    
    def test_calculate_distance_short(self):
        """Testa distância curta (poucos km)."""
        coord1 = (-23.5505, -46.6333)
        coord2 = (-23.5605, -46.6433)  # ~1.5 km
        
        distance = calculate_distance_haversine(coord1, coord2)
        
        assert distance > 1000
        assert distance < 2000
    
    def test_calculate_distance_long(self):
        """Testa distância longa."""
        sp = (-23.5505, -46.6333)
        ny = (40.7128, -74.0060)  # Nova York
        
        distance = calculate_distance_haversine(sp, ny)
        
        # Distância aproximada: ~7700 km
        assert distance > 7000000
        assert distance < 8000000
