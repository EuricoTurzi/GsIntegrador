"""
OpenRouteService API Client
Provides geocoding (address → coordinates) and routing services
"""
import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class OpenRouteServiceError(Exception):
    """Base exception for OpenRouteService API errors"""
    pass


class OpenRouteServiceClient:
    """
    Client for OpenRouteService API
    https://openrouteservice.org/dev/#/api-docs
    
    Free tier: 2000 requests/day
    """
    
    BASE_URL = "https://api.openrouteservice.org"
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENROUTESERVICE_API_KEY', None)
        if not self.api_key:
            logger.warning("OPENROUTESERVICE_API_KEY not configured")
    
    def _make_request(self, endpoint, params=None, json_data=None, method='GET'):
        """Make request to OpenRouteService API"""
        if not self.api_key:
            raise OpenRouteServiceError("OpenRouteService API key not configured")
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=json_data, headers=headers, timeout=10)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouteService API error: {e}")
            raise OpenRouteServiceError(f"API request failed: {e}")
    
    def geocode_address(self, address, country='BR'):
        """
        Convert address to coordinates (geocoding)
        
        Args:
            address: Street address to geocode
            country: Country code (default: BR for Brazil)
        
        Returns:
            dict with 'latitude', 'longitude', 'formatted_address'
        """
        cache_key = f"ors_geocode_{address}_{country}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                'text': address,
                'boundary.country': country,
                'size': 1  # Return only best match
            }
            
            data = self._make_request('/geocode/search', params=params)
            
            if not data.get('features'):
                raise OpenRouteServiceError(f"No results found for address: {address}")
            
            feature = data['features'][0]
            coords = feature['geometry']['coordinates']  # [longitude, latitude]
            
            result = {
                'latitude': coords[1],
                'longitude': coords[0],
                'formatted_address': feature['properties'].get('label', address)
            }
            
            # Cache for 7 days
            cache.set(cache_key, result, 60 * 60 * 24 * 7)
            
            return result
        
        except Exception as e:
            logger.error(f"Geocoding error for '{address}': {e}")
            raise OpenRouteServiceError(f"Geocoding failed: {e}")
    
    def reverse_geocode(self, latitude, longitude):
        """
        Convert coordinates to address (reverse geocoding)
        
        Args:
            latitude: Latitude
            longitude: Longitude
        
        Returns:
            dict with 'formatted_address'
        """
        cache_key = f"ors_reverse_{latitude}_{longitude}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                'point.lat': latitude,
                'point.lon': longitude,
                'size': 1
            }
            
            data = self._make_request('/geocode/reverse', params=params)
            
            if not data.get('features'):
                return {'formatted_address': f"{latitude}, {longitude}"}
            
            feature = data['features'][0]
            result = {
                'formatted_address': feature['properties'].get('label', f"{latitude}, {longitude}")
            }
            
            # Cache for 7 days
            cache.set(cache_key, result, 60 * 60 * 24 * 7)
            
            return result
        
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            return {'formatted_address': f"{latitude}, {longitude}"}
    
    def get_route(self, start_coords, end_coords, profile='driving-car'):
        """
        Get route between two points
        
        Args:
            start_coords: (longitude, latitude) tuple for start point
            end_coords: (longitude, latitude) tuple for end point
            profile: Routing profile (driving-car, driving-hgv, cycling-regular, foot-walking)
        
        Returns:
            dict with:
                - distance_meters: Route distance in meters
                - duration_seconds: Route duration in seconds
                - geometry: GeoJSON geometry (coordinates array)
                - bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
        """
        cache_key = f"ors_route_{start_coords}_{end_coords}_{profile}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            json_data = {
                'coordinates': [
                    list(start_coords),  # [longitude, latitude]
                    list(end_coords)
                ]
            }
            
            endpoint = f"/v2/directions/{profile}/geojson"
            data = self._make_request(endpoint, json_data=json_data, method='POST')
            
            if not data.get('features'):
                raise OpenRouteServiceError("No route found")
            
            feature = data['features'][0]
            properties = feature['properties']
            summary = properties['summary']
            
            result = {
                'distance_meters': int(summary['distance']),
                'duration_seconds': int(summary['duration']),
                'geometry': feature['geometry'],  # GeoJSON LineString
                'bbox': data.get('bbox')  # [min_lon, min_lat, max_lon, max_lat]
            }
            
            # Cache for 1 day
            cache.set(cache_key, result, 60 * 60 * 24)
            
            return result
        
        except Exception as e:
            logger.error(f"Routing error: {e}")
            raise OpenRouteServiceError(f"Route calculation failed: {e}")
    
    def get_route_with_waypoints(self, coordinates, profile='driving-car'):
        """
        Get route with multiple waypoints
        
        Args:
            coordinates: List of (longitude, latitude) tuples
            profile: Routing profile
        
        Returns:
            Same as get_route() but for multi-point route
        """
        cache_key = f"ors_route_wp_{len(coordinates)}_{hash(str(coordinates))}_{profile}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            json_data = {
                'coordinates': [list(coord) for coord in coordinates]
            }
            
            endpoint = f"/v2/directions/{profile}/geojson"
            data = self._make_request(endpoint, json_data=json_data, method='POST')
            
            if not data.get('features'):
                raise OpenRouteServiceError("No route found")
            
            feature = data['features'][0]
            properties = feature['properties']
            summary = properties['summary']
            
            result = {
                'distance_meters': int(summary['distance']),
                'duration_seconds': int(summary['duration']),
                'geometry': feature['geometry'],
                'bbox': data.get('bbox'),
                'waypoints': properties.get('way_points', [])  # Indices of waypoints in geometry
            }
            
            # Cache for 1 day
            cache.set(cache_key, result, 60 * 60 * 24)
            
            return result
        
        except Exception as e:
            logger.error(f"Routing with waypoints error: {e}")
            raise OpenRouteServiceError(f"Route calculation failed: {e}")


# Global client instance
openrouteservice_client = OpenRouteServiceClient()
