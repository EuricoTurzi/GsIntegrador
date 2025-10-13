"""
Serializers para a aplicação de rotas.
"""
from rest_framework import serializers
from .models import Route
from .osm_service import geocode_address


class RouteSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Route.
    """
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    distance_km = serializers.FloatField(read_only=True)
    estimated_duration_hours = serializers.FloatField(read_only=True)
    estimated_duration_formatted = serializers.CharField(read_only=True)
    origin_coordinates = serializers.SerializerMethodField()
    destination_coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id',
            'transportadora',
            'transportadora_nome',
            'name',
            'description',
            'origin_name',
            'origin_address',
            'origin_latitude',
            'origin_longitude',
            'origin_coordinates',
            'destination_name',
            'destination_address',
            'destination_latitude',
            'destination_longitude',
            'destination_coordinates',
            'distance_meters',
            'distance_km',
            'estimated_duration_seconds',
            'estimated_duration_hours',
            'estimated_duration_formatted',
            'route_geometry',
            'is_active',
            'observacoes',
            'created_at',
            'updated_at',
            'last_calculated_at'
        ]
        read_only_fields = [
            'id',
            'distance_meters',
            'estimated_duration_seconds',
            'route_geometry',
            'created_at',
            'updated_at',
            'last_calculated_at'
        ]
    
    def get_origin_coordinates(self, obj):
        """Retorna coordenadas de origem como [lat, lon]."""
        return list(obj.origin_coordinates)
    
    def get_destination_coordinates(self, obj):
        """Retorna coordenadas de destino como [lat, lon]."""
        return list(obj.destination_coordinates)


class RouteListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagem de rotas.
    """
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    distance_km = serializers.FloatField(read_only=True)
    estimated_duration_formatted = serializers.CharField(read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id',
            'name',
            'origin_name',
            'destination_name',
            'distance_km',
            'estimated_duration_formatted',
            'transportadora_nome',
            'is_active'
        ]


class RouteCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de rotas.
    """
    
    class Meta:
        model = Route
        fields = [
            'transportadora',
            'name',
            'description',
            'origin_name',
            'origin_address',
            'origin_latitude',
            'origin_longitude',
            'destination_name',
            'destination_address',
            'destination_latitude',
            'destination_longitude',
            'is_active',
            'observacoes'
        ]
    
    def validate(self, data):
        """
        Validar que origem e destino são diferentes.
        """
        origin_lat = data.get('origin_latitude')
        origin_lon = data.get('origin_longitude')
        dest_lat = data.get('destination_latitude')
        dest_lon = data.get('destination_longitude')
        
        if origin_lat == dest_lat and origin_lon == dest_lon:
            raise serializers.ValidationError(
                'Origem e destino devem ser diferentes.'
            )
        
        return data
    
    def create(self, validated_data):
        """
        Ao criar, calcular a rota automaticamente.
        """
        route = super().create(validated_data)
        route.calculate_route()
        return route
    
    def update(self, instance, validated_data):
        """
        Ao atualizar, se coordenadas mudaram, recalcular rota.
        """
        coords_changed = any(
            field in validated_data for field in [
                'origin_latitude', 'origin_longitude',
                'destination_latitude', 'destination_longitude'
            ]
        )
        
        route = super().update(instance, validated_data)
        
        if coords_changed:
            route.calculate_route()
        
        return route


class RouteCalculateSerializer(serializers.Serializer):
    """
    Serializer para calcular rota manualmente.
    """
    success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)
    route = RouteSerializer(read_only=True)


class GeocodeSerializer(serializers.Serializer):
    """
    Serializer para geocodificação de endereços.
    """
    address = serializers.CharField(required=True, help_text='Endereço completo')
    
    def validate_address(self, value):
        """Validar que o endereço não está vazio."""
        if not value.strip():
            raise serializers.ValidationError('Endereço não pode estar vazio.')
        return value.strip()


class GeocodeResultSerializer(serializers.Serializer):
    """
    Serializer para resultado de geocodificação.
    """
    address = serializers.CharField(read_only=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)
    success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)


class ReverseGeocodeSerializer(serializers.Serializer):
    """
    Serializer para reverse geocoding.
    """
    latitude = serializers.FloatField(required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=True, min_value=-180, max_value=180)


class ReverseGeocodeResultSerializer(serializers.Serializer):
    """
    Serializer para resultado de reverse geocoding.
    """
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)
    address = serializers.CharField(read_only=True)
    success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)
