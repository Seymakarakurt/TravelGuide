import json
from typing import Dict, Any, List
import requests

class MCPService:
    def __init__(self):
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
    
    def _get_weather(self, city: str) -> Dict[str, Any]:
        """Wetter-API-Call"""
        # Hier würde die echte Wetter-API aufgerufen werden
        return {
            "city": city,
            "temperature": "22°C",
            "description": "Sonnig",
            "humidity": "65%"
        }
    
    def _search_hotels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Hotel-Suche"""
        city = params.get("city", "")
        check_in = params.get("check_in", "")
        check_out = params.get("check_out", "")
        
        return {
            "city": city,
            "hotels": [
                {"name": "Hotel A", "price": "120€", "rating": "4.5"},
                {"name": "Hotel B", "price": "95€", "rating": "4.2"}
            ]
        }
    
    def _get_attractions(self, city: str) -> Dict[str, Any]:
        """Sehenswürdigkeiten"""
        attractions = {
            "paris": ["Eiffelturm", "Louvre", "Notre-Dame"],
            "london": ["Big Ben", "Tower Bridge", "Buckingham Palace"],
            "rom": ["Kolosseum", "Vatikan", "Trevi-Brunnen"]
        }
        
        return {
            "city": city,
            "attractions": attractions.get(city.lower(), ["Keine Daten verfügbar"])
        } 