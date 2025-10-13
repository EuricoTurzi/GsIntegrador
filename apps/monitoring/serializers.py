"""
Serializers para a aplicação de monitoramento.
"""
from rest_framework import serializers
from .models import MonitoringSystem, VehiclePositionHistory
from apps.drivers.serializers import DriverSerializer
from apps.vehicles.serializers import VehicleSerializer
from apps.routes.serializers import RouteSerializer


class MonitoringSystemSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo MonitoringSystem.
    """
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    driver_nome = serializers.CharField(source='driver.nome', read_only=True)
    vehicle_placa = serializers.CharField(source='vehicle.placa', read_only=True)
    route_name = serializers.CharField(source='route.name', read_only=True)
    
    duration_days = serializers.IntegerField(read_only=True)
    is_in_progress = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    device_status = serializers.BooleanField(read_only=True)
    current_vehicle_position = serializers.SerializerMethodField()
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MonitoringSystem
        fields = [
            'id',
            'identifier',
            'transportadora',
            'transportadora_nome',
            'route',
            'route_name',
            'driver',
            'driver_nome',
            'vehicle',
            'vehicle_placa',
            'name',
            'description',
            'status',
            'status_display',
            'planned_start_date',
            'planned_end_date',
            'actual_start_date',
            'actual_end_date',
            'duration_days',
            'device_validated_at',
            'device_was_updated',
            'device_status',
            'current_vehicle_position',
            'cargo_description',
            'cargo_value',
            'observations',
            'is_active',
            'is_in_progress',
            'is_completed',
            'created_at',
            'updated_at',
            'created_by'
        ]
        read_only_fields = [
            'id',
            'identifier',
            'device_validated_at',
            'device_was_updated',
            'actual_start_date',
            'actual_end_date',
            'created_at',
            'updated_at',
            'created_by'
        ]
    
    def get_current_vehicle_position(self, obj):
        """Retorna a posição atual do veículo."""
        return obj.current_vehicle_position


class MonitoringSystemListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagem de SMs.
    """
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    driver_nome = serializers.CharField(source='driver.nome', read_only=True)
    vehicle_placa = serializers.CharField(source='vehicle.placa', read_only=True)
    route_name = serializers.CharField(source='route.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    device_status = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MonitoringSystem
        fields = [
            'id',
            'identifier',
            'name',
            'status',
            'status_display',
            'driver_nome',
            'vehicle_placa',
            'route_name',
            'transportadora_nome',
            'planned_start_date',
            'device_status',
            'is_active'
        ]


class MonitoringSystemCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de SMs.
    """
    
    class Meta:
        model = MonitoringSystem
        fields = [
            'transportadora',
            'route',
            'driver',
            'vehicle',
            'name',
            'description',
            'planned_start_date',
            'planned_end_date',
            'cargo_description',
            'cargo_value',
            'observations',
            'is_active'
        ]
    
    def validate(self, data):
        """
        Validações customizadas.
        """
        # Validar datas
        if data.get('planned_start_date') and data.get('planned_end_date'):
            if data['planned_end_date'] <= data['planned_start_date']:
                raise serializers.ValidationError({
                    'planned_end_date': 'Data de término deve ser posterior à data de início.'
                })
        
        # Validar que todos pertencem à mesma transportadora
        transportadora = data.get('transportadora')
        route = data.get('route')
        driver = data.get('driver')
        vehicle = data.get('vehicle')
        
        if route and route.transportadora != transportadora:
            raise serializers.ValidationError({
                'route': 'A rota deve pertencer à mesma transportadora.'
            })
        
        if driver and driver.transportadora != transportadora:
            raise serializers.ValidationError({
                'driver': 'O motorista deve pertencer à mesma transportadora.'
            })
        
        if vehicle and vehicle.transportadora != transportadora:
            raise serializers.ValidationError({
                'vehicle': 'O veículo deve pertencer à mesma transportadora.'
            })
        
        return data


class MonitoringSystemDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detalhado com objetos completos aninhados.
    """
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    driver = DriverSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    route = RouteSerializer(read_only=True)
    
    duration_days = serializers.IntegerField(read_only=True)
    device_status = serializers.BooleanField(read_only=True)
    current_vehicle_position = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MonitoringSystem
        fields = [
            'id',
            'identifier',
            'transportadora',
            'transportadora_nome',
            'route',
            'driver',
            'vehicle',
            'name',
            'description',
            'status',
            'status_display',
            'planned_start_date',
            'planned_end_date',
            'actual_start_date',
            'actual_end_date',
            'duration_days',
            'device_validated_at',
            'device_was_updated',
            'device_status',
            'current_vehicle_position',
            'cargo_description',
            'cargo_value',
            'observations',
            'is_active',
            'created_at',
            'updated_at',
            'created_by'
        ]
    
    def get_current_vehicle_position(self, obj):
        """Retorna a posição atual do veículo."""
        return obj.current_vehicle_position


class VehiclePositionHistorySerializer(serializers.ModelSerializer):
    """
    Serializer para histórico de posições.
    """
    position_tuple = serializers.SerializerMethodField()
    
    class Meta:
        model = VehiclePositionHistory
        fields = [
            'id',
            'monitoring_system',
            'latitude',
            'longitude',
            'address',
            'speed',
            'heading',
            'altitude',
            'device_timestamp',
            'server_timestamp',
            'extra_data',
            'position_tuple',
        ]
        read_only_fields = ['id', 'monitoring_system', 'server_timestamp']
    
    def get_position_tuple(self, obj):
        """Retorna (lat, lng) para facilitar uso em mapas."""
        return obj.position_tuple


class MonitoringSystemActionSerializer(serializers.Serializer):
    """
    Serializer para ações em SMs (iniciar, finalizar, cancelar).
    """
    success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)
    monitoring_system = MonitoringSystemSerializer(read_only=True)
    reason = serializers.CharField(required=False, write_only=True)
