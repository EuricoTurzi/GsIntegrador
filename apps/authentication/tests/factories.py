"""
Factories para testes do app authentication.
"""
import factory
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()
fake = Faker('pt_BR')


class UserFactory(factory.django.DjangoModelFactory):
    """Factory para criar usuários."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    user_type = 'TRANSPORTADORA'
    is_verified = True
    is_active = True
    
    # Campos para transportadora
    company_name = factory.LazyFunction(lambda: fake.company())
    cnpj = '12.345.678/0001-90'
    phone = factory.LazyFunction(lambda: fake.phone_number())


class UserGRFactory(UserFactory):
    """Factory para criar usuários GR."""
    
    user_type = 'GR'
    company_name = ''  # GR não precisa de company_name
    cnpj = None  # GR não precisa de CNPJ (None para não conflitar com UNIQUE)


class UserTransportadoraFactory(UserFactory):
    """Factory para criar usuários Transportadora."""
    
    user_type = 'TRANSPORTADORA'
    company_name = factory.LazyFunction(lambda: fake.company())
    cnpj = factory.Sequence(lambda n: f'{n:02d}.{n+10:03d}.{n+100:03d}/0001-{n%100:02d}')
