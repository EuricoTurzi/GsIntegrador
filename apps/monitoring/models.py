"""
Modelo de Sistema de Monitoramento (SM).
"""
import logging
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from apps.authentication.models import User
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle
from apps.routes.models import Route

logger = logging.getLogger(__name__)


class MonitoringSystem(models.Model):
    """
    Sistema de Monitoramento (SM) que integra Rota, Motorista e Veículo.
    
    Representa um monitoramento ativo de uma viagem/transporte.
    """
    
    STATUS_CHOICES = [
        ('PLANEJADO', 'Planejado'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    # Relacionamentos principais
    transportadora = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='monitoring_systems',
        limit_choices_to={'user_type': 'TRANSPORTADORA'},
        verbose_name='Transportadora'
    )
    
    route = models.ForeignKey(
        Route,
        on_delete=models.PROTECT,
        related_name='monitoring_systems',
        verbose_name='Rota'
    )
    
    driver = models.ForeignKey(
        Driver,
        on_delete=models.PROTECT,
        related_name='monitoring_systems',
        verbose_name='Motorista'
    )
    
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name='monitoring_systems',
        verbose_name='Veículo'
    )
    
    # Identificação
    identifier = models.CharField(
        'Identificador',
        max_length=100,
        unique=True,
        help_text='Código único do SM (ex: SM-2024-0001)'
    )
    
    name = models.CharField(
        'Nome do Monitoramento',
        max_length=200,
        help_text='Nome descritivo do monitoramento'
    )
    
    description = models.TextField(
        'Descrição',
        blank=True,
        null=True
    )
    
    # Status e datas
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANEJADO'
    )
    
    planned_start_date = models.DateTimeField(
        'Data Planejada de Início',
        help_text='Data/hora planejada para início da viagem'
    )
    
    planned_end_date = models.DateTimeField(
        'Data Planejada de Término',
        help_text='Data/hora planejada para término da viagem'
    )
    
    actual_start_date = models.DateTimeField(
        'Data Real de Início',
        blank=True,
        null=True
    )
    
    actual_end_date = models.DateTimeField(
        'Data Real de Término',
        blank=True,
        null=True
    )
    
    # Validação do dispositivo
    device_validated_at = models.DateTimeField(
        'Dispositivo Validado em',
        null=True,
        blank=True,
        help_text='Data/hora da validação do rastreador (preenchido automaticamente)'
    )
    
    device_was_updated = models.BooleanField(
        'Dispositivo Estava Atualizado',
        default=False,
        help_text='Indica se o dispositivo estava atualizado no momento da criação'
    )
    
    # Informações adicionais
    cargo_description = models.TextField(
        'Descrição da Carga',
        blank=True,
        null=True
    )
    
    cargo_value = models.DecimalField(
        'Valor da Carga',
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    observations = models.TextField(
        'Observações',
        blank=True,
        null=True
    )
    
    # Controle
    is_active = models.BooleanField('Ativo', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_monitoring_systems',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Sistema de Monitoramento'
        verbose_name_plural = 'Sistemas de Monitoramento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transportadora', 'status']),
            models.Index(fields=['identifier']),
            models.Index(fields=['status', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.identifier} - {self.name}"
    
    @property
    def duration_days(self):
        """Retorna a duração planejada em dias."""
        if self.planned_start_date and self.planned_end_date:
            delta = self.planned_end_date - self.planned_start_date
            return delta.days
        return None
    
    @property
    def is_in_progress(self):
        """Verifica se o monitoramento está em andamento."""
        return self.status == 'EM_ANDAMENTO'
    
    @property
    def is_completed(self):
        """Verifica se o monitoramento foi concluído."""
        return self.status == 'CONCLUIDO'
    
    @property
    def device_status(self):
        """Retorna o status atual do dispositivo."""
        if hasattr(self.vehicle, 'device'):
            return self.vehicle.device.is_updated_recently
        return False
    
    @property
    def current_vehicle_position(self):
        """Retorna a posição atual do veículo se disponível."""
        if hasattr(self.vehicle, 'device'):
            device = self.vehicle.device
            if device.last_latitude and device.last_longitude:
                return {
                    'latitude': float(device.last_latitude),
                    'longitude': float(device.last_longitude),
                    'address': device.last_address,
                    'speed': float(device.last_speed) if device.last_speed else None,
                    'last_update': device.last_system_date
                }
        return None
    
    def save_position_snapshot(self):
        """
        Salva um snapshot da posição atual no histórico.
        
        Chamado automaticamente quando há nova atualização do dispositivo.
        Evita duplicatas usando unique_together.
        """
        position = self.current_vehicle_position
        
        if not position:
            return None
        
        try:
            # Criar registro de histórico
            history = VehiclePositionHistory.objects.create(
                monitoring_system=self,
                latitude=position['latitude'],
                longitude=position['longitude'],
                address=position['address'],
                speed=position['speed'],
                device_timestamp=position['last_update'],
                extra_data={
                    'device_id': self.vehicle.device.id,
                    'vehicle_placa': self.vehicle.placa,
                }
            )
            logger.info(
                f"Posição salva no histórico: {self.identifier} - "
                f"({position['latitude']}, {position['longitude']})"
            )
            return history
        except Exception as e:
            # Pode ser duplicata (unique_together), não é erro crítico
            logger.debug(f"Não foi possível salvar posição no histórico: {e}")
            return None
    
    def get_position_history(self, limit=None):
        """
        Retorna o histórico de posições da viagem.
        
        Args:
            limit: Número máximo de posições a retornar (None = todas)
        
        Returns:
            QuerySet de VehiclePositionHistory ordenado por data
        """
        queryset = self.position_history.all()
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    def get_position_history_geojson(self):
        """
        Retorna o histórico de posições em formato GeoJSON para mapas.
        
        Returns:
            dict: GeoJSON com LineString das posições
        """
        positions = self.position_history.values_list(
            'longitude', 'latitude', 'device_timestamp', 'speed'
        )
        
        if not positions:
            return None
        
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[float(lng), float(lat)] for lng, lat, _, _ in positions]
            },
            'properties': {
                'monitoring_system': self.identifier,
                'name': self.name,
                'timestamps': [dt.isoformat() for _, _, dt, _ in positions],
                'speeds': [float(speed) if speed else 0 for _, _, _, speed in positions],
                'total_points': len(positions)
            }
        }
    
    def validate_device_update(self):
        """
        Valida se o dispositivo do veículo foi atualizado recentemente.
        
        Raises:
            ValidationError: Se o veículo não possui dispositivo ou está desatualizado
        """
        if not hasattr(self.vehicle, 'device'):
            raise ValidationError({
                'vehicle': 'O veículo deve ter um rastreador vinculado.'
            })
        
        device = self.vehicle.device
        
        if not device.is_active:
            raise ValidationError({
                'vehicle': 'O rastreador do veículo está inativo.'
            })
        
        # Validação crítica: dispositivo deve estar atualizado nos últimos 30 minutos
        if not device.is_updated_recently:
            minutes = device.minutes_since_last_update
            threshold = settings.DEVICE_UPDATE_THRESHOLD_MINUTES
            
            raise ValidationError({
                'vehicle': (
                    f'O rastreador do veículo não está atualizado. '
                    f'Última atualização: {minutes:.1f} minutos atrás. '
                    f'Máximo permitido: {threshold} minutos.'
                )
            })
        
        # Registrar validação bem-sucedida
        self.device_validated_at = timezone.now()
        self.device_was_updated = True
    
    def clean(self):
        """Validações personalizadas."""
        super().clean()
        
        # Validar que todos pertencem à mesma transportadora
        if self.route and self.route.transportadora != self.transportadora:
            raise ValidationError({
                'route': 'A rota deve pertencer à mesma transportadora.'
            })
        
        if self.driver and self.driver.transportadora != self.transportadora:
            raise ValidationError({
                'driver': 'O motorista deve pertencer à mesma transportadora.'
            })
        
        if self.vehicle and self.vehicle.transportadora != self.transportadora:
            raise ValidationError({
                'vehicle': 'O veículo deve pertencer à mesma transportadora.'
            })
        
        # Validar que o motorista está ativo
        if self.driver and not self.driver.is_active:
            raise ValidationError({
                'driver': 'O motorista deve estar ativo.'
            })
        
        # Validar que o veículo está disponível ou em viagem
        if self.vehicle and self.vehicle.status not in ['DISPONIVEL', 'EM_VIAGEM']:
            raise ValidationError({
                'vehicle': f'O veículo está com status "{self.vehicle.get_status_display()}" e não pode ser usado.'
            })
        
        # Validar que a rota está ativa
        if self.route and not self.route.is_active:
            raise ValidationError({
                'route': 'A rota deve estar ativa.'
            })
        
        # Validar datas
        if self.planned_start_date and self.planned_end_date:
            if self.planned_end_date <= self.planned_start_date:
                raise ValidationError({
                    'planned_end_date': 'Data de término deve ser posterior à data de início.'
                })
        
        # VALIDAÇÃO CRÍTICA: Dispositivo atualizado nos últimos 30 minutos
        if self.vehicle:
            self.validate_device_update()
    
    def start_monitoring(self):
        """Inicia o monitoramento."""
        self.status = 'EM_ANDAMENTO'
        self.actual_start_date = timezone.now()
        
        # Atualizar status do veículo
        if self.vehicle:
            self.vehicle.status = 'EM_VIAGEM'
            self.vehicle.save()
        
        self.save()
    
    def complete_monitoring(self):
        """Finaliza o monitoramento."""
        self.status = 'CONCLUIDO'
        self.actual_end_date = timezone.now()
        
        # Atualizar status do veículo
        if self.vehicle:
            self.vehicle.status = 'DISPONIVEL'
            self.vehicle.save()
        
        self.save()
    
    def cancel_monitoring(self, reason=None):
        """Cancela o monitoramento."""
        self.status = 'CANCELADO'
        
        if reason:
            if self.observations:
                self.observations += f"\n\nCancelamento: {reason}"
            else:
                self.observations = f"Cancelamento: {reason}"
        
        # Atualizar status do veículo
        if self.vehicle and self.vehicle.status == 'EM_VIAGEM':
            self.vehicle.status = 'DISPONIVEL'
            self.vehicle.save()
        
        self.save()
    
    def save(self, *args, **kwargs):
        """Sobrescreve o save para validar antes de salvar."""
        # Gerar identifier se não existir
        if not self.identifier:
            from datetime import datetime
            year = datetime.now().year
            count = MonitoringSystem.objects.filter(
                identifier__startswith=f'SM-{year}-'
            ).count() + 1
            self.identifier = f'SM-{year}-{count:04d}'
        
        self.full_clean()
        super().save(*args, **kwargs)


