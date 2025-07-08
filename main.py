import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from decision_logic import TravelGuideDecisionLogic
from api_services.hotel_service import HotelService
from api_services.weather_service import WeatherService
from rasa_bot.rasa_handler import RasaHandler

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
            
        except Exception as e:
            raise
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/evaluation')
        def evaluation_dashboard():
            return render_template('evaluation_dashboard.html')
        
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
                
                response = self.decision_logic.process_user_message(message, user_id)
                
                return jsonify({
                    'success': True,
                    'response': response
                })
                
            except Exception as e:
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
        
        @self.app.route('/api/evaluation/report', methods=['GET'])
        def get_evaluation_report():
            try:
                report = self.decision_logic.evaluation_system.get_evaluation_report()
                return jsonify({
                    'success': True,
                    'report': report,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/evaluation/metrics', methods=['GET'])
        def get_evaluation_metrics():
            try:
                metrics = self.decision_logic.evaluation_system.metrics
                return jsonify({
                    'success': True,
                    'metrics': metrics,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
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
                
                # Teste MCP-Service
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
                
                # Teste nur Wetter-Komponente
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
                
                # Teste nur Hotel-Komponente
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
                
                # Teste nur Attractions-Komponente
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