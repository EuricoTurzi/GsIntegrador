from rest_framework import serializers
from .models import Driver


class DriverSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Driver"""
    
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    
    nome_curto = serializers.CharField(read_only=True)
    
    class Meta:
        model = Driver
        fields = (
            'id', 'transportadora', 'transportadora_nome',
            'nome', 'nome_curto', 'cpf', 'rg', 'cnh',
            'nome_do_pai', 'nome_da_mae', 'tipo_de_veiculo',
            'data_nascimento', 'telefone', 'email', 'endereco',
            'is_active', 'observacoes',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'transportadora')
    
    def validate_cpf(self, value):
        """Validar formato do CPF"""
        import re
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', value):
            raise serializers.ValidationError(
                'CPF deve estar no formato: 000.000.000-00'
            )
        return value
    
    def validate_rg(self, value):
        """Validar formato do RG"""
        import re
        if not re.match(r'^\d{2}\.\d{3}\.\d{3}-\d{1}$', value):
            raise serializers.ValidationError(
                'RG deve estar no formato: 00.000.000-0'
            )
        return value
    
    def validate_cnh(self, value):
        """Validar formato da CNH"""
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError(
                'CNH deve conter exatamente 11 dígitos'
            )
        return value
    
    def create(self, validated_data):
        """
        Criar motorista associado à transportadora autenticada
        """
        # A transportadora será definida na view
        return super().create(validated_data)


class DriverListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de motoristas"""
    
    transportadora_nome = serializers.CharField(
        source='transportadora.company_name',
        read_only=True
    )
    
    nome_curto = serializers.CharField(read_only=True)
    
    class Meta:
        model = Driver
        fields = (
            'id', 'nome', 'nome_curto', 'cpf', 'cnh',
            'tipo_de_veiculo', 'transportadora_nome',
            'is_active', 'created_at'
        )
        read_only_fields = fields


class DriverCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de motoristas"""
    
    class Meta:
        model = Driver
        fields = (
            'nome', 'cpf', 'rg', 'cnh',
            'nome_do_pai', 'nome_da_mae', 'tipo_de_veiculo',
            'data_nascimento', 'telefone', 'email', 'endereco',
            'is_active', 'observacoes'
        )
    
    def validate(self, attrs):
        """Validações gerais"""
        # Verificar se CPF já existe
        cpf = attrs.get('cpf')
        if cpf:
            instance_id = self.instance.id if self.instance else None
            if Driver.objects.filter(cpf=cpf).exclude(id=instance_id).exists():
                raise serializers.ValidationError({
                    'cpf': 'Já existe um motorista cadastrado com este CPF.'
                })
        
        # Verificar se CNH já existe
        cnh = attrs.get('cnh')
        if cnh:
            instance_id = self.instance.id if self.instance else None
            if Driver.objects.filter(cnh=cnh).exclude(id=instance_id).exists():
                raise serializers.ValidationError({
                    'cnh': 'Já existe um motorista cadastrado com esta CNH.'
                })
        
        return attrs
