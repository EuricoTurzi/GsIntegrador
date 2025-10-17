"""
Modelo de Sistema de Monitoramento (SM).
"""
import logging
import math
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from apps.authentication.models import User
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle
from apps.routes.models import Route

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula a distância em metros entre dois pontos usando fórmula de Haversine.
    
    Args:
        lat1, lon1: Coordenadas do ponto 1
        lat2, lon2: Coordenadas do ponto 2
    
    Returns:
        float: Distância em metros
    """
    R = 6371000  # Raio da Terra em metros
    
    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    delta_lat = math.radians(float(lat2) - float(lat1))
    delta_lon = math.radians(float(lon2) - float(lon1))
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


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
    
    # 🆕 Análise de Viagem e Desvios
    route_deviation_tolerance_meters = models.IntegerField(
        'Tolerância Desvio de Rota (m)',
        default=200,
        help_text='Distância máxima permitida da rota planejada antes de alertar (em metros)'
    )
    
    total_distance_traveled = models.DecimalField(
        'Distância Total Percorrida (km)',
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Distância total calculada a partir das posições capturadas'
    )
    
    max_speed_recorded = models.DecimalField(
        'Velocidade Máxima Registrada (km/h)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    average_speed = models.DecimalField(
        'Velocidade Média (km/h)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    total_stops = models.IntegerField(
        'Total de Paradas',
        default=0,
        help_text='Número de paradas detectadas (velocidade = 0 por mais de 5 min)'
    )
    
    total_route_deviations = models.IntegerField(
        'Total de Desvios de Rota',
        default=0,
        help_text='Número de vezes que o veículo saiu da rota planejada'
    )
    
    has_active_deviation = models.BooleanField(
        'Desvio Ativo',
        default=False,
        help_text='Indica se o veículo está atualmente fora da rota'
    )
    
    last_deviation_detected_at = models.DateTimeField(
        'Último Desvio Detectado em',
        null=True,
        blank=True
    )
    
    # 🆕 Controle de Paradas Prolongadas
    is_currently_stopped = models.BooleanField(
        'Veículo Parado Atualmente',
        default=False,
        help_text='Indica se o veículo está parado no momento (velocidade = 0)'
    )
    
    stopped_since = models.DateTimeField(
        'Parado Desde',
        null=True,
        blank=True,
        help_text='Data/hora em que o veículo parou (velocidade chegou a 0)'
    )
    
    last_stop_alert_at = models.DateTimeField(
        'Último Alerta de Parada em',
        null=True,
        blank=True,
        help_text='Data/hora do último alerta de parada prolongada'
    )
    
    alerts_data = models.JSONField(
        'Dados de Alertas',
        default=list,
        blank=True,
        help_text='Histórico de alertas gerados durante a viagem'
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
    
    def check_route_deviation(self, current_lat, current_lng):
        """
        Verifica se a posição atual está dentro da tolerância da rota planejada.
        
        Usa a geometria da rota (coordenadas reais das ruas) para calcular
        a distância mínima do veículo até a linha da rota.
        
        Args:
            current_lat: Latitude atual
            current_lng: Longitude atual
        
        Returns:
            dict: {
                'is_deviated': bool,
                'min_distance': float (metros),
                'tolerance': int (metros),
                'nearest_point': dict ou None
            }
        """
        if not self.route:
            logger.warning(f"{self.identifier}: Sem rota definida")
            return {
                'is_deviated': False,
                'min_distance': None,
                'tolerance': self.route_deviation_tolerance_meters,
                'nearest_point': None,
                'reason': 'Nenhuma rota definida'
            }
        
        # ✅ USAR GEOMETRIA DA ROTA (coordenadas reais das ruas)
        if self.route.route_geometry and self.route.route_geometry.get('coordinates'):
            # Geometria está no formato GeoJSON: [longitude, latitude]
            route_points = self.route.route_geometry['coordinates']
            
            logger.debug(
                f"{self.identifier}: Verificando desvio usando {len(route_points)} pontos da rota"
            )
            
            # Calcular distância mínima até qualquer segmento da rota
            min_distance = float('inf')
            nearest_point = None
            nearest_segment_idx = None
            
            for i in range(len(route_points)):
                # Converter de [lng, lat] para [lat, lng]
                point_lat = route_points[i][1]
                point_lng = route_points[i][0]
                
                # Distância até este ponto da rota
                distance = haversine_distance(
                    current_lat, current_lng,
                    point_lat, point_lng
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = {
                        'latitude': point_lat,
                        'longitude': point_lng,
                        'segment_index': i
                    }
                    nearest_segment_idx = i
            
            # Verificar se está fora da tolerância
            is_deviated = min_distance > self.route_deviation_tolerance_meters
            
            logger.info(
                f"{self.identifier}: Distância da rota: {min_distance:.1f}m "
                f"(tolerância: {self.route_deviation_tolerance_meters}m) - "
                f"{'DESVIADO' if is_deviated else 'OK'} - "
                f"Segmento mais próximo: {nearest_segment_idx}/{len(route_points)}"
            )
            
            return {
                'is_deviated': is_deviated,
                'min_distance': round(min_distance, 2),
                'tolerance': self.route_deviation_tolerance_meters,
                'nearest_point': nearest_point,
                'total_route_points': len(route_points)
            }
        
        # 🔄 FALLBACK: Se não tem geometria, usar apenas origem e destino
        logger.warning(
            f"{self.identifier}: Rota sem geometria, usando apenas origem/destino"
        )
        
        waypoints_to_check = []
        
        if self.route.origin_latitude and self.route.origin_longitude:
            waypoints_to_check.append({
                'name': self.route.origin_name or 'Origem',
                'lat': self.route.origin_latitude,
                'lng': self.route.origin_longitude,
            })
        
        if self.route.destination_latitude and self.route.destination_longitude:
            waypoints_to_check.append({
                'name': self.route.destination_name or 'Destino',
                'lat': self.route.destination_latitude,
                'lng': self.route.destination_longitude,
            })
        
        if not waypoints_to_check:
            logger.error(f"{self.identifier}: Rota sem coordenadas!")
            return {
                'is_deviated': False,
                'min_distance': None,
                'tolerance': self.route_deviation_tolerance_meters,
                'nearest_point': None,
                'reason': 'Rota sem coordenadas definidas'
            }
        
        # Calcular distância mínima até origem ou destino
        min_distance = float('inf')
        nearest_point = None
        
        for wp in waypoints_to_check:
            distance = haversine_distance(
                current_lat, current_lng,
                wp['lat'], wp['lng']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_point = {
                    'name': wp['name'],
                    'latitude': wp['lat'],
                    'longitude': wp['lng']
                }
        
        # Verificar se está fora da tolerância
        is_deviated = min_distance > self.route_deviation_tolerance_meters
        
        logger.warning(
            f"{self.identifier}: Usando fallback - Distância: {min_distance:.1f}m - "
            f"{'DESVIADO' if is_deviated else 'OK'}"
        )
        
        return {
            'is_deviated': is_deviated,
            'min_distance': round(min_distance, 2),
            'tolerance': self.route_deviation_tolerance_meters,
            'nearest_point': nearest_point
        }
    
    def add_alert(self, alert_type, severity, message, position_data=None):
        """
        Adiciona um alerta ao histórico de alertas da viagem.
        
        Args:
            alert_type: Tipo do alerta ('route_deviation', 'stop', 'speeding', etc)
            severity: Gravidade ('info', 'warning', 'critical')
            message: Mensagem descritiva
            position_data: Dados da posição quando o alerta foi gerado (opcional)
        """
        alert = {
            'timestamp': timezone.now().isoformat(),
            'type': alert_type,
            'severity': severity,
            'message': message,
            'position': position_data
        }
        
        if not isinstance(self.alerts_data, list):
            self.alerts_data = []
        
        self.alerts_data.append(alert)
        self.save(update_fields=['alerts_data'])
        
        logger.info(
            f"Alerta adicionado: {self.identifier} - "
            f"{alert_type} ({severity}): {message}"
        )
        
        return alert
    
    def analyze_current_position(self):
        """
        Analisa a posição atual do veículo e gera alertas se necessário.
        
        Verifica:
        - Desvio de rota
        - Velocidade excessiva
        - Parada não planejada
        
        Returns:
            dict: Resultado da análise com possíveis alertas
        """
        if self.status != 'EM_ANDAMENTO':
            return {
                'success': False,
                'reason': 'Viagem não está em andamento'
            }
        
        position = self.current_vehicle_position
        if not position:
            return {
                'success': False,
                'reason': 'Nenhuma posição disponível'
            }
        
        lat = position['latitude']
        lng = position['longitude']
        speed = position['speed'] or 0
        
        logger.info(
            f"{self.identifier}: Velocidade recebida: {position['speed']} → "
            f"Velocidade tratada: {speed} (tipo: {type(speed).__name__})"
        )
        
        alerts_generated = []
        
        # 1. Verificar desvio de rota
        deviation_check = self.check_route_deviation(lat, lng)
        
        if deviation_check['is_deviated']:
            # Gerar alerta se for um novo desvio OU se já passou tempo suficiente desde o último alerta
            should_alert = False
            alert_message = ""
            
            if not self.has_active_deviation:
                # Primeiro desvio
                should_alert = True
                alert_message = (
                    f"⚠️ Veículo desviou da rota! Distância: {deviation_check['min_distance']:.0f}m "
                    f"(tolerância: {deviation_check['tolerance']}m)"
                )
            else:
                # Já está desviado - gerar novo alerta a cada 2 minutos
                if self.last_deviation_detected_at:
                    minutes_since_last_alert = (timezone.now() - self.last_deviation_detected_at).total_seconds() / 60
                    logger.info(
                        f"{self.identifier}: Já desviado. Minutos desde último alerta: {minutes_since_last_alert:.1f}"
                    )
                    if minutes_since_last_alert >= 2:
                        should_alert = True
                        alert_message = (
                            f"⚠️ Veículo CONTINUA fora da rota há {int(minutes_since_last_alert)} minutos! "
                            f"Distância: {deviation_check['min_distance']:.0f}m "
                            f"(tolerância: {deviation_check['tolerance']}m)"
                        )
                        logger.info(
                            f"{self.identifier}: GERANDO ALERTA PERIÓDICO (>= 2 min)"
                        )
                    else:
                        logger.info(
                            f"{self.identifier}: Ainda não completou 2 min para próximo alerta "
                            f"(faltam {2 - minutes_since_last_alert:.1f} min)"
                        )
                else:
                    # Caso raro: tem desvio ativo mas sem timestamp
                    should_alert = True
                    alert_message = (
                        f"⚠️ Veículo continua fora da rota. Distância: {deviation_check['min_distance']:.0f}m "
                        f"(tolerância: {deviation_check['tolerance']}m)"
                    )
                    logger.warning(
                        f"{self.identifier}: Desvio ativo mas sem timestamp do último alerta"
                    )
            
            if should_alert:
                alert = self.add_alert(
                    alert_type='route_deviation',
                    severity='warning',
                    message=alert_message,
                    position_data={
                        'latitude': lat,
                        'longitude': lng,
                        'nearest_point': deviation_check.get('nearest_point'),
                        'distance': deviation_check['min_distance']
                    }
                )
                alerts_generated.append(alert)
                
                # Atualizar campos
                if not self.has_active_deviation:
                    self.total_route_deviations += 1
                
                self.has_active_deviation = True
                self.last_deviation_detected_at = timezone.now()
                self.save(update_fields=[
                    'has_active_deviation',
                    'last_deviation_detected_at',
                    'total_route_deviations'
                ])
        else:
            # Voltou para a rota
            if self.has_active_deviation:
                # Calcular quanto tempo ficou fora da rota
                time_off_route = ""
                if self.last_deviation_detected_at:
                    duration_minutes = (timezone.now() - self.last_deviation_detected_at).total_seconds() / 60
                    if duration_minutes < 60:
                        time_off_route = f" (ficou fora por {int(duration_minutes)} minutos)"
                    else:
                        hours = int(duration_minutes / 60)
                        mins = int(duration_minutes % 60)
                        time_off_route = f" (ficou fora por {hours}h{mins}min)"
                
                alert = self.add_alert(
                    alert_type='route_back',
                    severity='info',
                    message=f"✅ Veículo retornou à rota planejada{time_off_route}",
                    position_data={
                        'latitude': lat,
                        'longitude': lng
                    }
                )
                alerts_generated.append(alert)
                
                self.has_active_deviation = False
                self.save(update_fields=['has_active_deviation'])
        
        # 2. Atualizar velocidade máxima
        if speed > 0:
            if not self.max_speed_recorded or speed > float(self.max_speed_recorded):
                self.max_speed_recorded = speed
                self.save(update_fields=['max_speed_recorded'])
        
        # 3. 🆕 Detectar paradas prolongadas (velocidade = 0 por 5+ minutos)
        if speed == 0:
            # Veículo está parado
            if not self.is_currently_stopped:
                # Acabou de parar
                self.is_currently_stopped = True
                self.stopped_since = timezone.now()
                self.save(update_fields=['is_currently_stopped', 'stopped_since'])
                logger.info(f"{self.identifier}: Veículo parou às {self.stopped_since}")
            else:
                # Já estava parado - verificar se passou tempo suficiente para alertar
                if self.stopped_since:
                    minutes_stopped = (timezone.now() - self.stopped_since).total_seconds() / 60
                    
                    # Gerar alerta se parado por 5+ minutos
                    if minutes_stopped >= 5:
                        # Verificar se deve gerar novo alerta (a cada 5 minutos)
                        should_alert_stop = False
                        
                        if not self.last_stop_alert_at:
                            # Primeiro alerta de parada
                            should_alert_stop = True
                        else:
                            # Verificar se já passou 5 min desde o último alerta
                            minutes_since_last_stop_alert = (
                                timezone.now() - self.last_stop_alert_at
                            ).total_seconds() / 60
                            if minutes_since_last_stop_alert >= 5:
                                should_alert_stop = True
                        
                        if should_alert_stop:
                            alert = self.add_alert(
                                alert_type='prolonged_stop',
                                severity='warning',
                                message=(
                                    f"🛑 Veículo parado há {int(minutes_stopped)} minutos! "
                                    f"Local: {position.get('address', 'Desconhecido')}"
                                ),
                                position_data={
                                    'latitude': lat,
                                    'longitude': lng,
                                    'stopped_since': self.stopped_since.isoformat(),
                                    'minutes_stopped': int(minutes_stopped)
                                }
                            )
                            alerts_generated.append(alert)
                            
                            # Incrementar contador apenas no primeiro alerta desta parada
                            first_alert_of_this_stop = (self.last_stop_alert_at is None)
                            if first_alert_of_this_stop:
                                self.total_stops += 1
                            
                            self.last_stop_alert_at = timezone.now()
                            self.save(update_fields=['last_stop_alert_at', 'total_stops'])
                            
                            logger.warning(
                                f"{self.identifier}: ALERTA - Parado há {int(minutes_stopped)} minutos"
                            )
        else:
            # Veículo está em movimento
            if self.is_currently_stopped:
                # Estava parado e voltou a se mover
                duration_stopped = ""
                if self.stopped_since:
                    minutes_stopped = (timezone.now() - self.stopped_since).total_seconds() / 60
                    if minutes_stopped < 60:
                        duration_stopped = f" (ficou parado por {int(minutes_stopped)} minutos)"
                    else:
                        hours = int(minutes_stopped / 60)
                        mins = int(minutes_stopped % 60)
                        duration_stopped = f" (ficou parado por {hours}h{mins}min)"
                
                alert = self.add_alert(
                    alert_type='movement_resumed',
                    severity='info',
                    message=f"🚗 Veículo voltou a se mover{duration_stopped}",
                    position_data={
                        'latitude': lat,
                        'longitude': lng
                    }
                )
                alerts_generated.append(alert)
                
                self.is_currently_stopped = False
                self.stopped_since = None
                self.last_stop_alert_at = None
                self.save(update_fields=[
                    'is_currently_stopped',
                    'stopped_since',
                    'last_stop_alert_at'
                ])
                
                logger.info(f"{self.identifier}: Veículo voltou a se mover")
        
        return {
            'success': True,
            'position': position,
            'deviation_check': deviation_check,
            'alerts_generated': alerts_generated,
            'stats': {
                'has_active_deviation': self.has_active_deviation,
                'total_deviations': self.total_route_deviations,
                'max_speed': float(self.max_speed_recorded) if self.max_speed_recorded else 0,
                'is_currently_stopped': self.is_currently_stopped,
                'total_stops': self.total_stops
            }
        }
    
    def update_trip_statistics(self):
        """
        Atualiza estatísticas da viagem com base no histórico de posições.
        
        Calcula:
        - Distância total percorrida
        - Velocidade média
        - Total de paradas
        """
        positions = list(
            self.position_history.order_by('device_timestamp').values(
                'latitude', 'longitude', 'speed', 'device_timestamp'
            )
        )
        
        if len(positions) < 2:
            return
        
        # Calcular distância total
        total_distance_m = 0
        speeds = []
        stops = 0
        
        for i in range(1, len(positions)):
            prev = positions[i - 1]
            curr = positions[i]
            
            # Distância entre pontos consecutivos
            distance = haversine_distance(
                prev['latitude'], prev['longitude'],
                curr['latitude'], curr['longitude']
            )
            total_distance_m += distance
            
            # Coletar velocidades
            if curr['speed'] is not None:
                speeds.append(float(curr['speed']))
                
                # Detectar paradas
                if float(curr['speed']) == 0:
                    stops += 1
        
        # Atualizar campos
        self.total_distance_traveled = total_distance_m / 1000  # converter para km
        
        if speeds:
            self.average_speed = sum(speeds) / len(speeds)
        
        self.total_stops = stops
        
        self.save(update_fields=[
            'total_distance_traveled',
            'average_speed',
            'total_stops'
        ])
        
        logger.info(
            f"Estatísticas atualizadas: {self.identifier} - "
            f"{self.total_distance_traveled:.2f}km, "
            f"Vel.Média: {self.average_speed:.1f}km/h, "
            f"Paradas: {self.total_stops}"
        )
    
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
    
    # 🆕 Flag para posições de teste/simulação
    is_test_position = models.BooleanField(
        'Posição de Teste',
        default=False,
        help_text='Indica se esta é uma posição injetada para teste/simulação'
    )
    
    test_metadata = models.JSONField(
        'Metadados de Teste',
        blank=True,
        null=True,
        help_text='Informações sobre o teste (modo de simulação, origem, etc.)'
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
