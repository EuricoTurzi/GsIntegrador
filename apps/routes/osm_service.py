"""
Serviço de integração com OpenStreetMap/OSRM para cálculo de rotas.
"""
import requests
import logging
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)


class OSMServiceError(Exception):
    """Exceção personalizada para erros do serviço OSM."""
    pass


def calculate_route_osm(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    profile: str = 'driving'
) -> Optional[Dict]:
    """
    Calcula uma rota entre dois pontos usando o serviço OSRM (OpenStreetMap).
    
    Args:
        origin: Tupla (latitude, longitude) do ponto de origem
        destination: Tupla (latitude, longitude) do ponto de destino
        profile: Perfil de roteamento ('driving', 'walking', 'cycling')
        
    Returns:
        Dicionário com:
        - distance: Distância em metros
        - duration: Duração em segundos
        - geometry: Geometria da rota em formato GeoJSON
        
    Raises:
        OSMServiceError: Em caso de erro na requisição
    """
    # Servidor público OSRM (pode ser substituído por servidor próprio)
    base_url = "http://router.project-osrm.org"
    
    # OSRM usa longitude,latitude (diferente do padrão)
    origin_lon, origin_lat = origin[1], origin[0]
    dest_lon, dest_lat = destination[1], destination[0]
    
    # Montar URL
    url = f"{base_url}/route/v1/{profile}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    
    params = {
        'overview': 'full',  # Retorna geometria completa
        'geometries': 'geojson',  # Formato GeoJSON
        'steps': 'false'  # Não precisa de instruções passo-a-passo
    }
    
    try:
        logger.info(f"Calculando rota de {origin} para {destination}")
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('code') != 'Ok':
            error_message = data.get('message', 'Erro desconhecido')
            logger.error(f"Erro OSRM: {error_message}")
            raise OSMServiceError(f"Erro ao calcular rota: {error_message}")
        
        # Extrair primeira rota (normalmente a melhor)
        routes = data.get('routes', [])
        if not routes:
            raise OSMServiceError("Nenhuma rota encontrada")
        
        route = routes[0]
        
        result = {
            'distance': int(route.get('distance', 0)),  # metros
            'duration': int(route.get('duration', 0)),  # segundos
            'geometry': route.get('geometry')  # GeoJSON
        }
        
        logger.info(
            f"Rota calculada: {result['distance']/1000:.2f} km, "
            f"{result['duration']/60:.0f} min"
        )
        
        return result
        
    except requests.exceptions.Timeout:
        logger.error("Timeout ao conectar com OSRM")
        raise OSMServiceError("Timeout ao calcular rota")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição OSRM: {str(e)}")
        raise OSMServiceError(f"Erro ao conectar com serviço de rotas: {str(e)}")
    
    except (KeyError, ValueError) as e:
        logger.error(f"Erro ao processar resposta OSRM: {str(e)}")
        raise OSMServiceError("Resposta inválida do serviço de rotas")


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Converte um endereço em coordenadas geográficas usando Nominatim (OSM).
    
    Args:
        address: Endereço completo a ser geocodificado
        
    Returns:
        Tupla (latitude, longitude) ou None se não encontrado
        
    Raises:
        OSMServiceError: Em caso de erro na requisição
    """
    base_url = "https://nominatim.openstreetmap.org/search"
    
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    
    headers = {
        'User-Agent': 'IntegradorApp/1.0'  # Nominatim requer User-Agent
    }
    
    try:
        logger.info(f"Geocodificando endereço: {address}")
        
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            logger.warning(f"Endereço não encontrado: {address}")
            return None
        
        result = data[0]
        lat = float(result['lat'])
        lon = float(result['lon'])
        
        logger.info(f"Endereço geocodificado: ({lat}, {lon})")
        
        return (lat, lon)
        
    except requests.exceptions.Timeout:
        logger.error("Timeout ao conectar com Nominatim")
        raise OSMServiceError("Timeout ao geocodificar endereço")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição Nominatim: {str(e)}")
        raise OSMServiceError(f"Erro ao geocodificar endereço: {str(e)}")
    
    except (KeyError, ValueError, IndexError) as e:
        logger.error(f"Erro ao processar resposta Nominatim: {str(e)}")
        raise OSMServiceError("Resposta inválida do serviço de geocodificação")


def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """
    Converte coordenadas geográficas em endereço (reverse geocoding).
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        Endereço formatado ou None se não encontrado
        
    Raises:
        OSMServiceError: Em caso de erro na requisição
    """
    base_url = "https://nominatim.openstreetmap.org/reverse"
    
    params = {
        'lat': latitude,
        'lon': longitude,
        'format': 'json',
        'addressdetails': 1
    }
    
    headers = {
        'User-Agent': 'IntegradorApp/1.0'
    }
    
    try:
        logger.info(f"Reverse geocoding: ({latitude}, {longitude})")
        
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'error' in data:
            logger.warning(f"Coordenadas não encontradas: {data.get('error')}")
            return None
        
        address = data.get('display_name')
        
        logger.info(f"Endereço encontrado: {address}")
        
        return address
        
    except requests.exceptions.Timeout:
        logger.error("Timeout ao conectar com Nominatim")
        raise OSMServiceError("Timeout ao buscar endereço")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição Nominatim: {str(e)}")
        raise OSMServiceError(f"Erro ao buscar endereço: {str(e)}")
    
    except (KeyError, ValueError) as e:
        logger.error(f"Erro ao processar resposta Nominatim: {str(e)}")
        raise OSMServiceError("Resposta inválida do serviço de geocodificação")


def calculate_distance_haversine(
    coord1: Tuple[float, float],
    coord2: Tuple[float, float]
) -> float:
    """
    Calcula a distância em linha reta entre dois pontos usando a fórmula de Haversine.
    
    Args:
        coord1: Tupla (latitude, longitude) do primeiro ponto
        coord2: Tupla (latitude, longitude) do segundo ponto
        
    Returns:
        Distância em metros
    """
    from math import radians, sin, cos, sqrt, atan2
    
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Raio da Terra em metros
    R = 6371000
    
    # Converter para radianos
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    # Fórmula de Haversine
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance
