"""
Testes do modelo Driver.
"""
import pytest
from django.core.exceptions import ValidationError
from apps.drivers.models import Driver
from apps.drivers.tests.factories import DriverFactory
from apps.authentication.tests.factories import UserTransportadoraFactory


@pytest.mark.unit
@pytest.mark.django_db
class TestDriverModel:
    """Testes do modelo Driver."""
    
    def test_create_driver_success(self):
        """Testa criação de motorista com sucesso."""
        driver = DriverFactory()
        assert driver.id is not None
        assert driver.nome is not None
        assert driver.cpf is not None
        assert driver.is_active is True
    
    def test_driver_str(self):
        """Testa representação string do motorista."""
        driver = DriverFactory(nome='João Silva')
        assert 'João Silva' in str(driver)
    
    def test_driver_nome_curto_property(self):
        """Testa propriedade nome_curto."""
        driver = DriverFactory(nome='João Silva Santos')
        # Nome curto retorna primeiro e último nome
        assert driver.nome_curto == 'João Santos'
    
    def test_driver_nome_curto_single_name(self):
        """Testa nome_curto com nome único."""
        driver = DriverFactory(nome='João')
        assert driver.nome_curto == 'João'
    
    def test_cpf_format_validation(self):
        """Testa validação de formato do CPF."""
        transportadora = UserTransportadoraFactory()
        driver = DriverFactory.build(transportadora=transportadora, cpf='123.456.789-01')
        driver.full_clean()  # Deve passar
        assert driver.cpf == '123.456.789-01'
    
    def test_cpf_invalid_format_fails(self):
        """Testa que CPF com formato inválido falha."""
        driver = DriverFactory.build(cpf='12345678901')  # Sem formatação
        with pytest.raises(ValidationError) as exc:
            driver.full_clean()
        assert 'cpf' in str(exc.value).lower()
    
    def test_rg_format_validation(self):
        """Testa validação de formato do RG."""
        transportadora = UserTransportadoraFactory()
        driver = DriverFactory.build(transportadora=transportadora, rg='12.345.678-9')
        driver.full_clean()  # Deve passar
        assert driver.rg == '12.345.678-9'
    
    def test_rg_invalid_format_fails(self):
        """Testa que RG com formato inválido falha."""
        driver = DriverFactory.build(rg='123456789')  # Sem formatação
        with pytest.raises(ValidationError) as exc:
            driver.full_clean()
        assert 'rg' in str(exc.value).lower()
    
    def test_cnh_format_validation(self):
        """Testa validação de formato da CNH."""
        transportadora = UserTransportadoraFactory()
        driver = DriverFactory.build(transportadora=transportadora, cnh='12345678901')  # 11 dígitos
        driver.full_clean()  # Deve passar
        assert driver.cnh == '12345678901'
    
    def test_cnh_invalid_length_fails(self):
        """Testa que CNH com tamanho inválido falha."""
        driver = DriverFactory.build(cnh='123456789')  # Menos de 11 dígitos
        with pytest.raises(ValidationError) as exc:
            driver.full_clean()
        assert 'cnh' in str(exc.value).lower()
    
    def test_unique_cpf_constraint(self):
        """Testa que CPF deve ser único."""
        driver1 = DriverFactory(cpf='123.456.789-01')
        driver2 = DriverFactory.build(cpf='123.456.789-01')
        
        with pytest.raises(ValidationError) as exc:
            driver2.full_clean()
        assert 'cpf' in str(exc.value).lower()
    
    def test_unique_cnh_constraint(self):
        """Testa que CNH deve ser única."""
        driver1 = DriverFactory(cnh='12345678901')
        driver2 = DriverFactory.build(cnh='12345678901')
        
        with pytest.raises(ValidationError) as exc:
            driver2.full_clean()
        assert 'cnh' in str(exc.value).lower()
    
    def test_driver_belongs_to_transportadora(self):
        """Testa que motorista pertence a uma transportadora."""
        transportadora = UserTransportadoraFactory()
        driver = DriverFactory(transportadora=transportadora)
        
        assert driver.transportadora == transportadora
        assert driver.transportadora.is_transportadora is True
    
    def test_driver_tipo_de_veiculo_choices(self):
        """Testa tipos de veículo permitidos."""
        tipos_validos = ['Caminhão', 'Carreta', 'Van', 'Outros']
        
        for tipo in tipos_validos:
            driver = DriverFactory(tipo_de_veiculo=tipo)
            assert driver.tipo_de_veiculo == tipo
    
    def test_driver_active_inactive(self):
        """Testa status ativo/inativo do motorista."""
        driver = DriverFactory(is_active=True)
        assert driver.is_active is True
        
        driver.is_active = False
        driver.save()
        assert driver.is_active is False
    
    def test_driver_email_optional(self):
        """Testa que email é opcional."""
        driver = DriverFactory(email='')
        assert driver.email == ''
    
    def test_driver_telefone_required(self):
        """Testa que telefone é obrigatório."""
        driver = DriverFactory.build(telefone='')
        with pytest.raises(ValidationError):
            driver.full_clean()
    
    def test_driver_observacoes_optional(self):
        """Testa que observações são opcionais."""
        driver = DriverFactory(observacoes='')
        assert driver.observacoes == ''
        
        driver.observacoes = 'Motorista experiente'
        driver.save()
        assert driver.observacoes == 'Motorista experiente'
