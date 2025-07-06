import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RasaHandler:
    def __init__(self):

        self.intent_patterns = {
            'greet': [
                r'\b(hallo|hi|hey|guten tag|guten morgen|guten abend)\b'
            ],
            'get_weather': [
                r'\b(wetter|wettervorhersage|temperatur)\s+(in|für|von)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(wie ist das wetter)\s+(in|für|von)\s+([a-zA-Zäöüß\s]+)\b',
                r'\b(wetter|temperatur)\s+([a-zA-Zäöüß\s]+)\b'
            ],
            'search_hotels': [
                r'\b(hotels|hotel)\s+(in|in)\s+([a-zA-Zäöüß]+(?:\s+[a-zA-Zäöüß]+)*?)\s+(finden|suchen)\b',
                r'\b(hotel|hotels|unterkunft)\s+(suchen|finden|buchen)\b',
                r'\b(nach)\s+([a-zA-Zäöüß]+(?:\s+[a-zA-Zäöüß]+)*?)\s+(hotel|hotels|unterkunft)\s+(suchen|finden)\b'
            ],
            'goodbye': [
                r'\b(tschüss|auf wiedersehen|bye|danke)\b'
            ],
            'provide_dates': [
                r'\b(vom|ab|seit)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\s+(bis|bis zum)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\b',
                r'\b(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\s+(bis|bis zum)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\b'
            ],
            'create_plan': [
                r'\b(reiseplan|plan|planung)\s+(erstellen|machen)\b'
            ],
            'reset_session': [
                r'\b(alles zurücksetzen|zurücksetzen|neu starten|neue reise)\b'
            ]
        }

    def process_message(self, message: str, user_id: str) -> Dict[str, Any]:
        try:
            message_lower = message.lower().strip()
            
            best_intent = 'unknown'
            best_confidence = 0.0
            
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, message_lower)
                    if matches:
                        if isinstance(matches[0], tuple):
                            confidence = 0.5
                        else:
                            confidence = len(matches[0]) / len(message_lower) if isinstance(matches[0], str) else 0.5
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_intent = intent
            
            if best_confidence < 0.1:
                best_intent = 'unknown'
                best_confidence = 0.0
            
            logger.info(f"Intent erkannt: {best_intent} (Confidence: {best_confidence:.2f})")
            
            return {
                'intent': best_intent,
                'confidence': best_confidence,
                'entities': self._extract_entities(message_lower, best_intent)
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Intent-Erkennung: {e}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'entities': {}
            }
    
    def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        entities = {}
        
        if intent == 'get_weather':
            weather_patterns = [
                r'\b(wetter|wettervorhersage|temperatur)\s+(in|für|von)\s+([a-zA-Zäöüß]+(?:\s+[a-zA-Zäöüß]+)*?)(?:\s+(?:abfragen|suchen|finden|checken|prüfen))?\b',
                r'\b(wie ist das wetter)\s+(in|für|von)\s+([a-zA-Zäöüß]+(?:\s+[a-zA-Zäöüß]+)*?)(?:\s+(?:abfragen|suchen|finden|checken|prüfen))?\b',
                r'\b(wetter|temperatur)\s+([a-zA-Zäöüß]+(?:\s+[a-zA-Zäöüß]+)*?)(?:\s+(?:abfragen|suchen|finden|checken|prüfen))?\b',
                r'\b(regnet|sonnig|kalt|warm)\s+(in|für)\s+([a-zA-Zäöüß]+(?:\s+[a-zA-Zäöüß]+)*?)(?:\s+(?:abfragen|suchen|finden|checken|prüfen))?\b'
            ]
            for pattern in weather_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    if len(matches[0]) == 3:
                        location = matches[0][2].strip()
                    elif len(matches[0]) == 2:
                        location = matches[0][1].strip()
                    else:
                        continue
                    
                    location = re.sub(r'\s+(?:abfragen|suchen|finden|checken|prüfen)$', '', location, flags=re.IGNORECASE)
                    entities['weather_location'] = location.strip()
                    break
        
        elif intent == 'provide_dates':
            date_patterns = [
                r'\b(vom|ab)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\s+(bis|bis zum)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\b',
                r'\b(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\s+(bis|bis zum)\s+(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{1,2})\b'
            ]
            for pattern in date_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    entities['start_date'] = matches[0][1] if len(matches[0]) == 4 else matches[0][0]
                    entities['end_date'] = matches[0][3] if len(matches[0]) == 4 else matches[0][2]
                    break
        
        elif intent == 'search_hotels':
            hotel_patterns = [
                r'\b(hotels|hotel)\s+(in|in)\s+([a-zA-Zäöüß]+(?:\s+[a-zA-Zäöüß]+)*?)\s+(finden|suchen)\b',
                r'\b(hotel|hotels|unterkunft)\s+(suchen|finden|buchen)\b',
                r'\b(nach)\s+([a-zA-Zäöüß]+(?:\s+[a-zA-Zäöüß]+)*?)\s+(hotel|hotels|unterkunft)\s+(suchen|finden)\b'
            ]
            for pattern in hotel_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    if len(matches[0]) == 4:
                        if matches[0][0] == 'nach':
                            entities['hotel_location'] = matches[0][1].strip()
                        else:
                            entities['hotel_location'] = matches[0][2].strip()
                    elif len(matches[0]) == 2:
                        pass
                    break
        
        return entities 