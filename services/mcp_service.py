import json
from typing import Dict, Any, List
from datetime import datetime

class MCPService:
    def __init__(self, hotel_service=None, weather_service=None):
        self.hotel_service = hotel_service
        self.weather_service = weather_service
    
    def collect_all_data_for_city(self, city: str) -> Dict[str, Any]:
        print(f"MCP-SERVICE: Sammle alle Daten für {city}")
        
        collected_data = {
            "city": city,
            "timestamp": datetime.now().isoformat(),
            "weather": None,
            "hotels": None,
            "attractions": None
        }
        
        try:
            collected_data["weather"] = self._get_weather(city)
            print(f"MCP-SERVICE: Wetterdaten für {city} gesammelt")
        except Exception as e:
            collected_data["weather"] = {"error": f"Wetter-API Fehler: {str(e)}"}
            print(f"MCP-SERVICE: Wetter-API Fehler für {city}: {e}")
        
        try:
            hotel_params = {"city": city}
            collected_data["hotels"] = self._search_hotels(hotel_params)
            print(f"MCP-SERVICE: Hotel-Daten für {city} gesammelt")
        except Exception as e:
            collected_data["hotels"] = {"error": f"Hotel-API Fehler: {str(e)}"}
            print(f"MCP-SERVICE: Hotel-API Fehler für {city}: {e}")
        
        try:
            collected_data["attractions"] = self._get_attractions(city)
            print(f"MCP-SERVICE: Sehenswürdigkeiten für {city} gesammelt")
        except Exception as e:
            collected_data["attractions"] = {"error": f"Attractions Fehler: {str(e)}"}
            print(f"MCP-SERVICE: Attractions Fehler für {city}: {e}")
        
        filename = f"travel_data_{city.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, ensure_ascii=False, indent=2)
            print(f"MCP-SERVICE: Daten in {filename} gespeichert")
            collected_data["data_file"] = filename
        except Exception as e:
            print(f"MCP-SERVICE: Fehler beim Speichern: {e}")
        
        print(f"MCP-SERVICE: Alle Daten für {city} erfolgreich gesammelt")
        return collected_data
    
    def _get_weather(self, city: str) -> Dict[str, Any]:
        if self.weather_service:
            try:
                weather_data = self.weather_service.get_weather(city)
                if weather_data:
                    return {
                        "city": city,
                        "data": weather_data,
                        "summary": self.weather_service.get_weather_summary(city)
                    }
            except Exception as e:
                return {"error": f"Wetter-API Fehler: {str(e)}"}
        
        return {
            "city": city,
            "temperature": "22°C",
            "description": "Sonnig",
            "humidity": "65%",
            "note": "Mock-Daten (echte API nicht verfügbar)"
        }
    
    def _search_hotels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        city = params.get("city", "")
        check_in = params.get("check_in", "")
        check_out = params.get("check_out", "")
        
        if self.hotel_service:
            try:
                hotels = self.hotel_service.search_hotels(
                    location=city,
                    check_in=check_in,
                    check_out=check_out
                )
                if hotels:
                    return {
                        "city": city,
                        "hotels": hotels,
                        "summary": self.hotel_service.get_hotel_summary(hotels, city, check_in, check_out)
                    }
            except Exception as e:
                return {"error": f"Hotel-API Fehler: {str(e)}"}
        
        return {
            "city": city,
            "hotels": [
                {"name": "Hotel A", "price": "120€"},
                {"name": "Hotel B", "price": "95€"}
            ],
            "note": "Mock-Daten (echte API nicht verfügbar)"
        }
    
    def _get_attractions(self, city: str) -> Dict[str, Any]:
        attractions = {
            "paris": ["Eiffelturm", "Louvre", "Notre-Dame"],
            "london": ["Big Ben", "Tower Bridge", "Buckingham Palace"],
            "rom": ["Kolosseum", "Vatikan", "Trevi-Brunnen"],
            "berlin": ["Brandenburger Tor", "Berliner Mauer", "Museumsinsel"],
            "amsterdam": ["Grachten", "Van Gogh Museum", "Anne Frank Haus"]
        }
        
        return {
            "city": city,
            "attractions": attractions.get(city.lower(), ["Keine Daten verfügbar"])
        } 