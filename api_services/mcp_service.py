import json
from typing import Dict, Any, List
import requests
from datetime import datetime

class MCPService:
    def __init__(self, hotel_service=None, weather_service=None):
        self.hotel_service = hotel_service
        self.weather_service = weather_service
        
        self.tools = {
            "get_weather": {
                "name": "get_weather",
                "description": "Holt Wetterdaten für eine Stadt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name der Stadt"
                        }
                    },
                    "required": ["city"]
                }
            },
            "search_hotels": {
                "name": "search_hotels", 
                "description": "Sucht Hotels in einer Stadt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name der Stadt"
                        },
                        "check_in": {
                            "type": "string",
                            "description": "Check-in Datum (YYYY-MM-DD)"
                        },
                        "check_out": {
                            "type": "string", 
                            "description": "Check-out Datum (YYYY-MM-DD)"
                        }
                    },
                    "required": ["city"]
                }
            },
            "get_attractions": {
                "name": "get_attractions",
                "description": "Gibt Sehenswürdigkeiten für eine Stadt zurück",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name der Stadt"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Gibt das Tool-Schema für MCP zurück"""
        return list(self.tools.values())
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Führt einen Tool-Call aus"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} nicht gefunden"}
        
        try:
            if tool_name == "get_weather":
                return self._get_weather(parameters["city"])
            elif tool_name == "search_hotels":
                return self._search_hotels(parameters)
            elif tool_name == "get_attractions":
                return self._get_attractions(parameters["city"])
        except Exception as e:
            return {"error": str(e)}
    
    def collect_all_data_for_city(self, city: str) -> Dict[str, Any]:
        """Sammelt alle verfügbaren Daten für eine Stadt und speichert sie in JSON"""
        collected_data = {
            "city": city,
            "timestamp": datetime.now().isoformat(),
            "weather": None,
            "hotels": None,
            "attractions": None,
            "summary": ""
        }
        
        # 1. Wetterdaten sammeln
        try:
            collected_data["weather"] = self._get_weather(city)
            print(f"✅ Wetterdaten für {city} gesammelt")
        except Exception as e:
            collected_data["weather"] = {"error": f"Wetter-API Fehler: {str(e)}"}
            print(f"❌ Wetter-API Fehler für {city}: {e}")
        
        # 2. Hotel-Daten sammeln
        try:
            hotel_params = {"city": city}
            collected_data["hotels"] = self._search_hotels(hotel_params)
            print(f"✅ Hotel-Daten für {city} gesammelt")
        except Exception as e:
            collected_data["hotels"] = {"error": f"Hotel-API Fehler: {str(e)}"}
            print(f"❌ Hotel-API Fehler für {city}: {e}")
        
        # 3. Sehenswürdigkeiten sammeln
        try:
            collected_data["attractions"] = self._get_attractions(city)
            print(f"✅ Sehenswürdigkeiten für {city} gesammelt")
        except Exception as e:
            collected_data["attractions"] = {"error": f"Attractions Fehler: {str(e)}"}
            print(f"❌ Attractions Fehler für {city}: {e}")
        
        # 4. JSON-Datei speichern
        filename = f"travel_data_{city.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Daten in {filename} gespeichert")
            collected_data["data_file"] = filename
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
        
        return collected_data
    
    def _get_weather(self, city: str) -> Dict[str, Any]:
        """Wetter-API-Call"""
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
        
        # Fallback zu Mock-Daten
        return {
            "city": city,
            "temperature": "22°C",
            "description": "Sonnig",
            "humidity": "65%",
            "note": "Mock-Daten (echte API nicht verfügbar)"
        }
    
    def _search_hotels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Hotel-Suche"""
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
        
        # Fallback zu Mock-Daten
        return {
            "city": city,
            "hotels": [
                {"name": "Hotel A", "price": "120€", "rating": "4.5"},
                {"name": "Hotel B", "price": "95€", "rating": "4.2"}
            ],
            "note": "Mock-Daten (echte API nicht verfügbar)"
        }
    
    def _get_attractions(self, city: str) -> Dict[str, Any]:
        """Sehenswürdigkeiten"""
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