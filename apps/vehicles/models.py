"""
Modelo de Veículos.
"""
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from apps.authentication.models import User


class Vehicle(models.Model):
    """
    Modelo representando um veículo da transportadora.
    """
    
    STATUS_CHOICES = [
        ('DISPONIVEL', 'Disponível'),
        ('EM_VIAGEM', 'Em Viagem'),
        ('MANUTENCAO', 'Manutenção'),
        ('INATIVO', 'Inativo'),
    ]
    
    # Relacionamento
    transportadora = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicles',
        limit_choices_to={'user_type': 'TRANSPORTADORA'},
        verbose_name='Transportadora'
    )
    
    # Dados do veículo
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='DISPONIVEL'
    )
    
    placa = models.CharField(
        'Placa',
        max_length=8,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$',
                message='Placa deve estar no formato ABC1234 ou ABC1D23 (Mercosul)'
            )
        ],
        help_text='Formato: ABC1234 ou ABC1D23 (Mercosul)'
    )
    
    ano = models.IntegerField(
        'Ano',
        validators=[
            RegexValidator(
                regex=r'^\d{4}$',
                message='Ano deve conter 4 dígitos'
            )
        ]
    )
    
    cor = models.CharField(
        'Cor',
        max_length=50
    )
    
    modelo = models.CharField(
        'Modelo',
        max_length=100
    )
    
    renavam = models.CharField(
        'Renavam',
        max_length=11,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{11}$',
                message='Renavam deve conter exatamente 11 dígitos'
            )
        ]
    )
    
    chassi = models.CharField(
        'Chassi',
        max_length=17,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-HJ-NPR-Z0-9]{17}$',
                message='Chassi deve conter 17 caracteres alfanuméricos (sem I, O, Q)'
            )
        ],
        help_text='17 caracteres alfanuméricos (VIN)'
    )
    
    # Controle
    is_active = models.BooleanField('Ativo', default=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Veículo'
        verbose_name_plural = 'Veículos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['placa']),
            models.Index(fields=['transportadora', 'status']),
        ]
    
    def __str__(self):
        return f"{self.placa} - {self.modelo}"
    
    @property
    def placa_formatada(self):
        """Retorna a placa formatada com hífen."""
        if len(self.placa) == 7:
            # Formato antigo: ABC-1234
            return f"{self.placa[:3]}-{self.placa[3:]}"
        elif len(self.placa) == 8:
            # Formato Mercosul: ABC-1D23
            return f"{self.placa[:3]}-{self.placa[3:]}"
        return self.placa
    
    @property
    def esta_disponivel(self):
        """Verifica se o veículo está disponível para uso."""
        return self.is_active and self.status == 'DISPONIVEL'
    
    @property
    def tem_rastreador(self):
        """Verifica se o veículo possui um rastreador ativo."""
        return hasattr(self, 'device') and self.device.is_active
    
    def clean(self):
        """Validações personalizadas."""
        super().clean()
        
        # Validar placa única
        if self.pk:
            existing = Vehicle.objects.filter(placa=self.placa).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'placa': 'Já existe um veículo com esta placa.'})
        
        # Validar renavam único
        if self.pk:
            existing = Vehicle.objects.filter(renavam=self.renavam).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'renavam': 'Já existe um veículo com este Renavam.'})
        
        # Validar chassi único
        if self.pk:
            existing = Vehicle.objects.filter(chassi=self.chassi).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'chassi': 'Já existe um veículo com este Chassi.'})
        
        # Validar ano
        from datetime import datetime
        current_year = datetime.now().year
        if self.ano < 1900 or self.ano > current_year + 1:
            raise ValidationError({'ano': f'Ano deve estar entre 1900 e {current_year + 1}.'})
    
    def save(self, *args, **kwargs):
        """Sobrescreve o save para normalizar a placa."""
        # Converter placa para maiúsculas
        if self.placa:
            self.placa = self.placa.upper().replace('-', '')
        
        # Validar antes de salvar
        self.full_clean()
        super().save(*args, **kwargs)
