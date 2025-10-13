"""
Testes para o modelo Route.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch
from apps.routes.models import Route
from apps.authentication.models import User


@pytest.fixture
def transportadora():
    """Cria um usuário transportadora para testes."""
    return User.objects.create_user(
        username='transportadora1',
        email='transportadora1@example.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 1'
    )


@pytest.fixture
def route(transportadora):
    """Cria uma rota para testes."""
    return Route.objects.create(
        transportadora=transportadora,
        name='São Paulo - Rio de Janeiro',
        description='Rota principal entre SP e RJ',
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


@pytest.mark.django_db
class TestRouteModel:
    """Testes para o modelo Route."""
    
    def test_create_route(self, transportadora):
        """Testa a criação de uma rota."""
        route = Route.objects.create(
            transportadora=transportadora,
            name='Campinas - Santos',
            origin_name='Campinas',
            origin_address='Centro, Campinas, SP',
            origin_latitude=Decimal('-22.9056700'),
            origin_longitude=Decimal('-47.0608300'),
            destination_name='Santos',
            destination_address='Centro, Santos, SP',
            destination_latitude=Decimal('-23.9608700'),
            destination_longitude=Decimal('-46.3335300')
        )
        
        assert route.id is not None
        assert route.name == 'Campinas - Santos'
        assert route.transportadora == transportadora
        assert route.is_active is True
    
    def test_route_str(self, route):
        """Testa a representação em string da rota."""
        expected = 'São Paulo - Rio de Janeiro (São Paulo → Rio de Janeiro)'
        assert str(route) == expected
    
    def test_distance_km_property(self, route):
        """Testa a propriedade distance_km."""
        assert route.distance_km == 430.0
    
    def test_distance_km_none(self, transportadora):
        """Testa distance_km quando não há distância calculada."""
        route = Route.objects.create(
            transportadora=transportadora,
            name='Test Route',
            origin_name='A',
            origin_address='Address A',
            origin_latitude=Decimal('-23.5505000'),
            origin_longitude=Decimal('-46.6333000'),
            destination_name='B',
            destination_address='Address B',
            destination_latitude=Decimal('-22.9068000'),
            destination_longitude=Decimal('-43.1729000')
        )
        
        assert route.distance_km is None
    
    def test_estimated_duration_hours_property(self, route):
        """Testa a propriedade estimated_duration_hours."""
        assert route.estimated_duration_hours == 5.0
    
    def test_estimated_duration_formatted_property(self, route):
        """Testa a propriedade estimated_duration_formatted."""
        assert route.estimated_duration_formatted == '05:00'
    
    def test_estimated_duration_formatted_with_minutes(self, route):
        """Testa a duração formatada com horas e minutos."""
        route.estimated_duration_seconds = 19800  # 5h30min
        route.save()
        
        assert route.estimated_duration_formatted == '05:30'
    
    def test_origin_coordinates_property(self, route):
        """Testa a propriedade origin_coordinates."""
        coords = route.origin_coordinates
        assert coords == (-23.5505, -46.6333)
    
    def test_destination_coordinates_property(self, route):
        """Testa a propriedade destination_coordinates."""
        coords = route.destination_coordinates
        assert coords == (-22.9068, -43.1729)
    
    def test_latitude_validation_min(self, transportadora):
        """Testa validação de latitude mínima."""
        with pytest.raises(ValidationError) as exc_info:
            route = Route(
                transportadora=transportadora,
                name='Invalid Route',
                origin_name='A',
                origin_address='Address A',
                origin_latitude=Decimal('-91.0000000'),  # Inválido
                origin_longitude=Decimal('-46.6333000'),
                destination_name='B',
                destination_address='Address B',
                destination_latitude=Decimal('-22.9068000'),
                destination_longitude=Decimal('-43.1729000')
            )
            route.save()
        
        assert 'origin_latitude' in str(exc_info.value)
    
    def test_latitude_validation_max(self, transportadora):
        """Testa validação de latitude máxima."""
        with pytest.raises(ValidationError) as exc_info:
            route = Route(
                transportadora=transportadora,
                name='Invalid Route',
                origin_name='A',
                origin_address='Address A',
                origin_latitude=Decimal('91.0000000'),  # Inválido
                origin_longitude=Decimal('-46.6333000'),
                destination_name='B',
                destination_address='Address B',
                destination_latitude=Decimal('-22.9068000'),
                destination_longitude=Decimal('-43.1729000')
            )
            route.save()
        
        assert 'origin_latitude' in str(exc_info.value)
    
    def test_longitude_validation_min(self, transportadora):
        """Testa validação de longitude mínima."""
        with pytest.raises(ValidationError) as exc_info:
            route = Route(
                transportadora=transportadora,
                name='Invalid Route',
                origin_name='A',
                origin_address='Address A',
                origin_latitude=Decimal('-23.5505000'),
                origin_longitude=Decimal('-181.0000000'),  # Inválido
                destination_name='B',
                destination_address='Address B',
                destination_latitude=Decimal('-22.9068000'),
                destination_longitude=Decimal('-43.1729000')
            )
            route.save()
        
        assert 'origin_longitude' in str(exc_info.value)
    
    def test_longitude_validation_max(self, transportadora):
        """Testa validação de longitude máxima."""
        with pytest.raises(ValidationError) as exc_info:
            route = Route(
                transportadora=transportadora,
                name='Invalid Route',
                origin_name='A',
                origin_address='Address A',
                origin_latitude=Decimal('-23.5505000'),
                origin_longitude=Decimal('181.0000000'),  # Inválido
                destination_name='B',
                destination_address='Address B',
                destination_latitude=Decimal('-22.9068000'),
                destination_longitude=Decimal('-43.1729000')
            )
            route.save()
        
        assert 'origin_longitude' in str(exc_info.value)
    
    def test_origin_destination_same_validation(self, transportadora):
        """Testa validação de origem e destino iguais."""
        with pytest.raises(ValidationError) as exc_info:
            route = Route(
                transportadora=transportadora,
                name='Invalid Route',
                origin_name='A',
                origin_address='Address A',
                origin_latitude=Decimal('-23.5505000'),
                origin_longitude=Decimal('-46.6333000'),
                destination_name='B',
                destination_address='Address B',
                destination_latitude=Decimal('-23.5505000'),  # Mesma latitude
                destination_longitude=Decimal('-46.6333000')  # Mesma longitude
            )
            route.save()
        
        assert 'Origem e destino devem ser diferentes' in str(exc_info.value)
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_calculate_route_success(self, mock_calculate, route):
        """Testa o cálculo bem-sucedido da rota."""
        mock_calculate.return_value = {
            'distance': 450000,
            'duration': 20000,
            'geometry': {
                'type': 'LineString',
                'coordinates': [[-46.6333, -23.5505], [-43.1729, -22.9068]]
            }
        }
        
        result = route.calculate_route()
        
        assert result is True
        assert route.distance_meters == 450000
        assert route.estimated_duration_seconds == 20000
        assert route.route_geometry is not None
        assert route.last_calculated_at is not None
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_calculate_route_failure(self, mock_calculate, route):
        """Testa falha no cálculo da rota."""
        mock_calculate.side_effect = Exception('OSRM error')
        
        result = route.calculate_route()
        
        assert result is False
        # Valores não devem ter mudado
        assert route.distance_meters == 430000
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_calculate_route_no_result(self, mock_calculate, route):
        """Testa quando o cálculo não retorna resultado."""
        mock_calculate.return_value = None
        
        result = route.calculate_route()
        
        assert result is False
    
    def test_route_activation(self, route):
        """Testa ativação/desativação de rotas."""
        assert route.is_active is True
        
        route.is_active = False
        route.save()
        
        route.refresh_from_db()
        assert route.is_active is False
    
    def test_route_observacoes(self, route):
        """Testa o campo de observações."""
        route.observacoes = 'Rota com pedágios'
        route.save()
        
        route.refresh_from_db()
        assert route.observacoes == 'Rota com pedágios'
    
    def test_route_timestamps(self, route):
        """Testa os campos de timestamp."""
        assert route.created_at is not None
        assert route.updated_at is not None
        assert route.last_calculated_at is None
    
    def test_route_geometry_json(self, route):
        """Testa armazenamento de geometria JSON."""
        geometry = {
            'type': 'LineString',
            'coordinates': [[-46.6333, -23.5505], [-43.1729, -22.9068]]
        }
        
        route.route_geometry = geometry
        route.save()
        
        route.refresh_from_db()
        assert route.route_geometry['type'] == 'LineString'
        assert len(route.route_geometry['coordinates']) == 2
