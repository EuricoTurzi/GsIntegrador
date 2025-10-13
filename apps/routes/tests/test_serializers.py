"""
Testes para os serializers do app Routes.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch
from apps.routes.models import Route
from apps.routes.serializers import (
    RouteSerializer,
    RouteListSerializer,
    RouteCreateUpdateSerializer,
    GeocodeSerializer,
    ReverseGeocodeSerializer
)
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
class TestRouteSerializer:
    """Testes para RouteSerializer."""
    
    def test_route_serializer_fields(self, route):
        """Testa que o serializer contém todos os campos esperados."""
        serializer = RouteSerializer(route)
        data = serializer.data
        
        expected_fields = [
            'id', 'transportadora', 'transportadora_nome', 'name', 'description',
            'origin_name', 'origin_address', 'origin_latitude', 'origin_longitude',
            'origin_coordinates', 'destination_name', 'destination_address',
            'destination_latitude', 'destination_longitude', 'destination_coordinates',
            'distance_meters', 'distance_km', 'estimated_duration_seconds',
            'estimated_duration_hours', 'estimated_duration_formatted',
            'route_geometry', 'is_active', 'observacoes', 'created_at',
            'updated_at', 'last_calculated_at'
        ]
        
        for field in expected_fields:
            assert field in data
    
    def test_route_serializer_computed_fields(self, route):
        """Testa campos computados do serializer."""
        serializer = RouteSerializer(route)
        data = serializer.data
        
        assert data['distance_km'] == 430.0
        assert data['estimated_duration_hours'] == 5.0
        assert data['estimated_duration_formatted'] == '05:00'
        assert data['origin_coordinates'] == [-23.5505, -46.6333]
        assert data['destination_coordinates'] == [-22.9068, -43.1729]
    
    def test_route_serializer_transportadora_nome(self, route):
        """Testa campo transportadora_nome."""
        serializer = RouteSerializer(route)
        data = serializer.data
        
        assert data['transportadora_nome'] == 'Transportadora 1'
    
    def test_route_serializer_read_only_fields(self, route):
        """Testa que campos read-only não são atualizáveis."""
        serializer = RouteSerializer(route, data={
            'distance_meters': 999999,
            'estimated_duration_seconds': 999999,
            'name': 'Updated Name'
        }, partial=True)
        
        assert serializer.is_valid()
        serializer.save()
        
        route.refresh_from_db()
        assert route.name == 'Updated Name'
        # Campos read-only não devem ter mudado
        assert route.distance_meters == 430000
        assert route.estimated_duration_seconds == 18000


@pytest.mark.django_db
class TestRouteListSerializer:
    """Testes para RouteListSerializer."""
    
    def test_route_list_serializer_fields(self, route):
        """Testa campos do serializer de listagem."""
        serializer = RouteListSerializer(route)
        data = serializer.data
        
        expected_fields = [
            'id', 'name', 'origin_name', 'destination_name',
            'distance_km', 'estimated_duration_formatted',
            'transportadora_nome', 'is_active'
        ]
        
        for field in expected_fields:
            assert field in data
    
    def test_route_list_serializer_multiple_routes(self, transportadora):
        """Testa serialização de múltiplas rotas."""
        route1 = Route.objects.create(
            transportadora=transportadora,
            name='Route 1',
            origin_name='A',
            origin_address='Address A',
            origin_latitude=Decimal('-23.5505000'),
            origin_longitude=Decimal('-46.6333000'),
            destination_name='B',
            destination_address='Address B',
            destination_latitude=Decimal('-22.9068000'),
            destination_longitude=Decimal('-43.1729000')
        )
        
        route2 = Route.objects.create(
            transportadora=transportadora,
            name='Route 2',
            origin_name='C',
            origin_address='Address C',
            origin_latitude=Decimal('-22.9056700'),
            origin_longitude=Decimal('-47.0608300'),
            destination_name='D',
            destination_address='Address D',
            destination_latitude=Decimal('-23.9608700'),
            destination_longitude=Decimal('-46.3335300')
        )
        
        routes = [route1, route2]
        serializer = RouteListSerializer(routes, many=True)
        
        assert len(serializer.data) == 2


@pytest.mark.django_db
class TestRouteCreateUpdateSerializer:
    """Testes para RouteCreateUpdateSerializer."""
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_create_route(self, mock_calculate, transportadora):
        """Testa criação de rota via serializer."""
        mock_calculate.return_value = {
            'distance': 100000,
            'duration': 3600,
            'geometry': {'type': 'LineString', 'coordinates': []}
        }
        
        data = {
            'transportadora': transportadora.id,
            'name': 'Nova Rota',
            'origin_name': 'Origem',
            'origin_address': 'Endereço Origem',
            'origin_latitude': '-23.5505000',
            'origin_longitude': '-46.6333000',
            'destination_name': 'Destino',
            'destination_address': 'Endereço Destino',
            'destination_latitude': '-22.9068000',
            'destination_longitude': '-43.1729000'
        }
        
        serializer = RouteCreateUpdateSerializer(data=data)
        assert serializer.is_valid()
        
        route = serializer.save()
        
        assert route.name == 'Nova Rota'
        assert route.distance_meters == 100000
        mock_calculate.assert_called_once()
    
    @patch('apps.routes.osm_service.calculate_route_osm')
    def test_update_route(self, mock_calculate, route):
        """Testa atualização de rota via serializer."""
        mock_calculate.return_value = {
            'distance': 450000,
            'duration': 20000,
            'geometry': {'type': 'LineString', 'coordinates': []}
        }
        
        data = {
            'name': 'Rota Atualizada',
            'destination_latitude': '-22.9100000'
        }
        
        serializer = RouteCreateUpdateSerializer(route, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_route = serializer.save()
        
        assert updated_route.name == 'Rota Atualizada'
        # Deve recalcular pois coordenada mudou
        mock_calculate.assert_called_once()
    
    def test_validate_same_origin_destination(self, transportadora):
        """Testa validação de origem e destino iguais."""
        data = {
            'transportadora': transportadora.id,
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
        
        serializer = RouteCreateUpdateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'diferentes' in str(serializer.errors).lower()


@pytest.mark.django_db
class TestGeocodeSerializer:
    """Testes para GeocodeSerializer."""
    
    def test_geocode_serializer_valid(self):
        """Testa validação com endereço válido."""
        data = {
            'address': 'Av. Paulista, 1000, São Paulo, SP'
        }
        
        serializer = GeocodeSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['address'] == 'Av. Paulista, 1000, São Paulo, SP'
    
    def test_geocode_serializer_empty_address(self):
        """Testa validação com endereço vazio."""
        data = {
            'address': '   '
        }
        
        serializer = GeocodeSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'address' in serializer.errors
    
    def test_geocode_serializer_missing_address(self):
        """Testa validação sem endereço."""
        data = {}
        
        serializer = GeocodeSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'address' in serializer.errors
    
    def test_geocode_serializer_strips_whitespace(self):
        """Testa que espaços são removidos."""
        data = {
            'address': '  Av. Paulista, 1000  '
        }
        
        serializer = GeocodeSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['address'] == 'Av. Paulista, 1000'


@pytest.mark.django_db
class TestReverseGeocodeSerializer:
    """Testes para ReverseGeocodeSerializer."""
    
    def test_reverse_geocode_serializer_valid(self):
        """Testa validação com coordenadas válidas."""
        data = {
            'latitude': -23.5505,
            'longitude': -46.6333
        }
        
        serializer = ReverseGeocodeSerializer(data=data)
        
        assert serializer.is_valid()
    
    def test_reverse_geocode_serializer_invalid_latitude_max(self):
        """Testa validação com latitude inválida (> 90)."""
        data = {
            'latitude': 91.0,
            'longitude': -46.6333
        }
        
        serializer = ReverseGeocodeSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'latitude' in serializer.errors
    
    def test_reverse_geocode_serializer_invalid_latitude_min(self):
        """Testa validação com latitude inválida (< -90)."""
        data = {
            'latitude': -91.0,
            'longitude': -46.6333
        }
        
        serializer = ReverseGeocodeSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'latitude' in serializer.errors
    
    def test_reverse_geocode_serializer_invalid_longitude_max(self):
        """Testa validação com longitude inválida (> 180)."""
        data = {
            'latitude': -23.5505,
            'longitude': 181.0
        }
        
        serializer = ReverseGeocodeSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'longitude' in serializer.errors
    
    def test_reverse_geocode_serializer_invalid_longitude_min(self):
        """Testa validação com longitude inválida (< -180)."""
        data = {
            'latitude': -23.5505,
            'longitude': -181.0
        }
        
        serializer = ReverseGeocodeSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'longitude' in serializer.errors
    
    def test_reverse_geocode_serializer_missing_fields(self):
        """Testa validação sem campos obrigatórios."""
        data = {}
        
        serializer = ReverseGeocodeSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'latitude' in serializer.errors
        assert 'longitude' in serializer.errors
