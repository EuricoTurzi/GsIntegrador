"""
Serializers para a aplicação de veículos.
"""
from rest_framework import serializers
from .models import Vehicle
from apps.authentication.models import User


class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Vehicle.
    """
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    placa_formatada = serializers.CharField(read_only=True)
    esta_disponivel = serializers.BooleanField(read_only=True)
    tem_rastreador = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'transportadora',
            'transportadora_nome',
            'status',
            'placa',
            'placa_formatada',
            'ano',
            'cor',
            'modelo',
            'renavam',
            'chassi',
            'is_active',
            'observacoes',
            'esta_disponivel',
            'tem_rastreador',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagem de veículos.
    """
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    placa_formatada = serializers.CharField(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'placa',
            'placa_formatada',
            'modelo',
            'ano',
            'cor',
            'status',
            'transportadora_nome',
            'is_active'
        ]


class VehicleCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de veículos.
    """
    
    class Meta:
        model = Vehicle
        fields = [
            'transportadora',
            'status',
            'placa',
            'ano',
            'cor',
            'modelo',
            'renavam',
            'chassi',
            'is_active',
            'observacoes'
        ]
        read_only_fields = ['transportadora']
    
    def validate_placa(self, value):
        """
        Validar se a placa já não existe.
        """
        # Normalizar placa
        value = value.upper().replace('-', '')
        
        # Verificar se já existe (exceto o próprio veículo em caso de update)
        queryset = Vehicle.objects.filter(placa=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError('Já existe um veículo com esta placa.')
        
        return value
    
    def validate_renavam(self, value):
        """
        Validar se o renavam já não existe.
        """
        queryset = Vehicle.objects.filter(renavam=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError('Já existe um veículo com este Renavam.')
        
        return value
    
    def validate_chassi(self, value):
        """
        Validar se o chassi já não existe.
        """
        # Normalizar chassi
        value = value.upper()
        
        queryset = Vehicle.objects.filter(chassi=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError('Já existe um veículo com este Chassi.')
        
        return value
    
    def validate_ano(self, value):
        """
        Validar ano do veículo.
        """
        from datetime import datetime
        current_year = datetime.now().year
        
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(
                f'Ano deve estar entre 1900 e {current_year + 1}.'
            )
        
        return value
    
    def validate_transportadora(self, value):
        """
        Validar se o usuário é uma transportadora.
        """
        if value.user_type != 'TRANSPORTADORA':
            raise serializers.ValidationError(
                'Apenas usuários do tipo Transportadora podem ser vinculados a veículos.'
            )
        
        return value
