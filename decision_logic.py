import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from services import ai_service
from services.mcp_service import MCPService
from services.rag_service import RAGService
from services.ollama_mcp_client import OllamaMCPClient

class TravelGuideDecisionLogic:
    def __init__(self, hotel_service, weather_service, rasa_handler):
        self.hotel_service = hotel_service
        self.weather_service = weather_service
        self.rasa_handler = rasa_handler
        self.mcp_service = MCPService(hotel_service=hotel_service, weather_service=weather_service)
        self.rag_service = RAGService()
        self.ollama_mcp_client = OllamaMCPClient()
        self.user_sessions = {}
        
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
            },
            {
                "name": "get_complete_travel_data",
                "description": "Sammelt alle verfügbaren Reisedaten für eine Stadt (Wetter, Hotels, Sehenswürdigkeiten) in einem umfassenden Bericht",
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

            if intent == 'greet':
                response = self._handle_greeting(user_id)
            elif intent == 'reset_session':
                response = self.reset_user_session(user_id)
            elif intent == 'goodbye':
                response = self._handle_goodbye(user_id)
            else:
                response = self._handle_with_autonomous_llm(message, user_id, session)
            
            response['detected_intent'] = intent
            response['confidence'] = confidence
            response['intent_recognized'] = intent not in ['unknown', None, '']
            return response
            
        except Exception as e:
            return {
                'type': 'error',
                'message': 'Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage.',
                'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
            }

    def _handle_with_autonomous_llm(self, message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
        try:
            tool_response = self.ollama_mcp_client.generate_with_tools(message, self.available_tools)
            
            print(f"DEBUG: Tool-Response: {tool_response}")
            
            if tool_response.get("type") == "tool_call":
                tool_called = tool_response.get("tool_called", {})
                tool_name = tool_called.get("tool")
                parameters = tool_called.get("parameters", {})
                
                print(f"OLLAMA ENTSCHEIDUNG: Tool {tool_name} wird verwendet")
                print(f"Parameter: {parameters}")
                
                tool_result = self._execute_tool(tool_name, parameters, session)
                print(f"Tool-Ergebnis: {tool_result.get('summary', 'Keine Zusammenfassung verfügbar')}")
                
                final_response = self.ollama_mcp_client.generate_follow_up(tool_result, message)
                print(f"Finale Antwort generiert")
                
                return {
                    'type': 'tool_response',
                    'message': final_response,
                    'tool_used': tool_name,
                    'tool_parameters': parameters,
                    'suggestions': self._get_suggestions_for_tool(tool_name, parameters)
                }
            else:
                content = tool_response.get("content", "")
                if "TOOL_CALL:" in content:
                    print(f"VERSTECKTER TOOL-CALL GEFUNDEN: {content}")
                    
                    import re
                    tool_call_match = re.search(r'TOOL_CALL:\s*(\{[^}]+\})', content)
                    
                    if tool_call_match:
                        try:
                            tool_call_json = tool_call_match.group(1)
                            tool_call = json.loads(tool_call_json)
                            tool_name = tool_call.get("tool")
                            parameters = tool_call.get("parameters", {})
                            
                            print(f"OLLAMA ENTSCHEIDUNG: Tool {tool_name} wird verwendet (aus verstecktem Call)")
                            print(f"Parameter: {parameters}")
                            
                            tool_result = self._execute_tool(tool_name, parameters, session)
                            print(f"Tool-Ergebnis: {tool_result.get('summary', 'Keine Zusammenfassung verfügbar')}")
                            
                            summary = tool_result.get('summary', 'Keine Daten verfügbar.')
                            
                            return {
                                'type': 'tool_response',
                                'message': summary,
                                'tool_used': tool_name,
                                'tool_parameters': parameters,
                                'suggestions': self._get_suggestions_for_tool(tool_name, parameters)
                            }
                            
                        except json.JSONDecodeError as e:
                            print(f"Fehler beim Parsen des Tool-Calls: {e}")
                            return {
                                'type': 'error',
                                'message': 'Fehler beim Verarbeiten der Tool-Anfrage.',
                                'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
                            }
                    else:
                        return {
                            'type': 'error',
                            'message': 'Konnte keine Tool-Parameter finden.',
                            'suggestions': ['Versuchen Sie es erneut', 'Formulieren Sie Ihre Anfrage anders']
                        }
                
                message_lower = message.lower()
                if any(keyword in message_lower for keyword in ['hotel', 'unterkunft', 'übernachtung', 'zimmer']):
                    print("OLLAMA ENTSCHEIDUNG: Hotel-Anfrage erkannt - verwende search_hotels")
                    location = self._extract_location_from_message(message)
                    if location:
                        tool_result = self._execute_tool("search_hotels", {"location": location}, session)
                        return {
                            'type': 'tool_response',
                            'message': tool_result.get('summary', 'Keine Hotels gefunden.'),
                            'tool_used': 'search_hotels',
                            'tool_parameters': {"location": location},
                            'suggestions': self._get_suggestions_for_tool('search_hotels', {"location": location})
                        }
                
                elif any(keyword in message_lower for keyword in ['wetter', 'temperatur', 'regen', 'sonne']):
                    print("OLLAMA ENTSCHEIDUNG: Wetter-Anfrage erkannt - verwende get_weather")
                    location = self._extract_location_from_message(message)
                    if location:
                        tool_result = self._execute_tool("get_weather", {"location": location}, session)
                        return {
                            'type': 'tool_response',
                            'message': tool_result.get('summary', 'Keine Wetterdaten verfügbar.'),
                            'tool_used': 'get_weather',
                            'tool_parameters': {"location": location},
                            'suggestions': self._get_suggestions_for_tool('get_weather', {"location": location})
                        }
                
                elif any(keyword in message_lower for keyword in ['sehenswürdigkeit', 'attraktion', 'museum', 'denkmal', 'platz']):
                    print("OLLAMA ENTSCHEIDUNG: Sehenswürdigkeiten-Anfrage erkannt - verwende search_attractions")
                    location = self._extract_location_from_message(message)
                    if location:
                        tool_result = self._execute_tool("search_attractions", {"location": location}, session)
                        return {
                            'type': 'tool_response',
                            'message': tool_result.get('summary', 'Keine Sehenswürdigkeiten gefunden.'),
                            'tool_used': 'search_attractions',
                            'tool_parameters': {"location": location},
                            'suggestions': self._get_suggestions_for_tool('search_attractions', {"location": location})
                        }
                
                print("OLLAMA ENTSCHEIDUNG: Kein Tool benötigt - antwortet mit eigenem Wissen")
                suggestions = self._generate_smart_suggestions(message_lower)
                
                return {
                    'type': 'general',
                    'message': tool_response.get("content", "Keine Antwort verfügbar."),
                    'suggestions': suggestions
                }
                
        except Exception as e:
            print(f"Fehler bei Tool-Calling: {str(e)}")
            return self._fallback_to_traditional_logic(message, user_id, session)

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
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
            if not location:
                return {
                    'tool': 'get_weather',
                    'error': 'Keine Stadt angegeben',
                    'summary': 'Bitte geben Sie eine Stadt an, für die Sie das Wetter abfragen möchten.'
                }
            
            weather_data = self.weather_service.get_weather(location)
            session['search_results']['weather'] = weather_data
            
            return {
                'tool': 'get_weather',
                'location': location,
                'weather': weather_data,
                'summary': self.weather_service.get_weather_summary(location)
            }
            
        elif tool_name == "search_attractions":
            if not location:
                return {
                    'tool': 'search_attractions',
                    'error': 'Keine Stadt angegeben',
                    'summary': 'Bitte geben Sie eine Stadt an, für die Sie Sehenswürdigkeiten suchen möchten.'
                }
            
            print(f"RAG-Service wird verwendet für {location}")
            
            city_info = self.rag_service.get_city_info(location)
            attractions_results = self.rag_service.search(f"Sehenswürdigkeiten Attraktionen {location}", top_k=5)
            
            city_specific_results = [doc for doc in attractions_results if doc.get('city', '').lower() == location.lower()]
            general_results = [doc for doc in attractions_results if doc.get('city', '') != location.lower()]
            
            combined_results = city_specific_results + general_results[:2]
            
            if city_specific_results:
                summary = f"Sehenswürdigkeiten in {location.title()}:\n"
                for result in city_specific_results[:3]:
                    summary += f"• {result['content']}\n"
            else:
                summary = f"Keine spezifischen Informationen über Sehenswürdigkeiten in {location} gefunden. Hier sind allgemeine Reisetipps."
            
            return {
                'tool': 'search_attractions',
                'location': location,
                'attractions': combined_results,
                'summary': summary
            }
            
        elif tool_name == "get_travel_recommendations":
            if not location:
                return {
                    'tool': 'get_travel_recommendations',
                    'error': 'Keine Stadt angegeben',
                    'summary': 'Bitte geben Sie eine Stadt an, für die Sie Reiseempfehlungen möchten.'
                }
            
            print(f"RAG-Service wird verwendet für {location}")
            
            city_info = self.rag_service.get_city_info(location)
            travel_tips = self.rag_service.get_travel_tips(location)
            weather_data = self.weather_service.get_weather(location)
            
            summary = f"Reiseempfehlungen für {location.title()}:\n\n"
            
            if city_info:
                for info in city_info:
                    summary += f"• {info['content']}\n"
                summary += "\n"
            
            if travel_tips:
                for tip in travel_tips:
                    summary += f"• {tip['content']}\n"
                summary += "\n"
            
            if weather_data and 'note' not in weather_data:
                summary += f"{weather_data['description']} bei {weather_data['temperature']}°C\n"
            
            all_data = {
                'city_info': city_info,
                'travel_tips': travel_tips,
                'weather': weather_data
            }
            
            return {
                'tool': 'get_travel_recommendations',
                'location': location,
                'recommendations': all_data,
                'summary': summary
            }
            
        elif tool_name == "get_complete_travel_data":
            if not location:
                return {
                    'tool': 'get_complete_travel_data',
                    'error': 'Keine Stadt angegeben',
                    'summary': 'Bitte geben Sie eine Stadt an, für die Sie alle Reisedaten sammeln möchten.'
                }
            
            print(f"MCP-SERVICE wird verwendet für {location}")
            
            mcp_data = self.mcp_service.collect_all_data_for_city(location)
            
            summary = f"Vollständiger Reisebericht für {location.title()}:\n\n"
            
            if mcp_data.get('weather') and 'error' not in mcp_data['weather']:
                weather = mcp_data['weather']
                if isinstance(weather, dict) and 'data' in weather:
                    weather_data = weather['data']
                    summary += f"{weather_data.get('description', 'N/A')} bei {weather_data.get('temperature', 'N/A')}°C\n"
                else:
                    summary += f"{weather.get('description', 'N/A')} bei {weather.get('temperature', 'N/A')}°C\n"
            else:
                summary += "Daten nicht verfügbar\n"
            
            summary += "\n"
            
            if mcp_data.get('hotels') and 'error' not in mcp_data['hotels']:
                hotels = mcp_data['hotels']
                if isinstance(hotels, dict) and 'hotels' in hotels:
                    hotel_list = hotels['hotels']
                    summary += f"{len(hotel_list)} Optionen verfügbar\n"
                    for i, hotel in enumerate(hotel_list[:3], 1):
                        summary += f"  {i}. {hotel.get('name', 'Unbekannt')} - {hotel.get('price', 'Preis auf Anfrage')}\n"
                else:
                    summary += "Daten verfügbar\n"
            else:
                summary += "Daten nicht verfügbar\n"
            
            summary += "\n"
            
            if mcp_data.get('attractions') and 'error' not in mcp_data['attractions']:
                attractions = mcp_data['attractions']
                if isinstance(attractions, dict) and 'attractions' in attractions:
                    attraction_list = attractions['attractions']
                    summary += f"{len(attraction_list)} Highlights\n"
                    for i, attraction in enumerate(attraction_list[:3], 1):
                        summary += f"  {i}. {attraction}\n"
                else:
                    summary += "Daten verfügbar\n"
            else:
                summary += "Daten nicht verfügbar\n"
            
            if mcp_data.get('data_file'):
                summary += f"\nVollständiger Bericht gespeichert in: {mcp_data['data_file']}"
            
            return {
                'tool': 'get_complete_travel_data',
                'location': location,
                'mcp_data': mcp_data,
                'summary': summary
            }
            
        else:
            return {
                'tool': 'unknown',
                'error': f"Unbekanntes Tool: {tool_name}"
            }

    def _get_suggestions_for_tool(self, tool_name: str, parameters: Dict[str, Any]) -> List[str]:
        location = parameters.get('location', '')
        
        if tool_name == "search_hotels":
            return [
                f'Wetter in {location} abfragen',
                f'Sehenswürdigkeiten in {location}',
                f'Reiseempfehlungen für {location}'
            ]
        elif tool_name == "get_weather":
            return [
                f'Hotels in {location} finden',
                f'Sehenswürdigkeiten in {location}',
                f'Reiseempfehlungen für {location}'
            ]
        elif tool_name == "search_attractions":
            return [
                f'Hotels in {location} finden',
                f'Wetter in {location} abfragen',
                f'Reiseempfehlungen für {location}'
            ]
        elif tool_name == "get_travel_recommendations":
            return [
                f'Hotels in {location} finden',
                f'Wetter in {location} abfragen',
                f'Sehenswürdigkeiten in {location}'
            ]
        elif tool_name == "get_complete_travel_data":
            return [
                f'Detaillierte Hotels in {location}',
                f'Wettervorhersage für {location}',
                f'Sehenswürdigkeiten in {location}'
            ]
        else:
            return [
                'Wie ist das Wetter in Wien?',
                'Hotels in Barcelona finden',
                'Sehenswürdigkeiten in Paris',
                'Reiseempfehlungen für Rom'
            ]

    def _generate_smart_suggestions(self, message_lower: str) -> List[str]:
        cities = ['wien', 'berlin', 'paris', 'london', 'rom', 'amsterdam', 'barcelona', 'kopenhagen', 'münchen', 'hamburg']
        mentioned_cities = [city for city in cities if city in message_lower]
        
        has_weather = any(word in message_lower for word in ['wetter', 'klima', 'temperatur'])
        has_hotels = any(word in message_lower for word in ['hotel', 'unterkunft', 'hotels', 'wohnen'])
        has_attractions = any(word in message_lower for word in ['sehenswürdigkeit', 'attraktion', 'besichtigen', 'museum'])
        has_general = any(word in message_lower for word in ['reise', 'urlaub', 'empfehlung', 'tipp'])
        
        suggestions = []
        
        if mentioned_cities:
            city = mentioned_cities[0]
            if has_weather:
                suggestions.append(f'Hotels in {city.title()} finden')
                suggestions.append(f'Sehenswürdigkeiten in {city.title()}')
            elif has_hotels:
                suggestions.append(f'Wetter in {city.title()} abfragen')
                suggestions.append(f'Sehenswürdigkeiten in {city.title()}')
            elif has_attractions:
                suggestions.append(f'Hotels in {city.title()} finden')
                suggestions.append(f'Wetter in {city.title()} abfragen')
            else:
                suggestions.append(f'Wetter in {city.title()} abfragen')
                suggestions.append(f'Hotels in {city.title()} finden')
                suggestions.append(f'Sehenswürdigkeiten in {city.title()}')
        else:
            if has_weather:
                suggestions.extend(['Wetter in Wien abfragen', 'Wetter in Berlin abfragen'])
            elif has_hotels:
                suggestions.extend(['Hotels in Paris finden', 'Hotels in Barcelona finden'])
            elif has_attractions:
                suggestions.extend(['Sehenswürdigkeiten in Rom', 'Sehenswürdigkeiten in Amsterdam'])
            elif has_general:
                suggestions.extend(['Reiseempfehlungen für Wien', 'Reiseempfehlungen für Paris'])
            else:
                suggestions.extend([
                    'Wie ist das Wetter in Wien?',
                    'Hotels in Barcelona finden',
                    'Sehenswürdigkeiten in Paris',
                    'Reiseempfehlungen für Rom'
                ])
        
        if len(suggestions) < 4:
            pass
        
        return suggestions[:4]

    def _fallback_to_traditional_logic(self, message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
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
            'berlin', 'hamburg', 'münchen', 'köln', 'frankfurt', 'stuttgart', 'düsseldorf', 'dortmund', 'essen', 'leipzig',
            'bremen', 'dresden', 'hannover', 'nürnberg', 'duisburg', 'bochum', 'wuppertal', 'bielefeld', 'bonn', 'mannheim',
            'karlsruhe', 'augsburg', 'wiesbaden', 'gelsenkirchen', 'münster', 'aachen', 'braunschweig', 'chemnitz', 'kiel',
            'halle', 'magdeburg', 'freiburg', 'krefeld', 'lübeck', 'oberhausen', 'erfurt', 'mainz', 'rostock', 'kassel',
            'potsdam', 'hagen', 'potsdam', 'hagen', 'potsdam', 'hagen', 'potsdam', 'hagen', 'potsdam', 'hagen',
            
            'paris', 'london', 'rom', 'madrid', 'barcelona', 'amsterdam', 'wien', 'prag', 'budapest',
            'stockholm', 'kopenhagen', 'oslo', 'helsinki', 'warschau', 'athen', 'istanbul', 'dubai', 'tokio',
            'singapur', 'bangkok', 'sydney', 'melbourne', 'new york', 'los angeles', 'chicago', 'miami', 'toronto',
            'montreal', 'vancouver', 'mexiko', 'rio de janeiro', 'sao paulo', 'buenos aires', 'santiago', 'lima',
            'bogota', 'caracas', 'havanna', 'kingston', 'port-au-prince', 'santo domingo', 'san juan', 'bridgetown',
            'port of spain', 'georgetown', 'paramaribo', 'cayenne', 'fortaleza', 'recife', 'salvador', 'belo horizonte',
            'brasilia', 'curitiba', 'porto alegre', 'montevideo', 'asuncion', 'la paz', 'sucre', 'quito',
            'guayaquil', 'medellin', 'cali', 'maracaibo', 'valencia', 'barquisimeto', 'maracay', 'ciudad guayana',
            'maturin', 'puerto la cruz', 'petare', 'baruta', 'chacao', 'catia la mar', 'guarenas', 'guatire', 'los teques'
        ]
        
        message_lower = message.lower()
        
        for city in cities:
            if city in message_lower:
                return city.title()
        
        import re
        in_pattern = re.search(r'in\s+([a-zA-ZäöüßÄÖÜ]+(?:\s+[a-zA-ZäöüßÄÖÜ]+)*)', message_lower)
        if in_pattern:
            potential_city = in_pattern.group(1).strip()
            if len(potential_city) > 2:
                return potential_city.title()
        
        return None

    def _handle_general_question(self, message: str, user_id: str) -> Dict[str, Any]:
        session = self.user_sessions[user_id]
        message_lower = message.lower()

        location = self._extract_location_from_message(message)
        
        if location and any(word in message_lower for word in ['reise', 'urlaub', 'planen', 'besuchen', 'fahren', 'gehen']):
            return self._execute_tool("get_complete_travel_data", {'location': location}, session)

        if 'wetter' in message_lower or 'klima' in message_lower:
            if location:
                return self._handle_weather_request(user_id, {'weather_location': location}, message)
            else:
                return {
                    'type': 'missing_info',
                    'message': 'Für Wetterinformationen können Sie fragen: "Wie ist das Wetter in [Ort]?"',
                    'suggestions': ['Wie ist das Wetter in Berlin?', 'Wetter in München', 'Temperatur in Hamburg']
                }

        if any(word in message_lower for word in ['sehenswürdigkeiten', 'attraktionen', 'besichtigen', 'empfehlungen', 'tipps']):
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
            'message': 'Vielen Dank für die Nutzung des TravelGuide! Ich wünsche Ihnen eine wundervolle Reise!',
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
                        'Praktische Reisetipps'
                    ]
                }
            else:
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
    