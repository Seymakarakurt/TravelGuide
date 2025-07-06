#!/usr/bin/env python3
"""
Automatisiertes Test-Skript für TravelGuide
Testet alle neuen Features: MCP, RAG, Feedback-System
"""

import requests
import json
import time
from datetime import datetime

class TravelGuideTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Test-Ergebnis protokollieren"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_server_health(self):
        """Testet ob der Server läuft"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Server Health", True, "Server läuft")
                return True
            else:
                self.log_test("Server Health", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Health", False, f"Fehler: {str(e)}")
            return False
    
    def test_chat_api(self):
        """Testet die Chat-API"""
        test_messages = [
            "Hallo",
            "Wie ist das Wetter in Paris?",
            "Hotels in London finden",
            "Was kann ich in Rom besichtigen?",
            "Planen Sie eine Reise nach Berlin"
        ]
        
        for i, message in enumerate(test_messages):
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        'message': message,
                        'user_id': f'test_user_{i}'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        response_type = data['response'].get('type', 'unknown')
                        self.log_test(f"Chat API - {message[:30]}...", True, f"Type: {response_type}")
                    else:
                        self.log_test(f"Chat API - {message[:30]}...", False, "API Error")
                else:
                    self.log_test(f"Chat API - {message[:30]}...", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Chat API - {message[:30]}...", False, f"Exception: {str(e)}")
    
    def test_mcp_functionality(self):
        """Testet MCP-Funktionalität"""
        mcp_test_messages = [
            "Planen Sie eine 3-tägige Reise nach Paris",
            "Empfehlungen für Berlin mit Wetter",
            "Vergleichen Sie Hotels in London und Amsterdam"
        ]
        
        for message in mcp_test_messages:
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        'message': message,
                        'user_id': 'mcp_test_user'
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        response_type = data['response'].get('type')
                        if response_type == 'mcp_response':
                            self.log_test(f"MCP - {message[:30]}...", True, "MCP Response erkannt")
                        else:
                            self.log_test(f"MCP - {message[:30]}...", False, f"Unerwarteter Type: {response_type}")
                    else:
                        self.log_test(f"MCP - {message[:30]}...", False, "API Error")
                else:
                    self.log_test(f"MCP - {message[:30]}...", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"MCP - {message[:30]}...", False, f"Exception: {str(e)}")
    
    def test_rag_functionality(self):
        """Testet RAG-Funktionalität"""
        rag_test_messages = [
            "Was kann ich in Rom besichtigen?",
            "Empfehlungen für Amsterdam",
            "Sehenswürdigkeiten in Berlin"
        ]
        
        for message in rag_test_messages:
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        'message': message,
                        'user_id': 'rag_test_user'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        response_type = data['response'].get('type')
                        if response_type in ['rag_response', 'general']:
                            self.log_test(f"RAG - {message[:30]}...", True, f"Type: {response_type}")
                        else:
                            self.log_test(f"RAG - {message[:30]}...", False, f"Unerwarteter Type: {response_type}")
                    else:
                        self.log_test(f"RAG - {message[:30]}...", False, "API Error")
                else:
                    self.log_test(f"RAG - {message[:30]}...", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"RAG - {message[:30]}...", False, f"Exception: {str(e)}")
    

    
    def run_all_tests(self):
        """Führt alle Tests aus"""
        print("🚀 TravelGuide System-Tests starten...")
        print("=" * 50)
        
        # Server-Test
        if not self.test_server_health():
            print("❌ Server nicht erreichbar. Bitte starten Sie die Anwendung.")
            return
        
        # API-Tests
        self.test_chat_api()
        self.test_mcp_functionality()
        self.test_rag_functionality()
        
        # Zusammenfassung
        print("\n" + "=" * 50)
        print("📊 TEST-ZUSAMMENFASSUNG")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Gesamte Tests: {total_tests}")
        print(f"Erfolgreich: {passed_tests} ✅")
        print(f"Fehlgeschlagen: {failed_tests} ❌")
        print(f"Erfolgsrate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Fehlgeschlagene Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Ergebnisse speichern
        with open('test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detaillierte Ergebnisse gespeichert in: test_results.json")

if __name__ == "__main__":
    tester = TravelGuideTester()
    tester.run_all_tests() 