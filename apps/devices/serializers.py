"""
Serializers para a aplicação de dispositivos.
"""
from rest_framework import serializers
from .models import Device
from apps.vehicles.models import Vehicle


class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Device.
    """
    vehicle_placa = serializers.CharField(source='vehicle.placa', read_only=True)
    vehicle_modelo = serializers.CharField(source='vehicle.modelo', read_only=True)
    transportadora_nome = serializers.CharField(
        source='vehicle.transportadora.company_name',
        read_only=True
    )
    is_updated_recently = serializers.BooleanField(read_only=True)
    minutes_since_last_update = serializers.FloatField(read_only=True)
    odometer_km = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id',
            'vehicle',
            'vehicle_placa',
            'vehicle_modelo',
            'transportadora_nome',
            'suntech_device_id',
            'suntech_vehicle_id',
            'imei',
            'label',
            'last_position_date',
            'last_system_date',
            'last_latitude',
            'last_longitude',
            'last_address',
            'last_speed',
            'last_ignition_status',
            'odometer',
            'odometer_km',
            'is_active',
            'is_updated_recently',
            'minutes_since_last_update',
            'observacoes',
            'created_at',
            'updated_at',
            'last_sync_at'
        ]
        read_only_fields = [
            'id',
            'last_position_date',
            'last_system_date',
            'last_latitude',
            'last_longitude',
            'last_address',
            'last_speed',
            'last_ignition_status',
            'odometer',
            'created_at',
            'updated_at',
            'last_sync_at'
        ]


class DeviceListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagem de dispositivos.
    """
    vehicle_placa = serializers.CharField(source='vehicle.placa', read_only=True)
    vehicle_modelo = serializers.CharField(source='vehicle.modelo', read_only=True)
    is_updated_recently = serializers.BooleanField(read_only=True)
    minutes_since_last_update = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id',
            'suntech_device_id',
            'vehicle_placa',
            'vehicle_modelo',
            'label',
            'last_system_date',
            'is_active',
            'is_updated_recently',
            'minutes_since_last_update',
            'last_ignition_status'
        ]


class DeviceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de dispositivos.
    """
    
    class Meta:
        model = Device
        fields = [
            'vehicle',
            'suntech_device_id',
            'suntech_vehicle_id',
            'imei',
            'label',
            'is_active',
            'observacoes'
        ]
    
    def validate_suntech_device_id(self, value):
        """
        Validar se o suntech_device_id já não existe.
        """
        queryset = Device.objects.filter(suntech_device_id=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                'Já existe um dispositivo com este ID Suntech.'
            )
        
        return value
    
    def validate_vehicle(self, value):
        """
        Validar se o veículo já não possui um dispositivo.
        """
        queryset = Device.objects.filter(vehicle=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                'Este veículo já possui um dispositivo vinculado.'
            )
        
        return value
    
    def create(self, validated_data):
        """
        Ao criar, sincronizar dados com a API Suntech.
        """
        device = super().create(validated_data)
        device.sync_with_suntech()
        return device


class DeviceSyncSerializer(serializers.Serializer):
    """
    Serializer para sincronização manual de dispositivo.
    """
    success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)
    device = DeviceSerializer(read_only=True)


class DeviceStatusSerializer(serializers.Serializer):
    """
    Serializer para status de atualização do dispositivo.
    """
    device_id = serializers.IntegerField(read_only=True)
    suntech_device_id = serializers.IntegerField(read_only=True)
    vehicle_placa = serializers.CharField(read_only=True)
    is_updated = serializers.BooleanField(read_only=True)
    minutes_since_update = serializers.FloatField(read_only=True)
    threshold_minutes = serializers.IntegerField(read_only=True)
    last_system_date = serializers.DateTimeField(read_only=True)
