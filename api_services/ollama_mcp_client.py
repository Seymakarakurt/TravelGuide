import json
import requests
import os
from typing import Dict, Any, List

class OllamaMCPClient:
    def __init__(self, base_url: str = None):
        if base_url is None:
            self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        else:
            self.base_url = base_url
        self.model = "llama3.1:8b"
        
    def generate_with_tools(self, message: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = """Du bist ein intelligenter Reiseassistent. Du kannst verschiedene Tools verwenden, um Reiseinformationen zu finden, aber du entscheidest selbst, ob du sie brauchst.

Verfügbare Tools:
"""
        
        for tool in tools:
            system_prompt += f"- {tool['name']}: {tool['description']}\n"
            # Zeige die Parameter für jedes Tool
            if 'parameters' in tool:
                system_prompt += "  Parameter:\n"
                for param_name, param_desc in tool['parameters'].items():
                    system_prompt += f"    - {param_name}: {param_desc}\n"
        
        system_prompt += """
ENTSCHEIDUNGSLOGIK - DU ENTSCHEIDEST AUTONOM:

DU hast die volle Kontrolle über die Entscheidung, ob und welche Tools du verwendest.

VERWENDE TOOLS NUR WENN:
- Du spezifische, aktuelle Daten brauchst (Wetter, Hotel-Preise, aktuelle Sehenswürdigkeiten)
- Du mehrere Informationen gleichzeitig sammeln musst (komplexe Reiseplanung)
- Die Frage nach konkreten, datenabhängigen Informationen verlangt

ANTWORTE DIREKT WENN:
- Du die Frage mit deinem eigenen Wissen beantworten kannst
- Es sich um allgemeine Fragen über Reisen, Kultur, Geschichte handelt
- Du Vergleiche oder Empfehlungen geben kannst
- Die Frage nach Meinungen oder Erfahrungen fragt

BEISPIELE FÜR TOOL-NUTZUNG:
- "Wie ist das Wetter in Wien?" → get_weather
- "Hotels in Paris" → search_hotels  
- "Was kann ich in Rom besichtigen?" → search_attractions
- "Ich plane 3 Tage nach Barcelona, brauche Hotel und Wetter" → get_complete_travel_data

BEISPIELE FÜR DIREKTE ANTWORTEN:
- "Was ist der Eiffelturm?" → Direkte Antwort
- "Was ist eine gute Reisezeit für Europa?" → Direkte Antwort
- "Vergleiche Wien und Paris" → Direkte Antwort
- "Erzähl mir von der Wiener Kaffeehauskultur" → Direkte Antwort
- "Was ist der Unterschied zwischen Hostel und Hotel?" → Direkte Antwort

WICHTIG: Du entscheidest selbst! Verwende Tools nur wenn wirklich nötig.

Wenn du ein Tool verwenden möchtest:
TOOL_CALL: {"tool": "tool_name", "parameters": {"param1": "value1"}}

WICHTIG: Verwende die exakten Parameter-Namen, die in der Tool-Beschreibung angegeben sind!
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
            tool_call = json.loads(tool_call_json)
            
            return {
                "type": "tool_call",
                "content": content,
                "tool_called": {
                    "tool": tool_call.get("tool"),
                    "parameters": tool_call.get("parameters", {})
                }
            }
            
        except json.JSONDecodeError:
            return {
                "type": "text_response",
                "content": content,
                "tool_called": None
            }
    
    def generate_follow_up(self, tool_result: Dict[str, Any], original_question: str) -> str:
        prompt = f"""
Originale Frage: {original_question}
Tool-Ergebnis: {json.dumps(tool_result, ensure_ascii=False, indent=2)}

Antworte auf die ursprüngliche Frage basierend auf den Tool-Ergebnissen.
"""
        
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