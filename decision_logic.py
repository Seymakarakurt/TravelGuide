import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from api_services import ai_service

class TravelGuideDecisionLogic:
    def __init__(self, hotel_service, weather_service, rasa_handler):
        self.hotel_service = hotel_service
        self.weather_service = weather_service
        self.rasa_handler = rasa_handler
        self.user_sessions = {}

    
    def process_user_message(self, message: str, user_id: str) -> Dict[str, Any]:
        try:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = self._initialize_user_session()

            session = self.user_sessions[user_id]
            rasa_response = self.rasa_handler.process_message(message, user_id)
            intent = rasa_response.get('intent', 'unknown')
            confidence = rasa_response.get('confidence', 0.0)
            entities = rasa_response.get('entities', {})

            self._update_session_with_entities(session, entities)

            message_lower = message.lower()
            has_city = False
            has_hotel_word = any(word in message_lower for word in ["hotel", "unterkunft", "hotels"])
            has_weather_word = any(word in message_lower for word in ["wetter", "klima"])
            
            extracted_city = self._extract_location_from_message(message)
            if extracted_city:
                has_city = True
            
            if has_city and has_weather_word:
                return self._handle_weather_request(user_id, {'weather_location': extracted_city}, message)

            if has_city and has_hotel_word:
                return self._handle_hotel_search_request(user_id, {'hotel_location': extracted_city}, message)
            elif intent == 'search_hotels':
                return self._handle_hotel_search_request(user_id, entities, message)
            elif has_city and not has_hotel_word:
                try:
                    ollama_response = ai_service.generate(message)
                    return {
                        'type': 'general',
                        'message': ollama_response,
                        'suggestions': [
                            'Wie ist das Wetter in Wien?',
                            'Hotels in Barcelona finden',
                            'Hotels in Kopenhagen finden',
                            'Wetter in London abfragen'
                        ]
                    }
                except Exception as e:
                    return {
                        'type': 'error',
                        'message': 'Entschuldigung, die KI ist aktuell nicht erreichbar.',
                        'suggestions': ['Versuchen Sie es später erneut.']
                    }
            if intent == 'greet':
                return self._handle_greeting(user_id)
            elif intent == 'reset_session':
                return self.reset_user_session(user_id)
            elif intent == 'get_weather':
                return self._handle_weather_request(user_id, entities, message)

            elif intent == 'goodbye':
                return self._handle_goodbye(user_id)
            elif intent == 'unknown':
                return self._handle_general_question(message, user_id)
            else:
                return self._handle_general_question(message, user_id)
        except Exception as e:
            return {
                'type': 'error',
                'message': 'Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage.',
                'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
            }


    
    def _clean_destination(self, destination: str) -> str:
        if not destination:
            return destination
        
        unwanted_words = ['suchen', 'finden', 'reisen', 'nach', 'zu']
        
        cleaned = destination
        for word in unwanted_words:
            cleaned = cleaned.replace(f' {word}', '').replace(f'{word} ', '')
        
        for word in unwanted_words:
            cleaned = re.sub(rf'^{word}$', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(rf'^{word}\s+', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(rf'\s+{word}$', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    

    def _update_session_with_entities(self, session: Dict[str, Any], entities: Dict[str, Any]):
        if 'destination' in entities:
            session['preferences']['destination'] = self._clean_destination(entities['destination'])
        if 'start_date' in entities:
            session['preferences']['start_date'] = entities['start_date']
        if 'end_date' in entities:
            session['preferences']['end_date'] = entities['end_date']
    
    def _initialize_user_session(self) -> Dict[str, Any]:
        return {
            'preferences': {
                'destination': None,
                'start_date': None,
                'end_date': None,
                'travelers': 1
            },
            'search_results': {
                'hotels': [],
                'weather': None
            }
        }
    
    def _handle_greeting(self, user_id: str) -> Dict[str, Any]:
        return {
            'type': 'greeting',
            'message': 'Hallo! Ich bin Ihr TravelGuide. Wie kann ich Ihnen helfen?',
            'suggestions': [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Hotels in Kopenhagen finden',
                'Wetter in London abfragen',
                'Wo finde ich die schönsten Sehenswürdigkeiten in Paris?',
                'Was kann ich in Rom besichtigen?',
                'Empfehlungen für Amsterdam',
                'Was sollte ich in Berlin sehen?'
            ]
        }
    
    def reset_user_session(self, user_id: str) -> Dict[str, Any]:
        self.user_sessions[user_id] = self._initialize_user_session()
        
        return {
            'type': 'session_reset',
            'message': 'Perfekt! Lassen Sie uns eine neue Reise planen! \n\nIch helfe Ihnen gerne bei der Reiseplanung! Hier sind einige Möglichkeiten:',
            'suggestions': [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Hotels in Kopenhagen finden',
                'Wetter in London abfragen',
                'Wo finde ich die schönsten Sehenswürdigkeiten in Paris?',
                'Was kann ich in Rom besichtigen?',
                'Empfehlungen für Amsterdam',
                'Was sollte ich in Berlin sehen?'
            ]
        }
    

    
    def _handle_hotel_search_request(self, user_id: str, entities: Dict[str, Any], message: str = "") -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        prefs = session['preferences']
        
        hotel_location = entities.get('hotel_location')
        if hotel_location:
            prefs['destination'] = hotel_location
            session['preferences'] = prefs
        
        if not prefs.get('destination'):
            return {
                'type': 'missing_info',
                'message': 'Ich konnte keine Stadt in Ihrer Nachricht finden. Bitte versuchen Sie es mit einer anderen Formulierung.',
                'suggestions': [
                    'Hotels in Paris',
                    'Unterkunft in London',
                    'Hotel in Rom',
                    'Hotels in Amsterdam',
                    'Unterkunft in Barcelona'
                ]
            }
        
        try:
            location = prefs.get('destination')
            check_in = prefs.get('start_date')
            check_out = prefs.get('end_date')
            guests = prefs.get('travelers', 1)
            
            if not check_in or not check_out:
                today = datetime.now()
                check_in = today.strftime("%Y-%m-%d")
                check_out = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            
            hotels = self.hotel_service.search_hotels(
                location=location,
                check_in=check_in,
                check_out=check_out,
                guests=guests
            )
            
            session['search_results']['hotels'] = hotels
            
            hotel_summary = self.hotel_service.get_hotel_summary(hotels, location, check_in, check_out, guests)
            
            return {
                'type': 'hotel_results',
                'message': hotel_summary,
                'hotels': hotels,
                'suggestions': [
                    'Alles zurücksetzen'
                ]
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Hotelsuche ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut', 'Alles zurücksetzen']
            }
    

    
    def _extract_location_from_message(self, message: str) -> Optional[str]:
        cities = [
            'paris', 'london', 'rom', 'madrid', 'barcelona', 'amsterdam', 'berlin', 'wien', 'prag', 'budapest',
            'stockholm', 'kopenhagen', 'oslo', 'helsinki', 'warschau', 'athen', 'istanbul', 'dubai', 'tokio',
            'singapur', 'bangkok', 'sydney', 'melbourne', 'new york', 'los angeles', 'chicago', 'miami', 'toronto',
            'montreal', 'vancouver', 'mexiko', 'rio de janeiro', 'sao paulo', 'buenos aires', 'santiago', 'lima',
            'bogota', 'caracas', 'havanna', 'kingston', 'port-au-prince', 'santo domingo', 'san juan', 'bridgetown',
            'port of spain', 'georgetown', 'paramaribo', 'cayenne', 'fortaleza', 'recife', 'salvador', 'belo horizonte',
            'brasilia', 'curitiba', 'porto alegre', 'montevideo', 'asuncion', 'la paz', 'sucre', 'lima', 'quito',
            'guayaquil', 'bogota', 'medellin', 'cali', 'caracas', 'maracaibo', 'valencia', 'barquisimeto',
            'maracay', 'ciudad guayana', 'maturin', 'barcelona', 'puerto la cruz', 'petare', 'baruta', 'chacao',
            'catia la mar', 'guarenas', 'guatire', 'los teques', 'petare', 'baruta', 'chacao', 'catia la mar',
            'guarenas', 'guatire', 'los teques', 'petare', 'baruta', 'chacao', 'catia la mar', 'guarenas',
            'guatire', 'los teques', 'petare', 'baruta', 'chacao', 'catia la mar', 'guarenas', 'guatire',
            'los teques', 'petare', 'baruta', 'chacao', 'catia la mar', 'guarenas', 'guatire', 'los teques'
        ]
        
        message_lower = message.lower()
        
        for city in cities:
            if city in message_lower:
                return city.title()
        
        return None

    def _handle_general_question(self, message: str, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        message_lower = message.lower()

        if 'wetter' in message_lower or 'klima' in message_lower:
            location = self._extract_location_from_message(message)
            if location:
                return self._handle_weather_request(user_id, {'weather_location': location}, message)
            else:
                return {
                    'type': 'missing_info',
                    'message': 'Für Wetterinformationen können Sie fragen: "Wie ist das Wetter in [Ort]?"',
                    'suggestions': ['Wie ist das Wetter in Berlin?', 'Wetter in München', 'Temperatur in Hamburg']
                }

        try:
            ollama_response = ai_service.generate(message)
            return {
                'type': 'general',
                'message': ollama_response,
                'suggestions': [
                    'Wie ist das Wetter in Wien?',
                    'Hotels in Barcelona finden',
                    'Hotels in Kopenhagen finden',
                    'Wetter in London abfragen',
                    'Wo finde ich die schönsten Sehenswürdigkeiten in Paris?',
                    'Was kann ich in Rom besichtigen?',
                    'Empfehlungen für Amsterdam',
                    'Was sollte ich in Berlin sehen?'
                ]
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': 'Entschuldigung, die KI ist aktuell nicht erreichbar.',
                'suggestions': ['Versuchen Sie es später erneut.']
            }
    
    def _handle_weather_request(self, user_id: str, entities: Dict[str, Any], original_message: str = "") -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        
        weather_location = entities.get('weather_location')
        
        if not weather_location and original_message:
            weather_location = self._extract_location_from_message(original_message)
        
        if not weather_location:
            return {
                'type': 'missing_info',
                'message': 'Bitte geben Sie einen Ort für die Wetterabfrage an.',
                'suggestions': [
                    'Wie ist das Wetter in Berlin?',
                    'Wetter in München',
                    'Temperatur in Hamburg',
                    'Klima in Wien'
                ]
            }
        
        try:
            weather_data = self.weather_service.get_weather(weather_location)
            
            if weather_data:
                session['search_results']['weather'] = weather_data
                
                weather_message = self.weather_service.get_weather_summary(weather_location)
                
                return {
                    'type': 'weather_results',
                    'message': weather_message,
                    'suggestions': [
                        'Hotels in ' + weather_location.title() + ' finden',
                        'Alles zurücksetzen'
                    ]
                }
            else:
                return {
                    'type': 'error',
                    'message': f'Entschuldigung, ich konnte keine Wetterinformationen für {weather_location} finden.',
                    'suggestions': [
                        'Versuchen Sie einen anderen Ort',
                        'Alles zurücksetzen'
                    ]
                }
                
        except Exception as e:
            return {
                'type': 'error',
                'message': 'Entschuldigung, bei der Wetterabfrage ist ein Fehler aufgetreten.',
                'suggestions': ['Versuchen Sie es später erneut', 'Alles zurücksetzen']
            }

    def _handle_goodbye(self, user_id: str) -> Dict[str, Any]:
        return {
            'type': 'goodbye',
            'message': 'Vielen Dank für die Nutzung des TravelGuide! Ich wünsche Ihnen eine wundervolle Reise! 🌍',
            'suggestions': ['Neue Reise planen']
        }