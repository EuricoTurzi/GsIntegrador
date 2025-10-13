from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modelo de usuário customizado para o sistema Integrador.
    
    Tipos de usuário:
    - GR (Gerente de Risco): Acesso completo ao sistema, visualização de todas as SMs
    - TRANSPORTADORA: Gerencia seus próprios motoristas, veículos e SMs
    """
    
    class UserType(models.TextChoices):
        GR = 'GR', _('Gerente de Risco')
        TRANSPORTADORA = 'TRANSPORTADORA', _('Transportadora')
    
    # Campos básicos
    user_type = models.CharField(
        _('Tipo de Usuário'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.TRANSPORTADORA,
    )
    
    # Campos da empresa/transportadora
    company_name = models.CharField(
        _('Nome da Empresa'),
        max_length=255,
        blank=True,
        help_text=_('Nome da transportadora (obrigatório para tipo TRANSPORTADORA)')
    )
    
    cnpj = models.CharField(
        _('CNPJ'),
        max_length=18,
        blank=True,
        unique=True,
        null=True,
        help_text=_('CNPJ da transportadora (formato: 00.000.000/0000-00)')
    )
    
    phone = models.CharField(
        _('Telefone'),
        max_length=20,
        blank=True,
        help_text=_('Telefone de contato')
    )
    
    # Status e controle
    is_active = models.BooleanField(
        _('Ativo'),
        default=True,
        help_text=_('Usuário pode acessar o sistema')
    )
    
    is_verified = models.BooleanField(
        _('Verificado'),
        default=False,
        help_text=_('Conta foi verificada pelo administrador')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_gr(self):
        """Verifica se o usuário é do tipo GR (Gerente de Risco)"""
        return self.user_type == self.UserType.GR
    
    @property
    def is_transportadora(self):
        """Verifica se o usuário é do tipo Transportadora"""
        return self.user_type == self.UserType.TRANSPORTADORA
    
    def has_permission_to_view_sm(self, sm):
        """
        Verifica se o usuário tem permissão para visualizar uma SM específica.
        
        - GR: pode ver todas as SMs
        - Transportadora: pode ver apenas suas próprias SMs
        """
        if self.is_gr:
            return True
        
        if self.is_transportadora:
            # Verifica se a SM pertence a esta transportadora
            return sm.transportadora == self
        
        return False
    
    def save(self, *args, **kwargs):
        # Se for superuser, automaticamente é GR
        if self.is_superuser and not self.user_type:
            self.user_type = self.UserType.GR
        
        # Validação: Transportadora deve ter company_name
        if self.user_type == self.UserType.TRANSPORTADORA:
            if not self.company_name:
                raise ValueError('Transportadora deve ter um nome de empresa')
        
        super().save(*args, **kwargs)
