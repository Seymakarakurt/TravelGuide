import json
import requests
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv('config.env')

class OllamaMCPClient:
    def __init__(self, base_url: str = None, hotel_service=None, weather_service=None):
        if base_url is None:
            self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        else:
            self.base_url = base_url
        self.model = "llama3.1:8b"
        self.hotel_service = hotel_service
        self.weather_service = weather_service
        
        self.mcp_tools = {
            "search_hotels": {
                "function": self._call_hotel_api,
                "description": "Sucht nach Hotels in einer bestimmten Stadt",
                "parameters": {
                    "location": "Stadt oder Ort",
                    "check_in": "Check-in Datum (YYYY-MM-DD)",
                    "check_out": "Check-out Datum (YYYY-MM-DD)",
                    "guests": "Anzahl der Gäste",
                    "currency": "Währung (EUR, TL, USD)"
                }
            },
            "get_weather": {
                "function": self._call_weather_api,
                "description": "Holt aktuelle Wetterinformationen für einen bestimmten Ort",
                "parameters": {
                    "location": "Stadt oder Ort"
                }
            },
            "search_attractions": {
                "function": self._call_attractions_api,
                "description": "Sucht nach Sehenswürdigkeiten in einer Stadt",
                "parameters": {
                    "location": "Stadt oder Ort"
                }
            }
        }
        
    def generate_with_tools(self, message: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = """Du bist ein Reiseassistent mit direkter API-Integration. Du kannst APIs direkt aufrufen.

Verfügbare MCP-Tools:
"""
        
        for tool_name, tool_info in self.mcp_tools.items():
            system_prompt += f"- {tool_name}: {tool_info['description']}\n"
            if 'parameters' in tool_info:
                system_prompt += "  Parameter:\n"
                for param_name, param_desc in tool_info['parameters'].items():
                    system_prompt += f"    - {param_name}: {param_desc}\n"
        
        system_prompt += """

WICHTIGE REGELN:
1. Wenn der Benutzer nach Hotels fragt, verwende IMMER search_hotels
2. Wenn der Benutzer nach Wetter fragt, verwende IMMER get_weather  
3. Wenn der Benutzer nach Sehenswürdigkeiten fragt, verwende IMMER search_attractions
4. Verwende das Format: MCP_CALL: {"tool": "tool_name", "parameters": {"param": "value"}}
5. Du kannst APIs direkt aufrufen - das ist echte MCP-Integration!

Beispiele:
- "Hotels in Berlin" → MCP_CALL: {"tool": "search_hotels", "parameters": {"location": "Berlin"}}
- "Wetter in München" → MCP_CALL: {"tool": "get_weather", "parameters": {"location": "München"}}
- "Sehenswürdigkeiten in Wien" → MCP_CALL: {"tool": "search_attractions", "parameters": {"location": "Wien"}}
"""
        
        prompt = f"{system_prompt}\nUser: {message}"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        try:
            verify_ssl = os.getenv("OLLAMA_VERIFY_SSL", "true").lower() == "true"
            response = requests.post(f"{self.base_url}/api/generate", json=payload, verify=verify_ssl, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "")
            
            if "MCP_CALL:" in content:
                return self._execute_mcp_call(content, message)
            else:
                return {
                    "type": "text_response",
                    "content": content,
                    "tool_called": None
                }
                
        except Exception as e:
            return {
                "type": "error",
                "content": f"Fehler bei der Ollama-Anfrage: {str(e)}",
                "tool_called": None
            }
    
    def _execute_mcp_call(self, content: str, original_message: str) -> Dict[str, Any]:
        try:
            mcp_call_start = content.find("MCP_CALL:")
            if mcp_call_start == -1:
                return {
                    "type": "text_response",
                    "content": content,
                    "tool_called": None
                }
            
            mcp_call_json = content[mcp_call_start + 9:].strip()
            
            if '\n' in mcp_call_json:
                mcp_call_json = mcp_call_json.split('\n')[0]
            
            mcp_call = json.loads(mcp_call_json)
            tool_name = mcp_call.get("tool")
            parameters = mcp_call.get("parameters", {})
            
            if not tool_name or tool_name not in self.mcp_tools:
                return {
                    "type": "error",
                    "content": f"Unbekanntes Tool: {tool_name}",
                    "tool_called": None
                }
            
            print(f"MCP-INTEGRATION: Führe {tool_name} mit Parametern {parameters} aus")
            
            tool_function = self.mcp_tools[tool_name]["function"]
            api_result = tool_function(parameters)
            
            print(f"MCP-INTEGRATION: API-Ergebnis für {tool_name}: {api_result}")
            
            final_response = self._generate_response_from_api_result(api_result, original_message, tool_name)
            
            return {
                "type": "mcp_response",
                "content": final_response,
                "tool_called": {
                    "tool": tool_name,
                    "parameters": parameters,
                    "api_result": api_result
                }
            }
            
        except json.JSONDecodeError as e:
            print(f"MCP JSON Parse Error: {e}")
            return {
                "type": "error",
                "content": f"Fehler beim Parsen des MCP-Calls: {str(e)}",
                "tool_called": None
            }
        except Exception as e:
            print(f"MCP Execution Error: {e}")
            return {
                "type": "error",
                "content": f"Fehler bei der MCP-Ausführung: {str(e)}",
                "tool_called": None
            }
    
    def _call_hotel_api(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        location = parameters.get("location", "")
        check_in = parameters.get("check_in", "")
        check_out = parameters.get("check_out", "")
        currency = parameters.get("currency", "EUR")
        
        if self.hotel_service:
            try:
                if currency and currency.upper() in ["TL", "TRY"]:
                    self.hotel_service.set_currency("TL")
                
                hotels = self.hotel_service.search_hotels(
                    location=location,
                    check_in=check_in,
                    check_out=check_out,
                    currency=currency
                )
                return {
                    "success": True,
                    "data": hotels,
                    "summary": self.hotel_service.get_hotel_summary(hotels, location, check_in, check_out)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Hotel-API Fehler: {str(e)}",
                    "data": None
                }
        

        if currency and currency.upper() in ["TL", "TRY"]:
            mock_data = [
                {"name": "Hotel A", "price": 4200, "rating": 4.2, "currency": "TL"},
                {"name": "Hotel B", "price": 3325, "rating": 3.8, "currency": "TL"}
            ]
            summary = f"Mock-Hotels für {location} gefunden (Preise in TL)"
        else:
            mock_data = [
                {"name": "Hotel A", "price": 120, "rating": 4.2, "currency": "EUR"},
                {"name": "Hotel B", "price": 95, "rating": 3.8, "currency": "EUR"}
            ]
            summary = f"Mock-Hotels für {location} gefunden (Preise in EUR)"
        
        return {
            "success": True,
            "data": mock_data,
            "summary": summary
        }
    
    def _call_weather_api(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        location = parameters.get("location", "")
        
        if self.weather_service:
            try:
                weather_data = self.weather_service.get_weather(location)
                return {
                    "success": True,
                    "data": weather_data,
                    "summary": self.weather_service.get_weather_summary(location)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Wetter-API Fehler: {str(e)}",
                    "data": None
                }
        

        return {
            "success": True,
            "data": {
                "temperature": "22°C",
                "description": "Sonnig",
                "humidity": "65%"
            },
            "summary": f"Mock-Wetter für {location}: 22°C, sonnig"
        }
    
    def _call_attractions_api(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        location = parameters.get("location", "")
        
        attractions = {
            "paris": ["Eiffelturm", "Louvre", "Notre-Dame"],
            "london": ["Big Ben", "Tower Bridge", "Buckingham Palace"],
            "rom": ["Kolosseum", "Vatikan", "Trevi-Brunnen"],
            "berlin": ["Brandenburger Tor", "Berliner Mauer", "Museumsinsel"],
            "amsterdam": ["Grachten", "Van Gogh Museum", "Anne Frank Haus"]
        }
        
        city_attractions = attractions.get(location.lower(), ["Keine Daten verfügbar"])
        
        return {
            "success": True,
            "data": city_attractions,
            "summary": f"Sehenswürdigkeiten in {location}: {', '.join(city_attractions)}"
        }
    
    def _generate_response_from_api_result(self, api_result: Dict[str, Any], original_message: str, tool_name: str) -> str:
        if not api_result.get("success", False):
            return f"Entschuldigung, ich konnte keine Daten für Ihre Anfrage abrufen: {api_result.get('error', 'Unbekannter Fehler')}"
        
        summary = api_result.get("summary", "Daten erfolgreich abgerufen.")
        
        if tool_name == "search_hotels":
            return f"Hier sind die Hotels für Ihre Anfrage: {summary}"
        elif tool_name == "get_weather":
            return f"Das aktuelle Wetter: {summary}"
        elif tool_name == "search_attractions":
            return f"Sehenswürdigkeiten: {summary}"
        else:
            return summary
    
    def generate_follow_up(self, tool_result: Dict[str, Any], original_question: str) -> str:
        prompt = f"""Du bist ein hilfreicher Reiseassistent. Antworte auf Deutsch und sei freundlich und informativ.

Originale Frage: {original_question}
Tool-Ergebnis: {json.dumps(tool_result, ensure_ascii=False, indent=2)}

Antworte basierend auf den Tool-Ergebnissen. Verwende die verfügbaren Daten und sei hilfreich."""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        
        try:
            verify_ssl = os.getenv("OLLAMA_VERIFY_SSL", "true").lower() == "true"
            response = requests.post(f"{self.base_url}/api/generate", json=payload, verify=verify_ssl, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "Keine Antwort verfügbar.")
            
        except Exception as e:
            return f"Fehler bei der Antwortgenerierung: {str(e)}" 