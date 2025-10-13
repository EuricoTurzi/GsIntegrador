"""
Modelo de Dispositivos/Rastreadores.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from apps.vehicles.models import Vehicle
from apps.integrations.suntech_client import suntech_client, SuntechAPIError


class Device(models.Model):
    """
    Modelo representando um dispositivo/rastreador Suntech vinculado a um veículo.
    """
    
    # Relacionamento com veículo (OneToOne)
    vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='device',
        verbose_name='Veículo'
    )
    
    # Dados do dispositivo Suntech
    suntech_device_id = models.IntegerField(
        'ID Dispositivo Suntech',
        unique=True,
        help_text='ID do dispositivo na plataforma Suntech'
    )
    
    suntech_vehicle_id = models.IntegerField(
        'ID Veículo Suntech',
        help_text='ID do veículo na plataforma Suntech'
    )
    
    imei = models.CharField(
        'IMEI',
        max_length=20,
        blank=True,
        null=True,
        help_text='IMEI do dispositivo'
    )
    
    label = models.CharField(
        'Identificação',
        max_length=100,
        blank=True,
        null=True,
        help_text='Nome/identificação do dispositivo na Suntech'
    )
    
    # Status e dados de telemetria
    last_position_date = models.DateTimeField(
        'Data Última Posição',
        blank=True,
        null=True,
        help_text='Data/hora da última posição GPS'
    )
    
    last_system_date = models.DateTimeField(
        'Data Última Atualização Sistema',
        blank=True,
        null=True,
        help_text='Data/hora de recebimento no servidor Suntech'
    )
    
    last_latitude = models.DecimalField(
        'Última Latitude',
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )
    
    last_longitude = models.DecimalField(
        'Última Longitude',
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )
    
    last_address = models.TextField(
        'Último Endereço',
        blank=True,
        null=True
    )
    
    last_speed = models.DecimalField(
        'Última Velocidade (km/h)',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    last_ignition_status = models.CharField(
        'Status Ignição',
        max_length=10,
        blank=True,
        null=True,
        choices=[
            ('ON', 'Ligada'),
            ('OFF', 'Desligada')
        ]
    )
    
    odometer = models.BigIntegerField(
        'Odômetro (metros)',
        blank=True,
        null=True
    )
    
    # Controle
    is_active = models.BooleanField('Ativo', default=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    last_sync_at = models.DateTimeField('Última Sincronização', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['suntech_device_id']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Device {self.suntech_device_id} - {self.vehicle.placa}"
    
    @property
    def identifier(self):
        """
        Retorna identificação do device: label se disponível, senão suntech_device_id.
        """
        return self.label or str(self.suntech_device_id)
    
    @property
    def is_updated_recently(self):
        """
        Verifica se o dispositivo foi atualizado recentemente (últimos 30 minutos).
        """
        if not self.last_system_date:
            return False
        
        from django.conf import settings
        threshold_minutes = settings.DEVICE_UPDATE_THRESHOLD_MINUTES
        
        now = timezone.now()
        time_diff = now - self.last_system_date
        
        return time_diff.total_seconds() / 60 <= threshold_minutes
    
    @property
    def minutes_since_last_update(self):
        """
        Retorna quantos minutos se passaram desde a última atualização.
        """
        if not self.last_system_date:
            return None
        
        now = timezone.now()
        time_diff = now - self.last_system_date
        
        return round(time_diff.total_seconds() / 60, 2)
    
    @property
    def odometer_km(self):
        """
        Retorna o odômetro em quilômetros.
        """
        if self.odometer:
            return round(self.odometer / 1000, 2)
        return None
    
    def sync_with_suntech(self):
        """
        Sincroniza os dados do dispositivo com a API Suntech.
        
        Returns:
            bool: True se sincronização foi bem-sucedida
        """
        try:
            # Buscar dados do dispositivo na API Suntech
            # Force fresh fetch from Suntech API (bypass cache) to avoid stale positions
            vehicle_data = suntech_client.get_vehicle_by_device_id(self.suntech_device_id, use_cache=False)
            
            if not vehicle_data:
                return False
            
            # Atualizar dados do dispositivo
            self.suntech_vehicle_id = vehicle_data.get('vehicleId')
            self.label = vehicle_data.get('label')
            
            # Atualizar dados de telemetria
            date_str = vehicle_data.get('date')
            system_date_str = vehicle_data.get('systemDate')
            
            if date_str:
                from datetime import datetime
                self.last_position_date = timezone.make_aware(
                    datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                )
            
            if system_date_str:
                from datetime import datetime
                self.last_system_date = timezone.make_aware(
                    datetime.strptime(system_date_str, '%Y-%m-%d %H:%M:%S')
                )
            
            self.last_latitude = vehicle_data.get('latitude')
            self.last_longitude = vehicle_data.get('longitude')
            self.last_address = vehicle_data.get('address')
            self.last_speed = vehicle_data.get('speed')
            self.last_ignition_status = vehicle_data.get('ignition')
            self.odometer = vehicle_data.get('odometer')
            
            self.last_sync_at = timezone.now()
            self.save()
            
            return True
            
        except SuntechAPIError:
            return False
    
    def check_suntech_status(self):
        """
        Verifica o status de atualização do dispositivo diretamente na API Suntech.
        
        Returns:
            bool: True se o dispositivo está atualizado
        """
        try:
            return suntech_client.check_device_updated_recently(self.suntech_device_id)
        except SuntechAPIError:
            return False
    
    def clean(self):
        """
        Validações personalizadas.
        """
        super().clean()
        
        # Validar que o suntech_device_id é único
        if self.pk:
            existing = Device.objects.filter(
                suntech_device_id=self.suntech_device_id
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({
                    'suntech_device_id': 'Já existe um dispositivo com este ID Suntech.'
                })
        
        # Validar que o veículo não possui outro dispositivo
        if self.pk:
            existing = Device.objects.filter(vehicle=self.vehicle).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({
                    'vehicle': 'Este veículo já possui um dispositivo vinculado.'
                })
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o save para validar antes de salvar.
        """
        self.full_clean()
        super().save(*args, **kwargs)
