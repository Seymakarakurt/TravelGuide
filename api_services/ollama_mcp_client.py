import json
import requests
from typing import Dict, Any, List, Optional

class OllamaMCPClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama2"  # oder ein anderes verfügbares Modell
        
    def generate_with_tools(self, message: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generiert eine Antwort mit Tool-Calling Fähigkeiten"""
        
        # System-Prompt für Tool-Calling
        system_prompt = """Du bist ein Reiseassistent. Du kannst verschiedene Tools verwenden, um Reiseinformationen zu finden.

Verfügbare Tools:
"""
        
        for tool in tools:
            system_prompt += f"- {tool['name']}: {tool['description']}\n"
        
        system_prompt += """
Wenn du eine Frage beantworten kannst, ohne ein Tool zu verwenden, tue das.
Wenn du ein Tool benötigst, antworte im folgenden Format:
TOOL_CALL: {"tool": "tool_name", "parameters": {"param1": "value1"}}
"""
        
        # Ollama API Request
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            # Prüfe auf Tool-Call
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
        """Parst einen Tool-Call aus der Antwort"""
        try:
            # Extrahiere Tool-Call aus der Antwort
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
        """Generiert eine Antwort basierend auf Tool-Ergebnissen"""
        
        context = f"""
Originale Frage: {original_question}
Tool-Ergebnis: {json.dumps(tool_result, ensure_ascii=False, indent=2)}

Antworte auf die ursprüngliche Frage basierend auf den Tool-Ergebnissen.
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": context}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "Keine Antwort verfügbar.")
            
        except Exception as e:
            return f"Fehler bei der Antwortgenerierung: {str(e)}" 