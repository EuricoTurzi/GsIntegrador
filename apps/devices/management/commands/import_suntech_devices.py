"""
Comando de gerenciamento para importar dispositivos da API Suntech.
Uso: python manage.py import_suntech_devices
"""
from django.core.management.base import BaseCommand
from apps.devices.models import Device
from apps.integrations.suntech_client import suntech_client, SuntechAPIError


class Command(BaseCommand):
    help = 'Importa dispositivos da API Suntech e cria registros no banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Atualiza dispositivos existentes com novos dados',
        )

    def handle(self, *args, **options):
        update_existing = options['update']
        
        self.stdout.write(self.style.WARNING('Conectando à API Suntech...'))
        
        try:
            # Buscar todos os dispositivos da API
            vehicles_data = suntech_client.get_client_vehicles(use_cache=False)
            
            if not vehicles_data:
                self.stdout.write(self.style.ERROR('Nenhum dispositivo encontrado na API Suntech!'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'✓ Encontrados {len(vehicles_data)} dispositivos na API Suntech'))
            
            created = 0
            updated = 0
            skipped = 0
            
            for vehicle in vehicles_data:
                device_id = vehicle.get('deviceId')
                imei = vehicle.get('imei')
                label = vehicle.get('label', '')
                
                if not device_id or not imei:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Dispositivo sem ID ou IMEI, pulando...'))
                    skipped += 1
                    continue
                
                # Verificar se já existe
                device = Device.objects.filter(suntech_device_id=device_id).first()
                
                if device:
                    if update_existing:
                        # Atualizar dados existentes
                        device.imei = imei
                        device.label = label or device.label
                        device.last_latitude = vehicle.get('latitude')
                        device.last_longitude = vehicle.get('longitude')
                        device.last_speed = vehicle.get('speed', 0)
                        device.last_ignition_status = vehicle.get('ignition', False)
                        
                        # Parsear datas
                        from django.utils import timezone
                        from datetime import datetime
                        
                        position_date_str = vehicle.get('date')
                        if position_date_str:
                            try:
                                device.last_position_date = timezone.make_aware(
                                    datetime.strptime(position_date_str, '%Y-%m-%d %H:%M:%S')
                                )
                            except ValueError:
                                pass
                        
                        system_date_str = vehicle.get('systemDate')
                        if system_date_str:
                            try:
                                device.last_system_date = timezone.make_aware(
                                    datetime.strptime(system_date_str, '%Y-%m-%d %H:%M:%S')
                                )
                            except ValueError:
                                pass
                        
                        device.save()
                        updated += 1
                        self.stdout.write(f'  ↻ Atualizado: {device.identifier} (ID: {device_id})')
                    else:
                        skipped += 1
                        self.stdout.write(f'  - Já existe: {device.identifier} (ID: {device_id})')
                else:
                    # Criar novo dispositivo
                    identifier = label or f'DEVICE-{device_id}'
                    
                    device = Device.objects.create(
                        identifier=identifier,
                        imei=imei,
                        label=label,
                        suntech_device_id=str(device_id),
                        suntech_vehicle_id=str(vehicle.get('vehicleId', '')),
                        last_latitude=vehicle.get('latitude'),
                        last_longitude=vehicle.get('longitude'),
                        last_speed=vehicle.get('speed', 0),
                        last_ignition_status=vehicle.get('ignition', False),
                        is_active=True,
                    )
                    
                    # Parsear datas
                    from django.utils import timezone
                    from datetime import datetime
                    
                    position_date_str = vehicle.get('date')
                    if position_date_str:
                        try:
                            device.last_position_date = timezone.make_aware(
                                datetime.strptime(position_date_str, '%Y-%m-%d %H:%M:%S')
                            )
                        except ValueError:
                            pass
                    
                    system_date_str = vehicle.get('systemDate')
                    if system_date_str:
                        try:
                            device.last_system_date = timezone.make_aware(
                                datetime.strptime(system_date_str, '%Y-%m-%d %H:%M:%S')
                            )
                        except ValueError:
                            pass
                    
                    device.save()
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f'  + Criado: {device.identifier} (ID: {device_id})'))
            
            # Resumo
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 50))
            self.stdout.write(self.style.SUCCESS(f'✓ Importação concluída!'))
            self.stdout.write(f'  • Criados: {created}')
            self.stdout.write(f'  • Atualizados: {updated}')
            self.stdout.write(f'  • Pulados: {skipped}')
            self.stdout.write(self.style.SUCCESS('=' * 50))
            
            # Limpar cache
            suntech_client.clear_cache()
            
        except SuntechAPIError as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro da API Suntech: {str(e)}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro inesperado: {str(e)}'))
