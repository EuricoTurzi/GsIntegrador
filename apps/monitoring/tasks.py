"""
Tasks Celery para monitoramento.
"""
from celery import shared_task
import logging
from django.utils import timezone
from .models import MonitoringSystem

logger = logging.getLogger(__name__)


@shared_task(name='monitoring.check_device_status')
def check_monitoring_device_status():
    """
    Task para verificar status dos dispositivos em monitoramentos ativos.
    
    Verifica todos os SMs em andamento e alerta se algum dispositivo
    está desatualizado.
    """
    try:
        logger.info("Verificando status de dispositivos em monitoramentos ativos...")
        
        sms = MonitoringSystem.objects.filter(
            status='EM_ANDAMENTO',
            is_active=True
        ).select_related('vehicle')
        
        outdated_devices = []
        
        for sm in sms:
            if not sm.device_status:
                outdated_devices.append({
                    'sm_id': sm.id,
                    'identifier': sm.identifier,
                    'vehicle_placa': sm.vehicle.placa,
                    'driver_nome': sm.driver.nome,
                    'route_name': sm.route.name,
                    'minutes_since_update': sm.vehicle.device.minutes_since_last_update if hasattr(sm.vehicle, 'device') else None
                })
        
        logger.info(
            f"Verificação concluída: {len(outdated_devices)} "
            f"monitoramento(s) com dispositivo desatualizado"
        )
        
        return {
            'success': True,
            'total_active': sms.count(),
            'outdated_count': len(outdated_devices),
            'outdated_devices': outdated_devices
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar status de dispositivos: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='monitoring.auto_complete_overdue')
def auto_complete_overdue_monitoring():
    """
    Task para finalizar automaticamente monitoramentos com prazo vencido.
    
    Finaliza SMs que estão em andamento mas já passaram da data
    planejada de término.
    """
    try:
        logger.info("Verificando monitoramentos com prazo vencido...")
        
        now = timezone.now()
        overdue_sms = MonitoringSystem.objects.filter(
            status='EM_ANDAMENTO',
            planned_end_date__lt=now,
            is_active=True
        )
        
        completed_count = 0
        completed_list = []
        
        for sm in overdue_sms:
            sm.complete_monitoring()
            completed_count += 1
            completed_list.append({
                'sm_id': sm.id,
                'identifier': sm.identifier,
                'planned_end': str(sm.planned_end_date),
                'actual_end': str(sm.actual_end_date)
            })
        
        logger.info(f"Finalizados {completed_count} monitoramento(s) com prazo vencido")
        
        return {
            'success': True,
            'completed_count': completed_count,
            'completed_list': completed_list
        }
        
    except Exception as e:
        logger.error(f"Erro ao finalizar monitoramentos vencidos: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='monitoring.generate_monitoring_report')
def generate_monitoring_report(sm_id: int):
    """
    Task para gerar relatório de um monitoramento específico.
    
    Args:
        sm_id: ID do Sistema de Monitoramento
    """
    try:
        sm = MonitoringSystem.objects.get(id=sm_id)
        
        logger.info(f"Gerando relatório do SM {sm.identifier}...")
        
        report = {
            'identifier': sm.identifier,
            'name': sm.name,
            'status': sm.status,
            'transportadora': sm.transportadora.company_name,
            'route': {
                'name': sm.route.name,
                'origin': sm.route.origin_name,
                'destination': sm.route.destination_name,
                'distance_km': sm.route.distance_km
            },
            'driver': {
                'nome': sm.driver.nome,
                'cpf': sm.driver.cpf,
                'cnh': sm.driver.cnh
            },
            'vehicle': {
                'placa': sm.vehicle.placa,
                'modelo': sm.vehicle.modelo,
                'ano': sm.vehicle.ano
            },
            'dates': {
                'planned_start': str(sm.planned_start_date),
                'planned_end': str(sm.planned_end_date),
                'actual_start': str(sm.actual_start_date) if sm.actual_start_date else None,
                'actual_end': str(sm.actual_end_date) if sm.actual_end_date else None,
                'duration_days': sm.duration_days
            },
            'device': {
                'was_validated': sm.device_was_updated,
                'validated_at': str(sm.device_validated_at),
                'current_status': sm.device_status
            },
            'cargo': {
                'description': sm.cargo_description,
                'value': float(sm.cargo_value) if sm.cargo_value else None
            }
        }
        
        logger.info(f"Relatório do SM {sm.identifier} gerado com sucesso")
        
        return {
            'success': True,
            'sm_id': sm_id,
            'report': report
        }
        
    except MonitoringSystem.DoesNotExist:
        logger.error(f"SM {sm_id} não encontrado")
        return {
            'success': False,
            'sm_id': sm_id,
            'error': 'Monitoramento não encontrado'
        }
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório do SM {sm_id}: {str(e)}")
        return {
            'success': False,
            'sm_id': sm_id,
            'error': str(e)
        }


@shared_task(name='monitoring.notify_upcoming_departures')
def notify_upcoming_departures():
    """
    Task para notificar sobre monitoramentos que vão começar em breve.
    
    Retorna lista de SMs planejados que começam nas próximas 24 horas.
    """
    try:
        logger.info("Verificando partidas próximas...")
        
        now = timezone.now()
        next_24h = now + timezone.timedelta(hours=24)
        
        upcoming_sms = MonitoringSystem.objects.filter(
            status='PLANEJADO',
            planned_start_date__gte=now,
            planned_start_date__lte=next_24h,
            is_active=True
        )
        
        upcoming_list = []
        
        for sm in upcoming_sms:
            hours_until_start = (sm.planned_start_date - now).total_seconds() / 3600
            
            upcoming_list.append({
                'sm_id': sm.id,
                'identifier': sm.identifier,
                'name': sm.name,
                'driver': sm.driver.nome,
                'vehicle': sm.vehicle.placa,
                'route': sm.route.name,
                'planned_start': str(sm.planned_start_date),
                'hours_until_start': round(hours_until_start, 1)
            })
        
        logger.info(f"Encontrados {len(upcoming_list)} monitoramento(s) com partida próxima")
        
        return {
            'success': True,
            'upcoming_count': len(upcoming_list),
            'upcoming_list': upcoming_list
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar partidas próximas: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='monitoring.broadcast_fleet_positions')
def broadcast_fleet_positions():
    """
    Busca posições de todas viagens ativas e envia via WebSocket
    Task executada periodicamente (a cada 30 segundos)
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        # Buscar todas viagens ativas
        trips = MonitoringSystem.objects.filter(
            status='EM_ANDAMENTO'
        ).select_related('vehicle', 'vehicle__device', 'driver', 'route', 'transportadora')
        
        positions_by_transportadora = {}
        all_positions = []
        
        for trip in trips:
            position = trip.current_vehicle_position
            if position:
                # 🆕 SALVAR POSIÇÃO NO HISTÓRICO
                trip.save_position_snapshot()
                
                position_data = {
                    'trip_id': trip.id,
                    'identifier': trip.identifier,
                    'name': trip.name,
                    'status': trip.status,
                    'latitude': position['latitude'],
                    'longitude': position['longitude'],
                    'speed': position['speed'],
                    'address': position['address'],
                    'last_update': position['last_update'].isoformat() if position['last_update'] else None,
                    'driver': trip.driver.nome,
                    'vehicle': trip.vehicle.placa,
                    'device_status': trip.device_status,  # 🆕 Status atualização
                }
                
                # Adicionar às posições gerais
                all_positions.append(position_data)
                
                # Agrupar por transportadora
                transp_id = trip.transportadora_id
                if transp_id not in positions_by_transportadora:
                    positions_by_transportadora[transp_id] = []
                positions_by_transportadora[transp_id].append(position_data)
                
                # Enviar atualização individual para o grupo da viagem específica
                async_to_sync(channel_layer.group_send)(
                    f'trip_{trip.id}',
                    {
                        'type': 'position_update',
                        'data': position_data
                    }
                )
        
        # Enviar atualização para o grupo geral (GR/Admin)
        if all_positions:
            async_to_sync(channel_layer.group_send)(
                'fleet_all',
                {
                    'type': 'fleet_update',
                    'data': all_positions
                }
            )
        
        # Enviar atualizações por transportadora
        for transp_id, positions in positions_by_transportadora.items():
            async_to_sync(channel_layer.group_send)(
                f'fleet_transportadora_{transp_id}',
                {
                    'type': 'fleet_update',
                    'data': positions
                }
            )
        
        logger.info(f"Broadcast de {len(all_positions)} posições enviado")
        
        return {
            'success': True,
            'positions_sent': len(all_positions),
            'transportadoras': len(positions_by_transportadora)
        }
        
    except Exception as e:
        logger.error(f"Erro ao fazer broadcast de posições: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='monitoring.notify_device_sync')
def notify_device_sync(device_id, monitoring_system_id=None):
    """
    Notifica via WebSocket quando um dispositivo é sincronizado.
    
    Args:
        device_id: ID do dispositivo que foi sincronizado
        monitoring_system_id: ID do SM associado (opcional)
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from apps.devices.models import Device
        
        channel_layer = get_channel_layer()
        device = Device.objects.get(id=device_id)
        
        sync_data = {
            'type': 'device_sync',
            'device_id': device.id,
            'identifier': device.identifier,
            'last_update': device.last_system_date.isoformat() if device.last_system_date else None,
            'is_updated': device.is_updated_recently,
            'latitude': float(device.last_latitude) if device.last_latitude else None,
            'longitude': float(device.last_longitude) if device.last_longitude else None,
            'address': device.last_address,
            'speed': float(device.last_speed) if device.last_speed else None,
        }
        
        # Se tem SM associado, enviar para o grupo específico
        if monitoring_system_id:
            async_to_sync(channel_layer.group_send)(
                f'trip_{monitoring_system_id}',
                {
                    'type': 'device_sync_update',
                    'data': sync_data
                }
            )
        
        # Enviar para grupos de fleet (para atualizar dashboards)
        if hasattr(device, 'vehicle') and device.vehicle:
            vehicle = device.vehicle
            if vehicle.transportadora_id:
                async_to_sync(channel_layer.group_send)(
                    f'fleet_transportadora_{vehicle.transportadora_id}',
                    {
                        'type': 'device_sync_update',
                        'data': sync_data
                    }
                )
        
        logger.info(f"Notificação de sincronização enviada: Device {device.identifier}")
        return {'success': True, 'device': device.identifier}
        
    except Exception as e:
        logger.error(f"Erro ao notificar sincronização: {str(e)}")
        return {'success': False, 'error': str(e)}
