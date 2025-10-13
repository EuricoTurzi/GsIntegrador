from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class Driver(models.Model):
    """
    Modelo de Motorista
    
    Armazena informações dos motoristas cadastrados pelas transportadoras.
    Cada motorista pertence a uma transportadora específica.
    """
    
    # Validadores
    cpf_validator = RegexValidator(
        regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
        message='CPF deve estar no formato: 000.000.000-00'
    )
    
    rg_validator = RegexValidator(
        regex=r'^\d{2}\.\d{3}\.\d{3}-\d{1}$',
        message='RG deve estar no formato: 00.000.000-0'
    )
    
    cnh_validator = RegexValidator(
        regex=r'^\d{11}$',
        message='CNH deve conter 11 dígitos'
    )
    
    # Relacionamento
    transportadora = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='drivers',
        verbose_name=_('Transportadora'),
        limit_choices_to={'user_type': 'TRANSPORTADORA'},
        help_text=_('Transportadora responsável pelo motorista')
    )
    
    # Dados pessoais
    nome = models.CharField(
        _('Nome Completo'),
        max_length=255,
        help_text=_('Nome completo do motorista')
    )
    
    cpf = models.CharField(
        _('CPF'),
        max_length=14,
        unique=True,
        validators=[cpf_validator],
        help_text=_('CPF no formato: 000.000.000-00')
    )
    
    rg = models.CharField(
        _('RG'),
        max_length=12,
        validators=[rg_validator],
        help_text=_('RG no formato: 00.000.000-0')
    )
    
    cnh = models.CharField(
        _('CNH'),
        max_length=11,
        unique=True,
        validators=[cnh_validator],
        help_text=_('Carteira Nacional de Habilitação (11 dígitos)')
    )
    
    nome_do_pai = models.CharField(
        _('Nome do Pai'),
        max_length=255,
        blank=True,
        help_text=_('Nome completo do pai')
    )
    
    nome_da_mae = models.CharField(
        _('Nome da Mãe'),
        max_length=255,
        help_text=_('Nome completo da mãe')
    )
    
    # Tipo de veículo que pode dirigir
    tipo_de_veiculo = models.CharField(
        _('Tipo de Veículo'),
        max_length=100,
        help_text=_('Tipo de veículo que o motorista está habilitado a dirigir')
    )
    
    # Dados adicionais
    data_nascimento = models.DateField(
        _('Data de Nascimento'),
        null=True,
        blank=True,
        help_text=_('Data de nascimento do motorista')
    )
    
    telefone = models.CharField(
        _('Telefone'),
        max_length=20,
        blank=True,
        help_text=_('Telefone de contato')
    )
    
    email = models.EmailField(
        _('E-mail'),
        blank=True,
        help_text=_('E-mail de contato')
    )
    
    endereco = models.TextField(
        _('Endereço'),
        blank=True,
        help_text=_('Endereço completo')
    )
    
    # Status
    is_active = models.BooleanField(
        _('Ativo'),
        default=True,
        help_text=_('Motorista está ativo e pode ser designado para viagens')
    )
    
    observacoes = models.TextField(
        _('Observações'),
        blank=True,
        help_text=_('Observações adicionais sobre o motorista')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Motorista')
        verbose_name_plural = _('Motoristas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cpf']),
            models.Index(fields=['cnh']),
            models.Index(fields=['transportadora', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.nome} - CPF: {self.cpf}"
    
    @property
    def nome_curto(self):
        """Retorna apenas o primeiro e último nome"""
        partes = self.nome.split()
        if len(partes) > 1:
            return f"{partes[0]} {partes[-1]}"
        return self.nome
    
    def clean(self):
        """Validações customizadas"""
        from django.core.exceptions import ValidationError
        
        # CPF deve ser único
        if Driver.objects.filter(cpf=self.cpf).exclude(pk=self.pk).exists():
            raise ValidationError({'cpf': 'Já existe um motorista com este CPF.'})
        
        # CNH deve ser única
        if Driver.objects.filter(cnh=self.cnh).exclude(pk=self.pk).exists():
            raise ValidationError({'cnh': 'Já existe um motorista com esta CNH.'})
