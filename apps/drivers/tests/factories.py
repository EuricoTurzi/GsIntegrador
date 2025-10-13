"""
Factories para testes do app drivers.
"""
import factory
from apps.drivers.models import Driver
from apps.authentication.tests.factories import UserTransportadoraFactory
from faker import Faker

fake = Faker('pt_BR')


class DriverFactory(factory.django.DjangoModelFactory):
    """Factory para criar motoristas."""
    
    class Meta:
        model = Driver
    
    transportadora = factory.SubFactory(UserTransportadoraFactory)
    nome = factory.LazyFunction(lambda: fake.name())
    cpf = factory.Sequence(lambda n: f'{n:03d}.{n+100:03d}.{n+200:03d}-{n%100:02d}')
    rg = factory.Sequence(lambda n: f'{n:02d}.{n+100:03d}.{n+200:03d}-{n%10:01d}')
    cnh = factory.Sequence(lambda n: f'{n:011d}')
    nome_do_pai = factory.LazyFunction(lambda: fake.name_male())
    nome_da_mae = factory.LazyFunction(lambda: fake.name_female())
    tipo_de_veiculo = 'Caminhão'
    data_nascimento = factory.LazyFunction(lambda: fake.date_of_birth(minimum_age=21, maximum_age=70))
    telefone = factory.LazyFunction(lambda: fake.phone_number())
    email = factory.LazyFunction(lambda: fake.email())
    endereco = factory.LazyFunction(lambda: fake.address())
    is_active = True
    observacoes = ''
