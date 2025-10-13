from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer para o modelo User"""
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'company_name', 'cnpj', 'phone',
            'is_active', 'is_verified', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'is_verified', 'created_at', 'updated_at')


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirmar Senha'
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'user_type',
            'company_name', 'cnpj', 'phone'
        )
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validação customizada"""
        # Verificar se as senhas coincidem
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "As senhas não coincidem."
            })
        
        # Validar campos obrigatórios para Transportadora
        if attrs.get('user_type') == User.UserType.TRANSPORTADORA:
            if not attrs.get('company_name'):
                raise serializers.ValidationError({
                    "company_name": "Nome da empresa é obrigatório para Transportadora."
                })
            if not attrs.get('cnpj'):
                raise serializers.ValidationError({
                    "cnpj": "CNPJ é obrigatório para Transportadora."
                })
        
        return attrs
    
    def create(self, validated_data):
        """Criar novo usuário"""
        # Remover password2 dos dados validados
        validated_data.pop('password2')
        
        # Criar usuário
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', User.UserType.TRANSPORTADORA),
            company_name=validated_data.get('company_name', ''),
            cnpj=validated_data.get('cnpj', ''),
            phone=validated_data.get('phone', ''),
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login de usuários"""
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validar credenciais do usuário"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Credenciais inválidas. Verifique seu usuário e senha.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'Conta desativada. Entre em contato com o administrador.'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Usuário e senha são obrigatórios.'
            )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para alteração de senha"""
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        label='Confirmar Nova Senha'
    )
    
    def validate(self, attrs):
        """Validar senhas"""
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "As senhas não coincidem."
            })
        return attrs
    
    def validate_old_password(self, value):
        """Validar senha antiga"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value
    
    def save(self, **kwargs):
        """Alterar senha do usuário"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
