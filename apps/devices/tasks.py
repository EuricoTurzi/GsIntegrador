"""
Tasks Celery para dispositivos.
"""
from celery import shared_task
import logging
from .models import Device
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@shared_task(name='devices.sync_all_devices')
def sync_all_devices():
    """
    Task para sincronizar todos os dispositivos com a API Suntech.
    
    Esta task pode ser agendada para executar periodicamente.
    """
    try:
        logger.info("Iniciando sincronização de todos os dispositivos...")
        
        devices = Device.objects.filter(is_active=True)
        success_count = 0
        error_count = 0
        
        for device in devices:
            if device.sync_with_suntech():
                success_count += 1
                logger.debug(f"Dispositivo {device.suntech_device_id} sincronizado")
                
                # Recarrega do banco para garantir dados atualizados
                device.refresh_from_db()
                
                # 🆕 NOTIFICAR VIA WEBSOCKET - DASHBOARD DE DEVICES
                try:
                    # Chama direto (sem .delay) para garantir que execute após o commit
                    notify_device_sync_dashboard(device.id)
                except Exception as notify_error:
                    logger.warning(f"Erro ao notificar dashboard: {notify_error}")
                
                # 🆕 NOTIFICAR VIA WEBSOCKET SE TEM VIAGEM ATIVA
                try:
                    if hasattr(device, 'vehicle') and device.vehicle:
                        # Verificar se o veículo está em uma viagem ativa
                        from apps.monitoring.models import MonitoringSystem
                        active_trip = MonitoringSystem.objects.filter(
                            vehicle=device.vehicle,
                            status='EM_ANDAMENTO'
                        ).first()
                        
                        if active_trip:
                            from apps.monitoring.tasks import notify_device_sync
                            notify_device_sync.delay(device.id, active_trip.id)
                except Exception as notify_error:
                    logger.warning(f"Erro ao notificar viagem: {notify_error}")
            else:
                error_count += 1
                logger.warning(f"Erro ao sincronizar dispositivo {device.suntech_device_id}")
        
        logger.info(
            f"Sincronização concluída: "
            f"{success_count} sucesso, {error_count} erros"
        )
        
        return {
            'success': True,
            'total': devices.count(),
            'synced': success_count,
            'errors': error_count
        }
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar dispositivos: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='devices.check_outdated_devices')
def check_outdated_devices():
    """
    Task para verificar dispositivos desatualizados.
    
    Retorna lista de dispositivos que não foram atualizados
    nos últimos 30 minutos.
    """
    try:
        logger.info("Verificando dispositivos desatualizados...")
        
        devices = Device.objects.filter(is_active=True)
        outdated_devices = []
        
        for device in devices:
            if not device.is_updated_recently:
                outdated_devices.append({
                    'device_id': device.id,
                    'suntech_device_id': device.suntech_device_id,
                    'vehicle_placa': device.vehicle.placa,
                    'minutes_since_update': device.minutes_since_last_update,
                    'last_system_date': str(device.last_system_date)
                })
        
        logger.info(f"Encontrados {len(outdated_devices)} dispositivos desatualizados")
        
        return {
            'success': True,
            'total_devices': devices.count(),
            'outdated_count': len(outdated_devices),
            'outdated_devices': outdated_devices
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar dispositivos desatualizados: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='devices.sync_device_by_id')
def sync_device_by_id(device_id: int):
    """
    Task para sincronizar um dispositivo específico.
    
    Args:
        device_id: ID do dispositivo no banco de dados
    """
    try:
        device = Device.objects.get(id=device_id)
        
        logger.info(f"Sincronizando dispositivo {device.suntech_device_id}...")
        
        if device.sync_with_suntech():
            logger.info(f"Dispositivo {device.suntech_device_id} sincronizado com sucesso")
            return {
                'success': True,
                'device_id': device_id,
                'suntech_device_id': device.suntech_device_id
            }
        else:
            logger.error(f"Erro ao sincronizar dispositivo {device.suntech_device_id}")
            return {
                'success': False,
                'device_id': device_id,
                'error': 'Falha na sincronização'
            }
        
    except Device.DoesNotExist:
        logger.error(f"Dispositivo {device_id} não encontrado")
        return {
            'success': False,
            'device_id': device_id,
            'error': 'Dispositivo não encontrado'
        }
    
    except Exception as e:
        logger.error(f"Erro ao sincronizar dispositivo {device_id}: {str(e)}")
        return {
            'success': False,
            'device_id': device_id,
            'error': str(e)
        }


@shared_task(name='devices.notify_device_sync_dashboard')
def notify_device_sync_dashboard(device_id: int):
    """
    Task para notificar o dashboard de devices via WebSocket após sincronização.
    
    Args:
        device_id: ID do dispositivo sincronizado
    """
    try:
        device = Device.objects.get(id=device_id)
        
        # Força reload do banco para garantir dados mais recentes
        device.refresh_from_db()
        
        # Determina o status do dispositivo
        if device.is_updated_recently:
            status = 'active'
        elif device.last_position_date:
            status = 'outdated'
        else:
            status = 'no_data'
        
        # Prepara dados para envio
        sync_data = {
            'device_id': device.id,
            'device_name': device.label or f"Device {device.suntech_device_id}",
            'suntech_device_id': device.suntech_device_id,
            'last_position_date': device.last_position_date.isoformat() if device.last_position_date else None,
            'last_system_date': device.last_system_date.isoformat() if device.last_system_date else None,
            'latitude': float(device.last_latitude) if device.last_latitude is not None else None,
            'longitude': float(device.last_longitude) if device.last_longitude is not None else None,
            'speed': int(device.last_speed) if device.last_speed else 0,
            'address': device.last_address or '',
            'status': status,
            'minutes_since_update': float(device.minutes_since_last_update) if device.minutes_since_last_update else 0,
        }
        
        # Envia para o grupo geral (dashboard)
        async_to_sync(channel_layer.group_send)(
            'all_devices',
            {
                'type': 'device_sync',
                'data': sync_data
            }
        )
        
        # Envia para o grupo específico do dispositivo (device_detail)
        async_to_sync(channel_layer.group_send)(
            f'device_{device.id}',
            {
                'type': 'device_sync',
                'data': sync_data
            }
        )
        
        logger.info(f"Notificação de sync enviada para device {device.id} via WebSocket")
        
        return {
            'success': True,
            'device_id': device_id,
            'groups_notified': ['all_devices', f'device_{device.id}']
        }
        
    except Device.DoesNotExist:
        logger.error(f"Dispositivo {device_id} não encontrado para notificação")
        return {
            'success': False,
            'device_id': device_id,
            'error': 'Dispositivo não encontrado'
        }
    
    except Exception as e:
        logger.error(f"Erro ao notificar sync do dispositivo {device_id}: {str(e)}")
        return {
            'success': False,
            'device_id': device_id,
            'error': str(e)
        }
