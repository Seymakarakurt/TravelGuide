import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class FeedbackService:
    def _convert_old_feedback_format(self):
        if not os.path.exists(self.feedback_dir):
            return
        
        conversion_map = {
            'thumbs_up': 'Gut',
            'thumbs_down': 'Schlecht',
            'incomplete': 'Unvollständig',
            'inaccurate': 'Ungenau',
            'unknown': 'Unbekannt'
        }
        
        for filename in os.listdir(self.feedback_dir):
            if filename.startswith("feedback_") and filename.endswith(".json"):
                filepath = os.path.join(self.feedback_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    updated = False
                    for entry in data:
                        if 'feedback_type' in entry:
                            old_type = entry['feedback_type']
                            if old_type in conversion_map:
                                entry['feedback_type'] = conversion_map[old_type]
                                updated = True
                        
                        if 'feedback_types' in entry:
                            old_types = entry['feedback_types']
                            new_types = []
                            for old_type in old_types:
                                if old_type in conversion_map:
                                    new_types.append(conversion_map[old_type])
                                else:
                                    new_types.append(old_type)
                            if new_types != old_types:
                                entry['feedback_types'] = new_types
                                updated = True
                    
                    if updated:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"{filename} konvertiert")
                        
                except Exception as e:
                    print(f"Fehler beim Konvertieren von {filename}: {e}")
    
    def __init__(self):
        self.feedback_dir = "data/feedback_data"
        self._ensure_feedback_dir()
        self._convert_old_feedback_format()
    
    def _ensure_feedback_dir(self):
        if not os.path.exists(self.feedback_dir):
            os.makedirs(self.feedback_dir)
    
    def _determine_category(self, user_message: str, tool_used: str, response_type: str) -> str:
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['wetter', 'temperatur', 'regen', 'sonne', 'kalt', 'warm']):
            return "wetterabfrage"
        elif any(word in message_lower for word in ['hotel', 'unterkunft', 'übernachtung', 'zimmer', 'buchen']):
            return "hotelabfrage"
        elif any(word in message_lower for word in ['sehenswürdigkeit', 'attraktion', 'museum', 'denkmal', 'platz', 'besichtigen']):
            return "sehenswuerdigkeiten"
        elif any(word in message_lower for word in ['empfehlung', 'tipp', 'rat', 'sollte', 'kann']):
            return "reiseempfehlungen"
        elif tool_used == "get_complete_travel_data":
            return "vollstaendiger_bericht"
        else:
            return "allgemein"
    
    def _validate_feedback_type(self, feedback_type: str) -> str:
        valid_types = {
            'thumbs_up': 'Gut',
            'thumbs_down': 'Schlecht', 
            'incomplete': 'Unvollständig',
            'inaccurate': 'Ungenau'
        }
        
        return valid_types.get(feedback_type, 'Unbekannt')
    
    def _get_filename(self, category: str) -> str:
        return f"{self.feedback_dir}/feedback_{category}.json"
    
    def save_feedback(self, user_message: str, ai_response: str, feedback_type: str, 
                     specific_feedback: str = "", tool_used: str = "", response_type: str = "") -> bool:
        try:
            validated_feedback_type = self._validate_feedback_type(feedback_type)
            
            category = self._determine_category(user_message, tool_used, response_type)
            filename = self._get_filename(category)
            
            existing_data = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_data = []
            
            existing_entry = None
            for entry in existing_data:
                if (entry.get('user_message') == user_message and 
                    entry.get('ai_response') == ai_response and
                    entry.get('tool_used') == tool_used):
                    existing_entry = entry
                    break
            
            if existing_entry:
                if 'feedback_types' not in existing_entry:
                    existing_entry['feedback_types'] = [existing_entry.get('feedback_type', 'unknown')]
                    if 'feedback_type' in existing_entry:
                        del existing_entry['feedback_type']
                
                if validated_feedback_type not in existing_entry['feedback_types']:
                    existing_entry['feedback_types'].append(validated_feedback_type)
                
                existing_entry['last_updated'] = datetime.now().isoformat()
                
            else:
                feedback_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "category": category,
                    "user_message": user_message,
                    "ai_response": ai_response,
                    "feedback_types": [validated_feedback_type],
                    "specific_feedback": specific_feedback,
                    "tool_used": tool_used,
                    "response_type": response_type
                }
                existing_data.append(feedback_entry)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print(f"Feedback gespeichert in {filename}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Speichern des Feedbacks: {e}")
            return False
    
    def save_multiple_feedback(self, user_message: str, ai_response: str, feedback_types: list, 
                              specific_feedback: str = "", tool_used: str = "", response_type: str = "") -> bool:
        try:
            validated_feedback_types = []
            for feedback_type in feedback_types:
                validated_type = self._validate_feedback_type(feedback_type)
                if validated_type not in validated_feedback_types:
                    validated_feedback_types.append(validated_type)
            
            if not validated_feedback_types:
                print("Keine gültigen Feedback-Typen gefunden")
                return False
            
            category = self._determine_category(user_message, tool_used, response_type)
            filename = self._get_filename(category)
            
            existing_data = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_data = []
            
            existing_entry = None
            for entry in existing_data:
                if (entry.get('user_message') == user_message and 
                    entry.get('ai_response') == ai_response and
                    entry.get('tool_used') == tool_used):
                    existing_entry = entry
                    break
            
            if existing_entry:
                if 'feedback_types' not in existing_entry:
                    existing_entry['feedback_types'] = [existing_entry.get('feedback_type', 'unknown')]
                    if 'feedback_type' in existing_entry:
                        del existing_entry['feedback_type']
                
                for feedback_type in validated_feedback_types:
                    if feedback_type not in existing_entry['feedback_types']:
                        existing_entry['feedback_types'].append(feedback_type)
                
                existing_entry['last_updated'] = datetime.now().isoformat()
                
            else:
                feedback_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "category": category,
                    "user_message": user_message,
                    "ai_response": ai_response,
                    "feedback_types": validated_feedback_types,
                    "specific_feedback": specific_feedback,
                    "tool_used": tool_used,
                    "response_type": response_type
                }
                existing_data.append(feedback_entry)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print(f"{len(validated_feedback_types)} Feedback-Typen gespeichert in {filename}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Speichern der Feedbacks: {e}")
            return False
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        stats = {}
        
        if not os.path.exists(self.feedback_dir):
            return stats
        
        for filename in os.listdir(self.feedback_dir):
            if filename.startswith("feedback_") and filename.endswith(".json"):
                category = filename.replace("feedback_", "").replace(".json", "")
                filepath = os.path.join(self.feedback_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    total_entries = len(data)
                    feedback_counts = {}
                    
                    for entry in data:
                        feedback_type = entry.get('feedback_type', 'unknown')
                        feedback_counts[feedback_type] = feedback_counts.get(feedback_type, 0) + 1
                    
                    stats[category] = {
                        'total_entries': total_entries,
                        'feedback_counts': feedback_counts,
                        'filename': filename
                    }
                    
                except Exception as e:
                    print(f"Fehler beim Lesen von {filename}: {e}")
        
        return stats
    
    def get_category_feedback(self, category: str) -> list:
        filename = self._get_filename(category)
        
        if not os.path.exists(filename):
            return []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Lesen von {filename}: {e}")
            return []
    
    def clear_feedback(self, category: str = None) -> bool:
        try:
            if category:
                filename = self._get_filename(category)
                if os.path.exists(filename):
                    os.remove(filename)
                    print(f"Feedback für Kategorie '{category}' gelöscht")
            else:
                for filename in os.listdir(self.feedback_dir):
                    if filename.startswith("feedback_") and filename.endswith(".json"):
                        os.remove(os.path.join(self.feedback_dir, filename))
                print("Alle Feedback-Daten gelöscht")
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Löschen: {e}")
            return False 