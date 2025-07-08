# TravelGuide - Intelligenter Reiseplanungs-Assistent

Ein fortschrittlicher Chatbot für Reiseplanung mit KI-gestützter Entscheidungslogik, Tool-Calling-Integration und umfassender Evaluierungsstrategie.

## 🚀 Features

### 🤖 Intelligente Entscheidungslogik
- **Autonome LLM-Integration**: Das System entscheidet selbst, welche Tools es benötigt
- **Tool-Calling**: Dynamische Tool-Auswahl basierend auf Benutzeranfragen
- **Fallback-Mechanismen**: Robuste Fehlerbehandlung und Alternativlösungen

### 🛠️ Verfügbare Tools
- **Hotel-Suche**: Automatische Hotelsuche mit Preisvergleich
- **Wetter-Abfragen**: Aktuelle Wetterdaten für beliebige Städte
- **Attraktionen**: Sehenswürdigkeiten und Reiseempfehlungen
- **Reiseplanung**: Intelligente Reisevorschläge

### 📊 Umfassende Evaluierungsstrategie

#### Response Quality Assessment
- **Automatische Qualitätsbewertung** in 5 Dimensionen:
  - Relevanz (TF-IDF + Keyword-Überlappung)
  - Vollständigkeit (Struktur und Inhalt)
  - Genauigkeit (Fehlerfreiheit und Validierung)
  - Hilfreichkeit (Handlungsorientierung)
  - Kohärenz (Logik und Verständlichkeit)

#### User Feedback System
- **Interaktives Feedback-Widget** nach jeder Antwort
- **Sterne-Bewertung** (1-5) für Antwortqualität
- **Schnelle Bewertungen**: Hilfreich/Nicht hilfreich/Mehr Info
- **Spezifisches Feedback** für Verbesserungsvorschläge

#### Intent Recognition Evaluation
- **Intent-Erkennung-Bewertung** mit Konfidenz-Scores
- **Entity-Extraktion-Genauigkeit** für Named Entities
- **Kontextverständnis-Bewertung** für bessere Intent-Analyse

#### Echtzeit-Metriken
- **Performance-Tracking**: Response-Zeit und API-Erfolg
- **Qualitäts-Insights**: Automatische Verbesserungsvorschläge
- **Feedback-Statistiken**: Nutzerbewertungen und Trends

## 🏗️ Architektur

```
TravelGuide/
├── main.py                     # Flask-Anwendung
├── decision_logic.py           # Intelligente Entscheidungslogik
├── api_services/              # API-Services
│   ├── hotel_service.py       # Hotel-Suche
│   ├── weather_service.py     # Wetter-Abfragen
│   ├── ai_service.py          # AI-Integration
│   └── mcp_service.py         # Tool-Calling
├── evaluation/                # Evaluierungsframework
│   ├── evaluation_service.py  # Hauptservice
│   ├── metrics.json          # Metriken-Speicher
│   ├── user_feedback.json    # Feedback-Daten
│   └── EVALUATION_STRATEGY.md # Dokumentation
├── templates/                 # Frontend-Templates
│   ├── index.html            # Hauptseite
│   └── feedback_widget.html  # Feedback-Widget
└── static/                   # Statische Dateien
    ├── css/style.css         # Styling
    └── js/script.js          # Frontend-Logik
```

## 🚀 Installation

1. **Repository klonen**:
```bash
git clone <repository-url>
cd TravelGuide
```

2. **Virtuelle Umgebung erstellen**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows
```

3. **Abhängigkeiten installieren**:
```bash
pip install -r requirements.txt
```

4. **Umgebungsvariablen konfigurieren**:
```bash
cp config.env.example config.env
# Bearbeiten Sie config.env mit Ihren API-Keys
```

5. **Anwendung starten**:
```bash
python main.py
```

## 📊 Evaluierungsberichte

### API-Endpoints

#### Vollständiger Evaluierungsbericht
```bash
GET /api/evaluation/report
```

#### Qualitäts-Insights
```bash
GET /api/evaluation/quality-insights
```

#### Feedback-Statistiken
```bash
GET /api/feedback/statistics
```

### Beispiel-Response

```json
{
  "success": true,
  "report": {
    "metrics": {
      "total_interactions": 1000,
      "average_response_time": 2.8,
      "average_quality_score": 0.87,
      "api_success_rate": 94.5,
      "intent_recognition_rate": 89.2
    },
    "feedback_stats": {
      "total_feedback": 150,
      "average_rating": 4.2,
      "helpful_percentage": 85.3
    },
    "quality_dimensions": {
      "relevance_score": 0.89,
      "completeness_score": 0.85,
      "accuracy_score": 0.91,
      "helpfulness_score": 0.88,
      "coherence_score": 0.82
    }
  }
}
```

## 🎯 Verwendung

### Chat-Interface
1. Öffnen Sie `http://localhost:5001` im Browser
2. Stellen Sie Fragen wie:
   - "Wie ist das Wetter in Wien?"
   - "Hotels in Barcelona finden"
   - "Sehenswürdigkeiten in Paris"
   - "Empfehlungen für Amsterdam"

### Feedback-System
- Nach jeder Antwort erscheint automatisch ein Feedback-Widget
- Bewerten Sie die Antwortqualität mit 1-5 Sternen
- Geben Sie spezifisches Feedback für Verbesserungen

## 🔧 Konfiguration

### Umgebungsvariablen (config.env)
```env
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
WEATHER_API_KEY=your-weather-api-key
HOTEL_API_KEY=your-hotel-api-key
```

### Evaluierungseinstellungen
- **Qualitäts-Schwellenwerte**: Anpassbar in `evaluation_service.py`
- **Feedback-Widget**: Konfigurierbar in `feedback_widget.html`
- **Metriken-Speicherung**: Automatisch in `metrics.json`

## 📈 Evaluierungsstrategie

### Was wird evaluiert?

1. **Response Quality** (0-1 Score)
   - Relevanz zur ursprünglichen Frage
   - Vollständigkeit der Informationen
   - Genauigkeit der Daten
   - Hilfreichkeit für den Benutzer
   - Kohärenz der Antwort

2. **User Feedback** (1-5 Sterne)
   - Direkte Nutzerbewertungen
   - Spezifische Verbesserungsvorschläge
   - Follow-up-Bedarf

3. **Intent Recognition**
   - Intent-Erkennungsgenauigkeit
   - Entity-Extraktion
   - Kontextverständnis

4. **Performance Metrics**
   - Response-Zeit
   - API-Erfolgsrate
   - Tool-Ausführungsrate

### Verbesserungsvorschläge

Das System generiert automatisch:
- **Schwache Dimensionen**: Identifikation von Verbesserungsbereichen
- **Trend-Analyse**: Entwicklung der Qualität über Zeit
- **User-Feedback-Analyse**: Häufige Verbesserungswünsche

## 🤝 Beitragen

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch
3. Implementieren Sie Ihre Änderungen
4. Fügen Sie Tests hinzu
5. Erstellen Sie einen Pull Request

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

## 🆘 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Dokumentation
2. Schauen Sie in die Issues
3. Erstellen Sie ein neues Issue

---

**TravelGuide** - Ihr intelligenter Reiseplanungs-Assistent mit umfassender Evaluierungsstrategie! 🗺️✨ 