class VehiclePositionHistory(models.Model):
    """
    Histórico de posições do veículo durante uma viagem.
    
    Armazena snapshots das posições capturadas durante o monitoramento,
    permitindo visualizar o trajeto percorrido.
    """
    
    monitoring_system = models.ForeignKey(
        MonitoringSystem,
        on_delete=models.CASCADE,
        related_name='position_history',
        verbose_name='Sistema de Monitoramento'
    )
    
    # Dados da posição (snapshot do momento)
    latitude = models.DecimalField(
        'Latitude',
        max_digits=10,
        decimal_places=7,
        help_text='Latitude da posição'
    )
    
    longitude = models.DecimalField(
        'Longitude',
        max_digits=10,
        decimal_places=7,
        help_text='Longitude da posição'
    )
    
    address = models.CharField(
        'Endereço',
        max_length=500,
        blank=True,
        null=True,
        help_text='Endereço aproximado da posição'
    )
    
    speed = models.DecimalField(
        'Velocidade (km/h)',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    heading = models.IntegerField(
        'Direção (graus)',
        blank=True,
        null=True,
        help_text='Direção do veículo em graus (0-360)'
    )
    
    altitude = models.DecimalField(
        'Altitude (m)',
        max_digits=7,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Metadados
    device_timestamp = models.DateTimeField(
        'Data/Hora do Dispositivo',
        help_text='Data/hora reportada pelo rastreador'
    )
    
    server_timestamp = models.DateTimeField(
        'Data/Hora do Servidor',
        auto_now_add=True,
        help_text='Data/hora em que a posição foi registrada no sistema'
    )
    
    # Informações extras (JSON para dados adicionais da API)
    extra_data = models.JSONField(
        'Dados Extras',
        blank=True,
        null=True,
        help_text='Dados adicionais da API (ignição, bateria, etc.)'
    )
    
    class Meta:
        verbose_name = 'Histórico de Posição'
        verbose_name_plural = 'Histórico de Posições'
        ordering = ['-device_timestamp']
        indexes = [
            models.Index(fields=['monitoring_system', '-device_timestamp']),
            models.Index(fields=['monitoring_system', 'server_timestamp']),
        ]
        # Evitar duplicatas: mesma posição no mesmo segundo
        unique_together = [['monitoring_system', 'device_timestamp', 'latitude', 'longitude']]
    
    def __str__(self):
        return f"{self.monitoring_system.identifier} - {self.device_timestamp}"
    
    @property
    def position_tuple(self):
        """Retorna (lat, lng) para facilitar uso em mapas."""
        return (float(self.latitude), float(self.longitude))
