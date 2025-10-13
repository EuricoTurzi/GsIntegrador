"""
Modelo de Rotas.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.authentication.models import User


class Route(models.Model):
    """
    Modelo representando uma rota entre dois pontos.
    """
    
    # Relacionamento
    transportadora = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='routes',
        limit_choices_to={'user_type': 'TRANSPORTADORA'},
        verbose_name='Transportadora'
    )
    
    # Identificação da rota
    name = models.CharField(
        'Nome da Rota',
        max_length=200,
        help_text='Nome descritivo da rota (ex: São Paulo - Rio de Janeiro)'
    )
    
    description = models.TextField(
        'Descrição',
        blank=True,
        null=True,
        help_text='Detalhes adicionais sobre a rota'
    )
    
    # Ponto A (Origem)
    origin_name = models.CharField(
        'Nome Origem',
        max_length=200,
        help_text='Nome do local de origem'
    )
    
    origin_address = models.TextField(
        'Endereço Origem',
        help_text='Endereço completo do ponto de origem'
    )
    
    origin_latitude = models.DecimalField(
        'Latitude Origem',
        max_digits=10,
        decimal_places=7,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90)
        ]
    )
    
    origin_longitude = models.DecimalField(
        'Longitude Origem',
        max_digits=10,
        decimal_places=7,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180)
        ]
    )
    
    # Ponto B (Destino)
    destination_name = models.CharField(
        'Nome Destino',
        max_length=200,
        help_text='Nome do local de destino'
    )
    
    destination_address = models.TextField(
        'Endereço Destino',
        help_text='Endereço completo do ponto de destino'
    )
    
    destination_latitude = models.DecimalField(
        'Latitude Destino',
        max_digits=10,
        decimal_places=7,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90)
        ]
    )
    
    destination_longitude = models.DecimalField(
        'Longitude Destino',
        max_digits=10,
        decimal_places=7,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180)
        ]
    )
    
    # Dados calculados da rota
    distance_meters = models.IntegerField(
        'Distância (metros)',
        blank=True,
        null=True,
        help_text='Distância calculada pelo OpenStreetMap'
    )
    
    estimated_duration_seconds = models.IntegerField(
        'Duração Estimada (segundos)',
        blank=True,
        null=True,
        help_text='Tempo estimado de viagem calculado pelo OpenStreetMap'
    )
    
    route_geometry = models.JSONField(
        'Geometria da Rota',
        blank=True,
        null=True,
        help_text='Coordenadas da rota em formato GeoJSON'
    )
    
    # Controle
    is_active = models.BooleanField('Ativa', default=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criada em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizada em', auto_now=True)
    last_calculated_at = models.DateTimeField(
        'Última Calculo',
        blank=True,
        null=True,
        help_text='Data do último cálculo da rota'
    )
    
    class Meta:
        verbose_name = 'Rota'
        verbose_name_plural = 'Rotas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transportadora', 'is_active']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.origin_name} → {self.destination_name})"
    
    @property
    def distance_km(self):
        """Retorna a distância em quilômetros."""
        if self.distance_meters:
            return round(self.distance_meters / 1000, 2)
        return None
    
    @property
    def estimated_duration_hours(self):
        """Retorna a duração estimada em horas."""
        if self.estimated_duration_seconds:
            return round(self.estimated_duration_seconds / 3600, 2)
        return None
    
    @property
    def estimated_duration_formatted(self):
        """Retorna a duração formatada (HH:MM)."""
        if self.estimated_duration_seconds:
            hours = self.estimated_duration_seconds // 3600
            minutes = (self.estimated_duration_seconds % 3600) // 60
            return f"{hours:02d}:{minutes:02d}"
        return None
    
    @property
    def origin_coordinates(self):
        """Retorna as coordenadas de origem como tupla (lat, lon)."""
        return (float(self.origin_latitude), float(self.origin_longitude))
    
    @property
    def destination_coordinates(self):
        """Retorna as coordenadas de destino como tupla (lat, lon)."""
        return (float(self.destination_latitude), float(self.destination_longitude))
    
    def calculate_route(self):
        """
        Calcula a rota usando OpenStreetMap/OSRM.
        
        Returns:
            bool: True se o cálculo foi bem-sucedido
        """
        from .osm_service import calculate_route_osm
        from django.utils import timezone
        
        try:
            result = calculate_route_osm(
                self.origin_coordinates,
                self.destination_coordinates
            )
            
            if result:
                self.distance_meters = result.get('distance')
                self.estimated_duration_seconds = result.get('duration')
                self.route_geometry = result.get('geometry')
                self.last_calculated_at = timezone.now()
                self.save()
                return True
            
            return False
            
        except Exception:
            return False
    
    def clean(self):
        """Validações personalizadas."""
        super().clean()
        
        # Validar que origem e destino são diferentes
        if (self.origin_latitude == self.destination_latitude and
            self.origin_longitude == self.destination_longitude):
            raise ValidationError(
                'Origem e destino devem ser diferentes.'
            )
    
    def save(self, *args, **kwargs):
        """Sobrescreve o save para validar antes de salvar."""
        self.full_clean()
        super().save(*args, **kwargs)
