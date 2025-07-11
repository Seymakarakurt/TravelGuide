import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
        if not self.api_key:
            logger.warning("OpenWeatherMap API Key nicht gefunden")
    
    def get_weather(self, location: str, date: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not self.api_key:
                return self._get_fallback_weather(location)
            

            coords = self._get_coordinates(location)
            if not coords:
                return self._get_fallback_weather(location)
            
            lat, lon = coords
            

            weather_data = self._get_current_weather(lat, lon)
            if not weather_data:
                return self._get_fallback_weather(location)
            

            if date:
                forecast = self._get_forecast(lat, lon, date)
                if forecast:
                    weather_data.update(forecast)
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Fehler bei Wetterabfrage: {e}")
            return self._get_fallback_weather(location)
    
    def _get_coordinates(self, location: str) -> Optional[tuple]:
        try:
            url = f"http://api.openweathermap.org/geo/1.0/direct"
            params = {
                'q': location,
                'limit': 1,
                'appid': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                return (data[0]['lat'], data[0]['lon'])
            
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei Geocoding: {e}")
            return None
    
    def _get_current_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',  
                'lang': 'de'        
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temperature': round(data['main']['temp']),
                'feels_like': round(data['main']['feels_like']),
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fehler bei aktueller Wetterabfrage: {e}")
            return None
    
    def _get_forecast(self, lat: float, lon: float, target_date: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'de'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            

            try:
                target_dt = datetime.strptime(target_date, "%d.%m.%Y")
            except:
                try:
                    target_dt = datetime.strptime(target_date, "%d.%m")

                    target_dt = target_dt.replace(year=datetime.now().year + 1)
                except:
                    return None
            
            for item in data['list']:
                forecast_dt = datetime.fromtimestamp(item['dt'])
                if forecast_dt.date() == target_dt.date():
                    return {
                        'forecast_temperature': round(item['main']['temp']),
                        'forecast_description': item['weather'][0]['description'],
                        'forecast_icon': item['weather'][0]['icon'],
                        'forecast_date': target_date
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei Wettervorhersage: {e}")
            return None
    
    def _get_fallback_weather(self, location: str) -> Dict[str, Any]:
        return {
            'temperature': 20,
            'feels_like': 22,
            'description': 'Leicht bewölkt',
            'icon': '02d',
            'timestamp': datetime.now().isoformat(),
            'note': f'Wetterdaten für {location} (Simulation - API nicht verfügbar)'
        }
    
    def _get_5day_forecast(self, location: str) -> Optional[str]:
        try:
            if not self.api_key:
                return None
            
            coords = self._get_coordinates(location)
            if not coords:
                return None
            
            lat, lon = coords
            
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'de'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            forecast_summary = ""
            seen_dates = set()
            
            for item in data['list']:
                forecast_dt = datetime.fromtimestamp(item['dt'])
                date_str = forecast_dt.strftime("%d.%m")
                
                if date_str not in seen_dates and len(seen_dates) < 5:
                    seen_dates.add(date_str)
                    temp = round(item['main']['temp'])
                    description = item['weather'][0]['description']
                    
                    forecast_summary += f"• {date_str}: {temp}°C, {description}\n"
            
            return forecast_summary.strip()
            
        except Exception as e:
            logger.error(f"Fehler bei 5-Tage-Vorhersage: {e}")
            return None
    
    def get_weather_summary(self, location: str) -> str:
        weather = self.get_weather(location)
        
        location_title = location.title()
        
        if 'note' in weather:
            return f"Wetter in {location_title}: {weather['description']} bei {weather['temperature']}°C (Simulation)"
        
        summary = f"Wetter in {location_title}:\n"
        summary += f"• Temperatur: {weather['temperature']}°C (gefühlt {weather['feels_like']}°C)\n"
        summary += f"• Beschreibung: {weather['description'].title()}"
        
        forecast_5days = self._get_5day_forecast(location)
        if forecast_5days:
            summary += f"\n\n5-Tage Vorhersage:\n{forecast_5days}"
        
        return summary 