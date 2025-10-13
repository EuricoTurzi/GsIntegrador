"""
Factories para testes do app vehicles.
"""
import factory
from apps.vehicles.models import Vehicle
from apps.authentication.tests.factories import UserTransportadoraFactory
from faker import Faker

fake = Faker('pt_BR')


class VehicleFactory(factory.django.DjangoModelFactory):
    """Factory para criar veículos."""
    
    class Meta:
        model = Vehicle
    
    transportadora = factory.SubFactory(UserTransportadoraFactory)
    status = 'DISPONIVEL'
    placa = factory.Sequence(lambda n: f'ABC{n%10}{chr(65 + n%26)}{(n//10)%10}{n%10}')  # ABC1D23
    ano = factory.LazyFunction(lambda: fake.random_int(min=2000, max=2025))
    cor = factory.LazyFunction(lambda: fake.random_element(elements=('Branco', 'Preto', 'Prata', 'Vermelho', 'Azul')))
    modelo = factory.LazyFunction(lambda: fake.random_element(elements=(
        'Mercedes-Benz Actros',
        'Scania R450',
        'Volvo FH 460',
        'Volkswagen Constellation',
        'Iveco Stralis'
    )))
    renavam = factory.Sequence(lambda n: f'{n:011d}')  # 11 dígitos
    chassi = factory.Sequence(lambda n: f'9BW{n:014d}')  # 17 caracteres sem I, O, Q
    is_active = True
    observacoes = ''
