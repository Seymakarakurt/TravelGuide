import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from api_services import ai_service
from api_services.mcp_service import MCPService
from api_services.rag_service import RAGService
from api_services.ollama_mcp_client import OllamaMCPClient

class TravelGuideDecisionLogic:
    def __init__(self, hotel_service, weather_service, rasa_handler):
        self.hotel_service = hotel_service
        self.weather_service = weather_service
        self.rasa_handler = rasa_handler
        self.mcp_service = MCPService(hotel_service=hotel_service, weather_service=weather_service)
        self.rag_service = RAGService()
        self.ollama_mcp_client = OllamaMCPClient()
        self.user_sessions = {}
        
        # Verfügbare Tools für das LLM
        self.available_tools = [
            {
                "name": "search_hotels",
                "description": "Sucht nach Hotels in einer bestimmten Stadt mit Check-in/Check-out Daten",
                "parameters": {
                    "location": "Stadt oder Ort",
                    "check_in": "Check-in Datum (YYYY-MM-DD)",
                    "check_out": "Check-out Datum (YYYY-MM-DD)",
                    "guests": "Anzahl der Gäste"
                }
            },
            {
                "name": "get_weather",
                "description": "Holt aktuelle Wetterinformationen für einen bestimmten Ort",
                "parameters": {
                    "location": "Stadt oder Ort"
                }
            },
            {
                "name": "search_attractions",
                "description": "Sucht nach Sehenswürdigkeiten und Attraktionen in einer Stadt",
                "parameters": {
                    "location": "Stadt oder Ort"
                }
            },
            {
                "name": "get_travel_recommendations",
                "description": "Gibt allgemeine Reiseempfehlungen für eine Stadt basierend auf verfügbaren Daten",
                "parameters": {
                    "location": "Stadt oder Ort"
                }
            }
        ]

    
    def process_user_message(self, message: str, user_id: str) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = self._initialize_user_session()

            session = self.user_sessions[user_id]
            rasa_response = self.rasa_handler.process_message(message, user_id)
            intent = rasa_response.get('intent', 'unknown')
            confidence = rasa_response.get('confidence', 0.0)
            entities = rasa_response.get('entities', {})

            self._update_session_with_entities(session, entities)

            # ECHTE TOOL-CALLING-INTEGRATION
            # Das LLM entscheidet selbst, welche Tools es braucht
            if intent in ['search_hotels', 'get_weather', 'unknown'] or confidence < 0.7:
                response = self._handle_with_tool_calling(message, user_id, session)
            elif intent == 'greet':
                response = self._handle_greeting(user_id)
            elif intent == 'reset_session':
                response = self.reset_user_session(user_id)
            elif intent == 'goodbye':
                response = self._handle_goodbye(user_id)
            else:
                response = self._handle_with_tool_calling(message, user_id, session)
            
            return response
            
        except Exception as e:
            return {
                'type': 'error',
                'message': 'Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage.',
                'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
            }

    def _handle_with_tool_calling(self, message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        ECHTE TOOL-CALLING-INTEGRATION
        Das LLM entscheidet selbst, welche Tools es braucht
        """
        try:
            # Das LLM entscheidet, ob und welche Tools es verwenden möchte
            tool_response = self.ollama_mcp_client.generate_with_tools(message, self.available_tools)
            
            print(f"DEBUG: Tool-Response: {tool_response}")
            
            if tool_response.get("type") == "tool_call":
                # Das LLM hat entschieden, ein Tool zu verwenden
                tool_called = tool_response.get("tool_called", {})
                tool_name = tool_called.get("tool")
                parameters = tool_called.get("parameters", {})
                
                print(f"LLM hat Tool '{tool_name}' mit Parametern {parameters} aufgerufen")
                
                # Tool ausführen
                tool_result = self._execute_tool(tool_name, parameters, session)
                
                # LLM generiert finale Antwort basierend auf Tool-Ergebnis
                final_response = self.ollama_mcp_client.generate_follow_up(tool_result, message)
                
                return {
                    'type': 'tool_response',
                    'message': final_response,
                    'tool_used': tool_name,
                    'tool_parameters': parameters,
                    'suggestions': self._get_suggestions_for_tool(tool_name, parameters)
                }
            else:
                # Prüfe, ob in der Antwort ein Tool-Call versteckt ist
                content = tool_response.get("content", "")
                if "get_weather:" in content or "search_hotels:" in content or "search_attractions:" in content:
                    # Tool-Call in der Antwort gefunden - extrahiere und verarbeite
                    print(f"DEBUG: Tool-Call in Antwort gefunden: {content}")
                    
                    # Extrahiere Tool-Call aus der Antwort
                    if "get_weather:" in content:
                        tool_name = "get_weather"
                        # Extrahiere Location aus der Antwort
                        import re
                        location_match = re.search(r'"location":\s*"([^"]+)"', content)
                        if location_match:
                            location = location_match.group(1)
                            parameters = {"location": location}
                            
                            print(f"DEBUG: Extrahierte Parameter: {parameters}")
                            
                            # Tool ausführen
                            tool_result = self._execute_tool(tool_name, parameters, session)
                            
                            # Verwende die Wetter-Zusammenfassung als Antwort
                            weather_summary = tool_result.get('summary', 'Keine Wetterdaten verfügbar.')
                            
                            return {
                                'type': 'tool_response',
                                'message': weather_summary,
                                'tool_used': tool_name,
                                'tool_parameters': parameters,
                                'suggestions': self._get_suggestions_for_tool(tool_name, parameters)
                            }
                
                # Das LLM hat entschieden, keine Tools zu verwenden
                return {
                    'type': 'general',
                    'message': tool_response.get("content", "Keine Antwort verfügbar."),
                    'suggestions': [
                        'Wie ist das Wetter in Wien?',
                        'Hotels in Barcelona finden',
                        'Sehenswürdigkeiten in Paris',
                        'Reiseempfehlungen für Rom'
                    ]
                }
                
        except Exception as e:
            print(f"Fehler bei Tool-Calling: {str(e)}")
            # Fallback zu traditioneller Logik
            return self._fallback_to_traditional_logic(message, user_id, session)

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt das vom LLM gewählte Tool aus
        """
        location = parameters.get('location', '')
        
        if tool_name == "search_hotels":
            check_in = parameters.get('check_in', datetime.now().strftime("%Y-%m-%d"))
            check_out = parameters.get('check_out', (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
            guests = parameters.get('guests', 1)
            
            hotels = self.hotel_service.search_hotels(
                location=location,
                check_in=check_in,
                check_out=check_out,
                guests=guests
            )
            
            session['search_results']['hotels'] = hotels
            return {
                'tool': 'search_hotels',
                'location': location,
                'hotels': hotels,
                'summary': self.hotel_service.get_hotel_summary(hotels, location, check_in, check_out, guests)
            }
            
        elif tool_name == "get_weather":
            weather_data = self.weather_service.get_weather(location)
            session['search_results']['weather'] = weather_data
            
            return {
                'tool': 'get_weather',
                'location': location,
                'weather': weather_data,
                'summary': self.weather_service.get_weather_summary(location)
            }
            
        elif tool_name == "search_attractions":
            # Verwende RAG Service für Sehenswürdigkeiten
            attractions_query = f"Sehenswürdigkeiten und Attraktionen in {location}"
            attractions_results = self.rag_service.search(attractions_query)
            
            return {
                'tool': 'search_attractions',
                'location': location,
                'attractions': attractions_results,
                'summary': f"Informationen über Sehenswürdigkeiten in {location}"
            }
            
        elif tool_name == "get_travel_recommendations":
            # Kombiniere alle verfügbaren Daten für umfassende Empfehlungen
            all_data = self.mcp_service.collect_all_data_for_city(location)
            
            return {
                'tool': 'get_travel_recommendations',
                'location': location,
                'recommendations': all_data,
                'summary': f"Umfassende Reiseempfehlungen für {location}"
            }
            
        else:
            return {
                'tool': 'unknown',
                'error': f"Unbekanntes Tool: {tool_name}"
            }

    def _get_suggestions_for_tool(self, tool_name: str, parameters: Dict[str, Any]) -> List[str]:
        """
        Generiert passende Vorschläge basierend auf dem verwendeten Tool
        """
        location = parameters.get('location', '')
        
        if tool_name == "search_hotels":
            return [
                f'Wetter in {location} abfragen',
                f'Sehenswürdigkeiten in {location}',
                f'Reiseempfehlungen für {location}',
                'Andere Stadt erkunden'
            ]
        elif tool_name == "get_weather":
            return [
                f'Hotels in {location} finden',
                f'Sehenswürdigkeiten in {location}',
                f'Reiseempfehlungen für {location}',
                'Andere Stadt erkunden'
            ]
        elif tool_name == "search_attractions":
            return [
                f'Hotels in {location} finden',
                f'Wetter in {location} abfragen',
                f'Reiseempfehlungen für {location}',
                'Andere Stadt erkunden'
            ]
        elif tool_name == "get_travel_recommendations":
            return [
                f'Hotels in {location} finden',
                f'Wetter in {location} abfragen',
                f'Sehenswürdigkeiten in {location}',
                'Andere Stadt erkunden'
            ]
        else:
            return [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Sehenswürdigkeiten in Paris',
                'Reiseempfehlungen für Rom'
            ]

    def _fallback_to_traditional_logic(self, message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback zur traditionellen Logik, falls Tool-Calling fehlschlägt
        """
        message_lower = message.lower()
        has_city = False
        has_hotel_word = any(word in message_lower for word in ["hotel", "unterkunft", "hotels"])
        has_weather_word = any(word in message_lower for word in ["wetter", "klima"])
        
        extracted_city = self._extract_location_from_message(message)
        if extracted_city:
            has_city = True
        
        if has_city and has_weather_word:
            return self._handle_weather_request(user_id, {'weather_location': extracted_city}, message)
        elif has_city and has_hotel_word:
            return self._handle_hotel_search_request(user_id, {'hotel_location': extracted_city}, message)
        elif has_city and not has_hotel_word:
            return self._handle_rag_request(message, user_id)
        else:
            return self._handle_general_question(message, user_id)

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

        if any(word in message_lower for word in ['sehenswürdigkeiten', 'attraktionen', 'besichtigen', 'empfehlungen', 'tipps']):
            location = self._extract_location_from_message(message)
            if location:
                rag_answer = self.rag_service.answer_question(message, location)
                return {
                    'type': 'rag_response',
                    'message': rag_answer,
                    'suggestions': [
                        'Hotels in ' + location.title() + ' finden',
                        'Wetter in ' + location.title() + ' abfragen',
                        'Alles zurücksetzen'
                    ]
                }

        try:
            rag_answer = self.rag_service.answer_question(message)
            if rag_answer and "keine relevanten Informationen" not in rag_answer:
                return {
                    'type': 'rag_response',
                    'message': rag_answer,
                    'suggestions': [
                        'Wie ist das Wetter in Wien?',
                        'Hotels in Barcelona finden',
                        'Hotels in Kopenhagen finden',
                        'Wetter in London abfragen'
                    ]
                }
            else:
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
    
    def _handle_rag_request(self, message: str, user_id: str) -> Dict[str, Any]:
        try:
            rag_results = self.rag_service.search(message)
            
            if rag_results and len(rag_results) > 0:
                context = "\n".join([result['content'] for result in rag_results])
                enhanced_response = self.ollama_mcp_client.generate_follow_up(
                    {'context': context, 'query': message}, 
                    message
                )
                
                return {
                    'type': 'rag_response',
                    'message': enhanced_response,
                    'sources': rag_results,
                    'suggestions': [
                        'Mehr Details zu Sehenswürdigkeiten',
                        'Praktische Reisetipps',
                        'Andere Stadt erkunden'
                    ]
                }
            else:
                # Fallback zu allgemeiner KI-Antwort
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
                    
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Fehler bei der RAG-Verarbeitung: {str(e)}',
                'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
            }
    
