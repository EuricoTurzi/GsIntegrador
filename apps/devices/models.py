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
        
        🛡️ Validação de timestamp agora é feita automaticamente no save()
        
        Returns:
            bool: True se sincronização foi bem-sucedida
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Buscar dados do dispositivo na API Suntech
            # Force fresh fetch from Suntech API (bypass cache) to avoid stale positions
            vehicle_data = suntech_client.get_vehicle_by_device_id(self.suntech_device_id, use_cache=False)
            
            if not vehicle_data:
                logger.warning(f"Device {self.suntech_device_id}: Nenhum dado retornado pela API Suntech")
                return False
            
            # Atualizar dados do dispositivo
            self.suntech_vehicle_id = vehicle_data.get('vehicleId')
            self.label = vehicle_data.get('label')
            
            # Processar timestamps
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
            
            # Atualizar dados de telemetria
            self.last_latitude = vehicle_data.get('latitude')
            self.last_longitude = vehicle_data.get('longitude')
            self.last_address = vehicle_data.get('address')
            self.last_speed = vehicle_data.get('speed')
            self.last_ignition_status = vehicle_data.get('ignition')
            self.odometer = vehicle_data.get('odometer')
            
            self.last_sync_at = timezone.now()
            
            # save() irá validar timestamp automaticamente
            # Se posição for antiga, ValidationError será lançado
            self.save()
            
            logger.info(
                f"Device {self.suntech_device_id} sincronizado com sucesso - "
                f"Posição: ({self.last_latitude}, {self.last_longitude})"
            )
            
            return True
            
        except ValidationError as e:
            # Posição antiga rejeitada pelo save()
            logger.warning(f"Device {self.suntech_device_id}: {e}")
            return False
        except SuntechAPIError as e:
            logger.error(f"Device {self.suntech_device_id}: Erro na API Suntech: {e}")
            return False
        except Exception as e:
            logger.error(f"Device {self.suntech_device_id}: Erro inesperado: {e}", exc_info=True)
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
    
    def save(self, *args, skip_timestamp_validation=False, **kwargs):
        """
        Sobrescreve o save para validar timestamp antes de salvar.
        
        🛡️ VALIDAÇÃO CRÍTICA DE TIMESTAMP:
        - Rejeita posições com timestamp mais antigo que o último registrado
        - Previne tracking devastado por posições antigas
        - Garante consistência em 100+ dispositivos em tempo real
        
        Args:
            skip_timestamp_validation: Se True, pula validação (usar apenas em setup/testes)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 🛡️ VALIDAÇÃO DE TIMESTAMP - Single Source of Truth
        if not skip_timestamp_validation and self.pk and self.last_system_date:
            try:
                # Buscar timestamp atual do banco
                old_device = Device.objects.only('last_system_date', 'suntech_device_id').get(pk=self.pk)
                
                if old_device.last_system_date:
                    # Comparar timestamps
                    if self.last_system_date < old_device.last_system_date:
                        # POSIÇÃO ANTIGA - REJEITAR
                        time_diff = (old_device.last_system_date - self.last_system_date).total_seconds()
                        
                        error_msg = (
                            f"🚨 POSIÇÃO ANTIGA REJEITADA: "
                            f"Device {self.suntech_device_id} "
                            f"({self.vehicle.placa if hasattr(self, 'vehicle') else 'N/A'}) - "
                            f"Tentativa de salvar timestamp {self.last_system_date.isoformat()} "
                            f"mais antigo que o atual {old_device.last_system_date.isoformat()} - "
                            f"Diferença: {time_diff:.0f}s ({time_diff/60:.1f} min) mais antiga"
                        )
                        
                        logger.error(error_msg)
                        
                        raise ValidationError({
                            'last_system_date': (
                                f'Posição rejeitada: timestamp {time_diff/60:.1f} minutos '
                                f'mais antigo que a posição atual. '
                                f'Use skip_timestamp_validation=True apenas se necessário.'
                            )
                        })
                    
                    elif self.last_system_date == old_device.last_system_date:
                        # Mesmo timestamp - aceitar mas logar
                        logger.debug(
                            f"Device {self.suntech_device_id}: "
                            f"Mesmo timestamp (duplicata), permitindo..."
                        )
                    
                    else:
                        # Timestamp mais recente - OK
                        time_diff = (self.last_system_date - old_device.last_system_date).total_seconds()
                        logger.info(
                            f"✅ Device {self.suntech_device_id} "
                            f"({self.vehicle.placa if hasattr(self, 'vehicle') else 'N/A'}): "
                            f"Nova posição válida - "
                            f"Anterior: {old_device.last_system_date.isoformat()} - "
                            f"Nova: {self.last_system_date.isoformat()} - "
                            f"Diferença: +{time_diff:.0f}s (+{time_diff/60:.1f} min)"
                        )
                        
            except Device.DoesNotExist:
                # Novo dispositivo - pular validação
                pass
        
        self.full_clean()
        super().save(*args, **kwargs)
