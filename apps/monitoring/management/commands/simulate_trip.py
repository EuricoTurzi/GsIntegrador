"""
Comando para simular uma viagem com posições controladas.

Uso:
    python manage.py simulate_trip <trip_id> [--speed 60] [--interval 5] [--mode route|circle|random]
    
Exemplos:
    # Simular seguindo a rota planejada
    python manage.py simulate_trip 1 --speed 60 --interval 5
    
    # Simular em círculo (para testar desvios)
    python manage.py simulate_trip 1 --mode circle --speed 40
    
    # Simular posições aleatórias
    python manage.py simulate_trip 1 --mode random --speed 50
"""

import time
import math
import random
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from apps.monitoring.models import MonitoringSystem
from apps.devices.models import Device


class Command(BaseCommand):
    help = 'Simula uma viagem com posições controladas para teste'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'trip_id',
            type=int,
            help='ID da viagem (MonitoringSystem) a simular'
        )
        
        parser.add_argument(
            '--speed',
            type=float,
            default=60.0,
            help='Velocidade simulada em km/h (padrão: 60)'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Intervalo entre atualizações em segundos (padrão: 5)'
        )
        
        parser.add_argument(
            '--mode',
            type=str,
            default='route',
            choices=['route', 'circle', 'random', 'static'],
            help='Modo de simulação: route (segue rota), circle (círculo), random (aleatório), static (parado)'
        )
        
        parser.add_argument(
            '--duration',
            type=int,
            default=300,
            help='Duração da simulação em segundos (padrão: 300 = 5 minutos)'
        )
        
        parser.add_argument(
            '--inject-old-position',
            action='store_true',
            help='Injetar uma posição antiga no meio da simulação (para testar validação)'
        )
    
    def handle(self, *args, **options):
        trip_id = options['trip_id']
        speed = options['speed']
        interval = options['interval']
        mode = options['mode']
        duration = options['duration']
        inject_old = options['inject_old_position']
        
        # Buscar viagem
        try:
            trip = MonitoringSystem.objects.select_related(
                'vehicle', 'vehicle__device', 'route'
            ).get(id=trip_id)
        except MonitoringSystem.DoesNotExist:
            raise CommandError(f'Viagem com ID {trip_id} não encontrada')
        
        # Verificar se tem dispositivo
        if not hasattr(trip.vehicle, 'device'):
            raise CommandError(f'Veículo {trip.vehicle.placa} não possui dispositivo rastreador')
        
        device = trip.vehicle.device
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🚗 Iniciando simulação de viagem:\n'
                f'   Trip: {trip.identifier} - {trip.name}\n'
                f'   Veículo: {trip.vehicle.placa}\n'
                f'   Device: {device.suntech_device_id}\n'
                f'   Modo: {mode}\n'
                f'   Velocidade: {speed} km/h\n'
                f'   Intervalo: {interval}s\n'
                f'   Duração: {duration}s ({duration/60:.1f} min)\n'
            )
        )
        
        # Inicializar simulação baseado no modo
        if mode == 'route':
            positions = self._generate_route_positions(trip, speed, interval, duration)
        elif mode == 'circle':
            positions = self._generate_circle_positions(trip, speed, interval, duration)
        elif mode == 'random':
            positions = self._generate_random_positions(trip, speed, interval, duration)
        elif mode == 'static':
            positions = self._generate_static_positions(trip, speed, interval, duration)
        
        self.stdout.write(f'\n📍 Total de posições a simular: {len(positions)}\n')
        
        # Executar simulação
        start_time = time.time()
        old_position_injected = False
        
        for i, pos_data in enumerate(positions, 1):
            # Injetar posição antiga no meio (se solicitado)
            if inject_old and not old_position_injected and i == len(positions) // 2:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠️  [TESTE] Injetando posição ANTIGA (timestamp de 10 minutos atrás)...'
                    )
                )
                
                old_timestamp = timezone.now() - timezone.timedelta(minutes=10)
                
                # Tentar atualizar com posição antiga
                device.last_latitude = Decimal(str(round(pos_data['latitude'], 7)))
                device.last_longitude = Decimal(str(round(pos_data['longitude'], 7)))
                device.last_speed = Decimal(str(pos_data['speed']))
                device.last_system_date = old_timestamp
                device.last_address = f"[TESTE POSIÇÃO ANTIGA] {pos_data['address']}"
                
                try:
                    device.save()
                    self.stdout.write(
                        self.style.ERROR(
                            f'   ❌ FALHOU: Posição antiga foi ACEITA (BUG!)\n'
                            f'   Timestamp: {old_timestamp.isoformat()}'
                        )
                    )
                except ValidationError as e:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'   ✅ SUCESSO: Posição antiga foi REJEITADA pelo sistema!\n'
                            f'   Timestamp tentado: {old_timestamp.isoformat()}\n'
                            f'   Erro: {str(e)}'
                        )
                    )
                
                old_position_injected = True
                time.sleep(2)
                continue
            
            # Atualizar device com nova posição
            device.last_latitude = Decimal(str(round(pos_data['latitude'], 7)))
            device.last_longitude = Decimal(str(round(pos_data['longitude'], 7)))
            device.last_speed = Decimal(str(pos_data['speed']))
            device.last_system_date = timezone.now()
            device.last_address = pos_data['address']
            
            try:
                device.save()
            except ValidationError as e:
                # Timestamp conflict - pular esta posição
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠️  Posição {i}/{len(positions)} rejeitada (timestamp conflict): {e}'
                    )
                )
                continue
            
            # Exibir progresso
            elapsed = time.time() - start_time
            progress = (i / len(positions)) * 100
            
            self.stdout.write(
                f'\r[{progress:5.1f}%] Posição {i}/{len(positions)} | '
                f'Lat: {pos_data["latitude"]:.6f}, Lng: {pos_data["longitude"]:.6f} | '
                f'Speed: {pos_data["speed"]:.1f} km/h | '
                f'Elapsed: {elapsed:.0f}s',
                ending=''
            )
            self.stdout.flush()
            
            # Aguardar intervalo
            if i < len(positions):
                time.sleep(interval)
        
        total_time = time.time() - start_time
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n\n✅ Simulação concluída!\n'
                f'   Total de posições: {len(positions)}\n'
                f'   Tempo total: {total_time:.1f}s ({total_time/60:.1f} min)\n'
                f'   Velocidade média: {speed:.1f} km/h\n'
            )
        )
        
        # Exibir estatísticas da viagem
        trip.refresh_from_db()
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Estatísticas da viagem:\n'
                f'   Desvios de rota: {trip.total_route_deviations}\n'
                f'   Paradas detectadas: {trip.total_stops}\n'
                f'   Desvio ativo: {"Sim" if trip.has_active_deviation else "Não"}\n'
                f'   Parado atualmente: {"Sim" if trip.is_currently_stopped else "Não"}\n'
            )
        )
    
    def _generate_route_positions(self, trip, speed, interval, duration):
        """Gera posições seguindo a rota planejada."""
        positions = []
        
        if not trip.route.route_geometry or not trip.route.route_geometry.get('coordinates'):
            self.stdout.write(
                self.style.WARNING('Rota sem geometria, usando apenas origem/destino')
            )
            return self._generate_simple_route(trip, speed, interval, duration)
        
        route_coords = trip.route.route_geometry['coordinates']
        num_updates = duration // interval
        
        # Distribuir posições ao longo da rota
        for i in range(num_updates):
            progress = i / num_updates
            idx = int(progress * (len(route_coords) - 1))
            
            coord = route_coords[idx]
            
            positions.append({
                'latitude': round(coord[1], 7),  # GeoJSON é [lng, lat], max 7 decimais
                'longitude': round(coord[0], 7),
                'speed': speed if i > 0 else 0,  # Começa parado
                'address': f'Simulação - ponto {i+1}/{num_updates} da rota'
            })
        
        return positions
    
    def _generate_simple_route(self, trip, speed, interval, duration):
        """Gera posições simples entre origem e destino."""
        positions = []
        num_updates = duration // interval
        
        start_lat = float(trip.route.origin_latitude)
        start_lng = float(trip.route.origin_longitude)
        end_lat = float(trip.route.destination_latitude)
        end_lng = float(trip.route.destination_longitude)
        
        for i in range(num_updates):
            progress = i / num_updates
            
            lat = start_lat + (end_lat - start_lat) * progress
            lng = start_lng + (end_lng - start_lng) * progress
            
            positions.append({
                'latitude': round(lat, 7),
                'longitude': round(lng, 7),
                'speed': speed,
                'address': f'Simulação - {progress*100:.0f}% do percurso'
            })
        
        return positions
    
    def _generate_circle_positions(self, trip, speed, interval, duration):
        """Gera posições em círculo (para testar desvios)."""
        positions = []
        num_updates = duration // interval
        
        # Centro no ponto inicial da rota
        if trip.route.route_geometry and trip.route.route_geometry.get('coordinates'):
            center_coord = trip.route.route_geometry['coordinates'][0]
            center_lat = center_coord[1]
            center_lng = center_coord[0]
        else:
            center_lat = float(trip.route.origin_latitude)
            center_lng = float(trip.route.origin_longitude)
        
        # Raio de ~500m (para garantir desvio)
        radius_degrees = 0.005  # ~500m
        
        for i in range(num_updates):
            angle = (i / num_updates) * 2 * math.pi
            
            lat = center_lat + radius_degrees * math.sin(angle)
            lng = center_lng + radius_degrees * math.cos(angle)
            
            positions.append({
                'latitude': round(lat, 7),
                'longitude': round(lng, 7),
                'speed': speed,
                'address': f'Simulação - círculo {i+1}/{num_updates}'
            })
        
        return positions
    
    def _generate_random_positions(self, trip, speed, interval, duration):
        """Gera posições aleatórias próximas à rota."""
        positions = []
        num_updates = duration // interval
        
        # Centro na origem da rota
        if trip.route.route_geometry and trip.route.route_geometry.get('coordinates'):
            center_coord = trip.route.route_geometry['coordinates'][0]
            center_lat = center_coord[1]
            center_lng = center_coord[0]
        else:
            center_lat = float(trip.route.origin_latitude)
            center_lng = float(trip.route.origin_longitude)
        
        for i in range(num_updates):
            # Offset aleatório de até 1km
            offset_lat = random.uniform(-0.01, 0.01)
            offset_lng = random.uniform(-0.01, 0.01)
            
            positions.append({
                'latitude': round(center_lat + offset_lat, 7),
                'longitude': round(center_lng + offset_lng, 7),
                'speed': random.uniform(speed * 0.8, speed * 1.2),
                'address': f'Simulação - posição aleatória {i+1}/{num_updates}'
            })
        
        return positions
    
    def _generate_static_positions(self, trip, speed, interval, duration):
        """Gera posições estáticas (veículo parado - para testar alertas de parada)."""
        positions = []
        num_updates = duration // interval
        
        # Posição fixa na origem
        if trip.route.route_geometry and trip.route.route_geometry.get('coordinates'):
            coord = trip.route.route_geometry['coordinates'][0]
            lat = coord[1]
            lng = coord[0]
        else:
            lat = float(trip.route.origin_latitude)
            lng = float(trip.route.origin_longitude)
        
        for i in range(num_updates):
            positions.append({
                'latitude': round(lat, 7),
                'longitude': round(lng, 7),
                'speed': 0,  # Parado
                'address': f'Simulação - parado {i+1}/{num_updates}'
            })
        
        return positions

