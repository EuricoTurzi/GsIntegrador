"""
Configuração global para testes do projeto Integrador.

Este arquivo contém fixtures compartilhadas entre todos os apps.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from faker import Faker

User = get_user_model()
fake = Faker('pt_BR')


@pytest.fixture
def api_client():
    """Cliente API para testes."""
    return APIClient()


@pytest.fixture
def user_gr(db):
    """Usuário do tipo GR (Gerente de Risco)."""
    return User.objects.create_user(
        username='gr_test',
        email='gr@test.com',
        password='testpass123',
        user_type='GR',
        is_verified=True
    )


@pytest.fixture
def user_transportadora(db):
    """Usuário do tipo Transportadora."""
    return User.objects.create_user(
        username='transportadora_test',
        email='transportadora@test.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora Teste Ltda',
        cnpj='12.345.678/0001-90',
        is_verified=True
    )


@pytest.fixture
def user_transportadora_2(db):
    """Segunda transportadora para testar isolamento de dados."""
    return User.objects.create_user(
        username='transportadora2_test',
        email='transportadora2@test.com',
        password='testpass123',
        user_type='TRANSPORTADORA',
        company_name='Transportadora 2 Ltda',
        cnpj='98.765.432/0001-10',
        is_verified=True
    )


@pytest.fixture
def authenticated_client_gr(api_client, user_gr):
    """Cliente autenticado como GR."""
    api_client.force_authenticate(user=user_gr)
    return api_client


@pytest.fixture
def authenticated_client_transportadora(api_client, user_transportadora):
    """Cliente autenticado como Transportadora."""
    api_client.force_authenticate(user=user_transportadora)
    return api_client


@pytest.fixture
def authenticated_client_transportadora_2(api_client, user_transportadora_2):
    """Cliente autenticado como segunda Transportadora."""
    api_client.force_authenticate(user=user_transportadora_2)
    return api_client
