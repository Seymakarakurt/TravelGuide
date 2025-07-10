import json
import requests
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv('config.env')

class OllamaMCPClient:
    def __init__(self, base_url: str = None):
        if base_url is None:
            self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        else:
            self.base_url = base_url
        self.model = "llama3.1:8b"
        
    def generate_with_tools(self, message: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = """Du bist ein Reiseassistent. Wenn der Benutzer nach Hotels, Wetter oder Sehenswürdigkeiten fragt, MUSS du IMMER ein Tool verwenden.

Verfügbare Tools:
"""
        
        for tool in tools:
            system_prompt += f"- {tool['name']}: {tool['description']}\n"
            if 'parameters' in tool:
                system_prompt += "  Parameter:\n"
                for param_name, param_desc in tool['parameters'].items():
                    system_prompt += f"    - {param_name}: {param_desc}\n"
        
        system_prompt += """

WICHTIGE REGELN:
1. Wenn der Benutzer nach Hotels fragt, verwende IMMER search_hotels
2. Wenn der Benutzer nach Wetter fragt, verwende IMMER get_weather  
3. Wenn der Benutzer nach Sehenswürdigkeiten fragt, verwende IMMER search_attractions
4. Antworte NICHT mit eigenem Wissen über Hotels, Wetter oder Sehenswürdigkeiten
5. Verwende das Format: TOOL_CALL: {"tool": "tool_name", "parameters": {"param": "value"}}

Beispiele:
- "Hotels in Berlin" → TOOL_CALL: {"tool": "search_hotels", "parameters": {"location": "Berlin"}}
- "Wetter in München" → TOOL_CALL: {"tool": "get_weather", "parameters": {"location": "München"}}
- "Sehenswürdigkeiten in Wien" → TOOL_CALL: {"tool": "search_attractions", "parameters": {"location": "Wien"}}
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
            
            if "TOOL_CALL:" in content:
                return self._parse_tool_call(content)
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
    
    def _parse_tool_call(self, content: str) -> Dict[str, Any]:
        try:
            tool_call_start = content.find("TOOL_CALL:")
            if tool_call_start == -1:
                return {
                    "type": "text_response",
                    "content": content,
                    "tool_called": None
                }
            
            tool_call_json = content[tool_call_start + 10:].strip()
            
            if '\n' in tool_call_json:
                tool_call_json = tool_call_json.split('\n')[0]
            
            tool_call = json.loads(tool_call_json)
            
            if not tool_call.get("tool"):
                print(f"Warnung: Kein Tool-Name in {tool_call}")
                return {
                    "type": "text_response",
                    "content": content,
                    "tool_called": None
                }
            
            return {
                "type": "tool_call",
                "content": content,
                "tool_called": {
                    "tool": tool_call.get("tool"),
                    "parameters": tool_call.get("parameters", {})
                }
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Content: {content}")
            return {
                "type": "text_response",
                "content": content,
                "tool_called": None
            }
    
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