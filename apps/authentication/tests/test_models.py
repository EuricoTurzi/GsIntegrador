"""
Testes do modelo User.
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.authentication.tests.factories import UserFactory, UserGRFactory, UserTransportadoraFactory

User = get_user_model()


@pytest.mark.unit
@pytest.mark.django_db
class TestUserModel:
    """Testes do modelo User."""
    
    def test_create_user_gr(self):
        """Testa criação de usuário GR."""
        user = UserGRFactory()
        assert user.user_type == 'GR'
        assert user.is_gr is True
        assert user.is_transportadora is False
        assert user.company_name == ''  # GR tem company_name vazio
        assert user.cnpj is None  # GR tem cnpj None
    
    def test_create_user_transportadora(self):
        """Testa criação de usuário Transportadora."""
        user = UserTransportadoraFactory()
        assert user.user_type == 'TRANSPORTADORA'
        assert user.is_gr is False
        assert user.is_transportadora is True
        assert user.company_name is not None
        assert user.cnpj is not None
    
    def test_user_str(self):
        """Testa representação string do usuário."""
        user = UserTransportadoraFactory(username='testuser')
        assert 'testuser' in str(user)
    
    def test_is_gr_property(self):
        """Testa propriedade is_gr."""
        user = UserGRFactory()
        assert user.is_gr is True
        assert user.is_transportadora is False
    
    def test_is_transportadora_property(self):
        """Testa propriedade is_transportadora."""
        user = UserTransportadoraFactory()
        assert user.is_transportadora is True
        assert user.is_gr is False
    
    def test_user_type_choices(self):
        """Testa que apenas tipos válidos são aceitos."""
        user = UserFactory.build(user_type='INVALID')
        with pytest.raises(ValidationError):
            user.full_clean()
    
    def test_email_required(self):
        """Testa que email é obrigatório."""
        user = User(username='test', user_type='GR')
        with pytest.raises(ValidationError):
            user.full_clean()
    
    def test_unique_username(self):
        """Testa que username deve ser único."""
        UserFactory(username='duplicate')
        with pytest.raises(Exception):  # IntegrityError
            UserFactory(username='duplicate')
    
    def test_unique_email(self):
        """Testa que email deve ser único."""
        UserFactory(email='duplicate@test.com')
        with pytest.raises(Exception):  # IntegrityError
            UserFactory(email='duplicate@test.com')


@pytest.mark.unit
@pytest.mark.django_db
class TestUserManager:
    """Testes do gerenciador de usuários."""
    
    def test_create_user_transportadora(self):
        """Testa criação de usuário transportadora normal."""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            user_type='TRANSPORTADORA',
            company_name='Test Company',
            cnpj='12.345.678/0001-90'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@test.com'
        assert user.check_password('testpass123')
        assert user.is_staff is False
        assert user.is_superuser is False
    
    def test_create_superuser(self):
        """Testa criação de superusuário."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            user_type='GR'
        )
        assert user.is_staff is True
        assert user.is_superuser is True
    
    def test_create_user_without_username_raises_error(self):
        """Testa que criar usuário sem username gera erro."""
        with pytest.raises(ValueError):
            User.objects.create_user(username='', email='test@test.com')
    
    def test_create_user_without_email_raises_error(self):
        """Testa que criar usuário sem email gera erro."""
        with pytest.raises(ValueError):
            User.objects.create_user(username='test', email='')
