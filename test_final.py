#!/usr/bin/env python3
"""
Finaler Test für das TravelGuide-System (ohne Emojis)
"""

import sys
import os
import json

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_system_structure():
    """Test: System-Struktur"""
    print("Teste System-Struktur...")
    
    required_files = [
        'main.py',
        'decision_logic.py',
        'requirements.txt',
        'README.md',
        'config.env'
    ]
    
    required_dirs = [
        'api_services',
        'evaluation',
        'templates',
        'static',
        'rasa_bot'
    ]
    
    all_good = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  OK: {file}")
        else:
            print(f"  MISSING: {file}")
            all_good = False
    
    for dir in required_dirs:
        if os.path.exists(dir):
            print(f"  OK: {dir}/")
        else:
            print(f"  MISSING: {dir}/")
            all_good = False
    
    return all_good

def test_imports():
    """Test: Module-Imports"""
    print("\nTeste Module-Imports...")
    
    try:
        from main import TravelGuideApp
        print("  OK: TravelGuideApp importiert")
    except Exception as e:
        print(f"  ERROR: TravelGuideApp - {e}")
        return False
    
    try:
        from decision_logic import TravelGuideDecisionLogic
        print("  OK: TravelGuideDecisionLogic importiert")
    except Exception as e:
        print(f"  ERROR: TravelGuideDecisionLogic - {e}")
        return False
    
    try:
        from api_services.ollama_mcp_client import OllamaMCPClient
        print("  OK: OllamaMCPClient importiert")
    except Exception as e:
        print(f"  ERROR: OllamaMCPClient - {e}")
        return False
    
    try:
        from api_services.rag_service import RAGService
        print("  OK: RAGService importiert")
    except Exception as e:
        print(f"  ERROR: RAGService - {e}")
        return False
    
    try:
        from evaluation.evaluation_service import EvaluationService
        print("  OK: EvaluationService importiert")
    except Exception as e:
        print(f"  ERROR: EvaluationService - {e}")
        return False
    
    return True

def test_rag_service():
    """Test: RAG-Service"""
    print("\nTeste RAG-Service...")
    
    try:
        from api_services.rag_service import RAGService
        
        rag = RAGService()
        print(f"  OK: RAG-Service initialisiert mit {len(rag.travel_knowledge)} Einträgen")
        
        # Test Suche
        results = rag.search("Paris Eiffelturm", top_k=2)
        print(f"  OK: Suche funktioniert - {len(results)} Ergebnisse")
        
        # Test Stadt-Info
        paris_info = rag.get_city_info("Paris")
        print(f"  OK: Paris-Info gefunden - {len(paris_info)} Einträge")
        
        return True
    except Exception as e:
        print(f"  ERROR: RAG-Service - {e}")
        return False

def test_evaluation_service():
    """Test: Evaluation-Service"""
    print("\nTeste Evaluation-Service...")
    
    try:
        from evaluation.evaluation_service import EvaluationService
        
        eval_service = EvaluationService()
        print("  OK: Evaluation-Service initialisiert")
        
        # Test Qualitätsbewertung
        evaluation = eval_service.evaluate_response_quality(
            user_message="Hotels in Berlin",
            response={
                "type": "mcp_response",
                "message": "Hier sind Hotels in Berlin gefunden",
                "tool_used": "search_hotels"
            },
            response_time=1.5,
            api_success=True
        )
        
        print(f"  OK: Qualitätsbewertung - Score {evaluation['overall_score']:.2f}")
        
        return True
    except Exception as e:
        print(f"  ERROR: Evaluation-Service - {e}")
        return False

def test_ollama_mcp_client():
    """Test: OllamaMCPClient"""
    print("\nTeste OllamaMCPClient...")
    
    try:
        from api_services.ollama_mcp_client import OllamaMCPClient
        
        client = OllamaMCPClient()
        print(f"  OK: OllamaMCPClient initialisiert - Modell: {client.model}")
        
        # Test Tools
        expected_tools = ["search_hotels", "get_weather", "search_attractions"]
        for tool in expected_tools:
            if tool in client.mcp_tools:
                print(f"  OK: Tool '{tool}' verfügbar")
            else:
                print(f"  MISSING: Tool '{tool}'")
                return False
        
        # Test Tool-Ausführung
        hotel_result = client._call_hotel_api({"location": "Berlin"})
        print(f"  OK: Hotel-API - {hotel_result['success']}")
        
        weather_result = client._call_weather_api({"location": "München"})
        print(f"  OK: Wetter-API - {weather_result['success']}")
        
        attractions_result = client._call_attractions_api({"location": "Paris"})
        print(f"  OK: Attraktionen-API - {attractions_result['success']}")
        
        return True
    except Exception as e:
        print(f"  ERROR: OllamaMCPClient - {e}")
        return False

def test_decision_logic():
    """Test: Decision Logic"""
    print("\nTeste Decision Logic...")
    
    try:
        from decision_logic import TravelGuideDecisionLogic
        from api_services.hotel_service import HotelService
        from api_services.weather_service import WeatherService
        from rasa_bot.rasa_handler import RasaHandler
        
        # Mock Services
        mock_hotel_service = type('MockHotelService', (), {})()
        mock_weather_service = type('MockWeatherService', (), {})()
        mock_rasa_handler = type('MockRasaHandler', (), {})()
        
        decision_logic = TravelGuideDecisionLogic(
            hotel_service=mock_hotel_service,
            weather_service=mock_weather_service,
            rasa_handler=mock_rasa_handler
        )
        
        print(f"  OK: Decision Logic initialisiert - {len(decision_logic.available_tools)} Tools")
        
        # Test Session-Management
        session = decision_logic._initialize_user_session()
        print("  OK: Session-Management funktioniert")
        
        return True
    except Exception as e:
        print(f"  ERROR: Decision Logic - {e}")
        return False

def test_flask_app():
    """Test: Flask-App"""
    print("\nTeste Flask-App...")
    
    try:
        from main import TravelGuideApp
        
        app = TravelGuideApp()
        print("  OK: TravelGuideApp initialisiert")
        
        # Test Health-Endpoint
        with app.app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                data = json.loads(response.data)
                print(f"  OK: Health-Endpoint - {data['status']}")
                return True
            else:
                print(f"  ERROR: Health-Endpoint - Status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ERROR: Flask-App - {e}")
        return False

def main():
    """Hauptfunktion"""
    print("TRAVELGUIDE SYSTEM TEST")
    print("=" * 50)
    
    tests = [
        ("System-Struktur", test_system_structure),
        ("Module-Imports", test_imports),
        ("RAG-Service", test_rag_service),
        ("Evaluation-Service", test_evaluation_service),
        ("OllamaMCPClient", test_ollama_mcp_client),
        ("Decision Logic", test_decision_logic),
        ("Flask-App", test_flask_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"  RESULT: PASSED")
            else:
                print(f"  RESULT: FAILED")
        except Exception as e:
            print(f"  RESULT: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"TEST-ERGEBNIS: {passed}/{total} Tests bestanden")
    print(f"ERFOLGSRATE: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("STATUS: ALLE TESTS ERFOLGREICH!")
        return True
    else:
        print("STATUS: EINIGE TESTS FEHLGESCHLAGEN")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 