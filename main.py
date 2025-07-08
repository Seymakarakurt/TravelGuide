import os
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from decision_logic import TravelGuideDecisionLogic
from api_services.hotel_service import HotelService
from api_services.weather_service import WeatherService
from rasa_bot.rasa_handler import RasaHandler
from evaluation.evaluation_service import EvaluationService

load_dotenv('config.env')

class TravelGuideApp:
    def __init__(self):
        self.app = Flask(__name__, static_folder='static')
        self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'travelguide-secret-key-2024')
        
        self._initialize_services()
        self._setup_routes()
    
    def _initialize_services(self):
        try:
            self.hotel_service = HotelService()
            self.weather_service = WeatherService()
            self.rasa_handler = RasaHandler()
            
            self.decision_logic = TravelGuideDecisionLogic(
                hotel_service=self.hotel_service,
                weather_service=self.weather_service,
                rasa_handler=self.rasa_handler
            )
            
            try:
                self.evaluation_service = EvaluationService()
                print("✅ Evaluation Service erfolgreich initialisiert")
            except Exception as e:
                print(f"❌ Fehler beim Initialisieren des Evaluation Service: {e}")
                import traceback
                traceback.print_exc()
                self.evaluation_service = None
            
        except Exception as e:
            raise
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat_endpoint():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No data provided'
                    }), 400
                
                message = data.get('message', '').strip()
                user_id = data.get('user_id', 'anonymous')
                
                if not message:
                    return jsonify({
                        'success': False,
                        'error': 'Empty message'
                    }), 400
                
                start_time = time.time()
                response = self.decision_logic.process_user_message(message, user_id)
                response_time = time.time() - start_time
                
                interaction = None
                if self.evaluation_service:
                    try:
                        quality_evaluation = self.evaluation_service.evaluate_response_quality(
                            user_message=message,
                            response=response,
                            response_time=response_time,
                            api_success=response.get('type') != 'error'
                        )
                        
                        intent_evaluation = self.evaluation_service.evaluate_intent_recognition(
                            user_message=message,
                            detected_intent=response.get('detected_intent', ''),
                            confidence=response.get('confidence', 0.0),
                            entities=response.get('entities', {})
                        )
                        
                        performance_metrics = self.evaluation_service.track_performance_metrics(
                            response_time=response_time,
                            api_calls=1 if response.get('tool_used') else 0,
                            api_success_rate=100.0 if response.get('type') != 'error' else 0.0,
                            tool_used=response.get('tool_used')
                        )
                        
                        interaction = {
                            'interaction_id': f"{user_id}_{int(time.time())}",
                            'quality_evaluation': quality_evaluation,
                            'intent_evaluation': intent_evaluation,
                            'performance_metrics': performance_metrics
                        }
                        
                    except Exception as e:
                        print(f"❌ Fehler bei der Evaluierung: {e}")
                        import traceback
                        traceback.print_exc()
                        interaction = {
                            'interaction_id': f"{user_id}_{int(time.time())}",
                            'quality_evaluation': {'overall_score': 0.5}
                        }
                else:
                    interaction = {
                        'interaction_id': f"{user_id}_{int(time.time())}",
                        'quality_evaluation': {'overall_score': 0.5}
                    }
                
                return jsonify({
                    'success': True,
                    'response': response,
                    'interaction_id': interaction.get('interaction_id'),
                    'evaluation': {
                        'quality_score': interaction.get('quality_evaluation', {}).get('overall_score', 0),
                        'response_time': response_time,
                        'quality_dimensions': interaction.get('quality_evaluation', {}).get('quality_scores', {}),
                        'improvement_suggestions': interaction.get('quality_evaluation', {}).get('improvement_suggestions', [])
                    }
                })
                
            except Exception as e:
                import traceback
                print(f"ERROR in chat endpoint: {str(e)}")
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': 'Internal server error'
                }), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/api/feedback', methods=['POST'])
        def feedback_endpoint():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'Keine Daten bereitgestellt'
                    }), 400
                
                interaction_id = data.get('interaction_id')
                rating = data.get('rating', 0)
                helpful = data.get('helpful')
                follow_up_needed = data.get('follow_up_needed', False)
                specific_feedback = data.get('specific_feedback', '')
                user_id = data.get('user_id', 'anonymous')
                
                if not interaction_id:
                    return jsonify({
                        'success': False,
                        'error': 'Interaction ID erforderlich'
                    }), 400
                
                self.evaluation_service.collect_user_feedback(
                    user_id=user_id,
                    response_id=interaction_id,
                    rating=rating,
                    feedback_type="helpful" if helpful else "not_helpful",
                    additional_feedback=specific_feedback
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Feedback erfolgreich gespeichert'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': 'Interner Server-Fehler'
                }), 500
        
        @self.app.route('/api/test/hotels', methods=['GET'])
        def test_hotels():
            try:
                location = request.args.get('location', 'Berlin')
                hotels = self.hotel_service.search_hotels(location=location)
                
                return jsonify({
                    'success': True,
                    'location': location,
                    'hotels_found': len(hotels),
                    'hotels': hotels[:3],
                    'cache_info': {
                        'cached_entries': len(self.hotel_service.price_cache),
                        'cache_file': self.hotel_service.cache_file
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/test/hotels/scraping', methods=['GET'])
        def test_hotel_scraping():
            try:
                location = request.args.get('location', 'Berlin')
                
                self.hotel_service.clear_cache()
                
                hotels = self.hotel_service.search_hotels(location=location)
                
                return jsonify({
                    'success': True,
                    'location': location,
                    'hotels_found': len(hotels),
                    'hotels': hotels[:5],
                    'scraping_test': True,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/test/hotels/debug', methods=['GET'])
        def test_hotel_debug():
            try:
                location = request.args.get('location', 'Berlin')
                
                self.hotel_service.clear_cache()
                
                hotels = self.hotel_service.search_hotels(location=location)
                
                return jsonify({
                    'success': True,
                    'location': location,
                    'hotels_found': len(hotels),
                    'hotels': hotels[:3],
                    'debug_mode': True,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/hotels/cache', methods=['GET'])
        def get_hotel_cache():
            try:
                location = request.args.get('location', '')
                
                if location:
                    cached_hotels = self.hotel_service.get_cached_prices(location)
                    return jsonify({
                        'success': True,
                        'location': location,
                        'cached_hotels': cached_hotels,
                        'count': len(cached_hotels)
                    })
                else:
                    return jsonify({
                        'success': True,
                        'cache_entries': len(self.hotel_service.price_cache),
                        'cache_keys': list(self.hotel_service.price_cache.keys()),
                        'cache_file': self.hotel_service.cache_file
                    })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/hotels/cache/clear', methods=['POST'])
        def clear_hotel_cache():
            try:
                self.hotel_service.clear_cache()
                return jsonify({
                    'success': True,
                    'message': 'Hotel-Cache erfolgreich gelöscht'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/test/mcp', methods=['GET'])
        def test_mcp_service():
            try:
                city = request.args.get('city', 'Wien')
                
                mcp_data = self.decision_logic.mcp_service.collect_all_data_for_city(city)
                
                return jsonify({
                    'success': True,
                    'city': city,
                    'mcp_data': mcp_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/test/mcp/weather', methods=['GET'])
        def test_mcp_weather():
            try:
                city = request.args.get('city', 'Wien')
                
                weather_data = self.decision_logic.mcp_service._get_weather(city)
                
                return jsonify({
                    'success': True,
                    'city': city,
                    'weather_data': weather_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/test/mcp/hotels', methods=['GET'])
        def test_mcp_hotels():
            try:
                city = request.args.get('city', 'Wien')
                
                hotel_data = self.decision_logic.mcp_service._search_hotels({"city": city})
                
                return jsonify({
                    'success': True,
                    'city': city,
                    'hotel_data': hotel_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/test/mcp/attractions', methods=['GET'])
        def test_mcp_attractions():
            try:
                city = request.args.get('city', 'Wien')
                
                attractions_data = self.decision_logic.mcp_service._get_attractions(city)
                
                return jsonify({
                    'success': True,
                    'city': city,
                    'attractions_data': attractions_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/evaluation/report', methods=['GET'])
        def evaluation_report():
            try:
                if not self.evaluation_service:
                    return jsonify({
                        'success': False,
                        'error': 'Evaluation Service nicht verfügbar'
                    }), 500
                
                report = self.evaluation_service.generate_evaluation_report()
                
                return jsonify({
                    'success': True,
                    'report': report
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/evaluation/quality-insights', methods=['GET'])
        def quality_insights():
            try:
                if not self.evaluation_service:
                    return jsonify({
                        'success': False,
                        'error': 'Evaluation Service nicht verfügbar'
                    }), 500
                
                # Generiere Insights aus den Metriken
                metrics = self.evaluation_service._calculate_overall_metrics()
                quality_dimensions = self.evaluation_service._calculate_quality_dimensions()
                
                insights = {
                    'metrics': metrics,
                    'quality_dimensions': quality_dimensions,
                    'recommendations': self.evaluation_service._generate_improvement_recommendations()
                }
                
                return jsonify({
                    'success': True,
                    'insights': insights
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/feedback/statistics', methods=['GET'])
        def feedback_statistics():
            try:
                if not self.evaluation_service:
                    return jsonify({
                        'success': False,
                        'error': 'Evaluation Service nicht verfügbar'
                    }), 500
                
                feedback_stats = self.evaluation_service._calculate_feedback_statistics()
                
                return jsonify({
                    'success': True,
                    'statistics': feedback_stats
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def run(self, host='127.0.0.1', port=5001):
        print("TravelGuide wird gestartet...")
        print(f"Web-Interface verfügbar unter: http://localhost:{port}")
        self.app.run(
            host=host,
            port=port
        )

def main():
    try:
        app = TravelGuideApp()
        app.run(port=5001)
        
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Application failed to start: {e}")
        raise

if __name__ == '__main__':
    main() 