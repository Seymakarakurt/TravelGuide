# TravelGuide - Intelligenter Reiseplanungs-Assistent

Ein Chatbot für Reiseplanung mit echter MCP-Integration und umfassender Evaluierungsstrategie.

## Features

### Echte MCP-Integration
- **Direkte API-Aufrufe**: Das LLM kann APIs direkt aufrufen
- **Tool-Calling**: Dynamische Tool-Auswahl basierend auf Benutzeranfragen
- **Strukturierte API-Integration**: Robuste Fehlerbehandlung und Fallback-Mechanismen

### Verfügbare Tools
- **Hotel-Suche**: Automatische Hotelsuche mit Preisvergleich
- **Wetter-Abfragen**: Aktuelle Wetterdaten für beliebige Städte
- **Attraktionen**: Sehenswürdigkeiten und Reiseempfehlungen
- **Reiseplanung**: Intelligente Reisevorschläge

### Umfassende Evaluierungsstrategie
- **Automatische Qualitätsbewertung** in 5 Dimensionen (Relevanz, Vollständigkeit, Genauigkeit, Hilfreichkeit, Kohärenz)
- **User-Feedback-System**: Interaktives Feedback-Widget mit Sterne-Bewertung
- **Intent-Erkennung-Bewertung**: Konfidenz-Scores und Entity-Extraktion
- **Performance-Metriken**: Response-Zeit und API-Erfolgsrate
- **A/B-Testing**: Automatische Verbesserungsvorschläge

## Architektur

```
TravelGuide/
├── main.py                    # Flask-Anwendung
├── decision_logic.py          # Intelligente Entscheidungslogik
├── api_services/              # API-Services
├── evaluation/                # Evaluierungsframework
├── templates/                 # Frontend-Templates
└── static/                    # Statische Dateien
```

## Installation

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
# Bearbeiten Sie config.env mit Ihren API-Keys
```

5. **Anwendung starten**:
```bash
python main.py
```

## Verwendung

1. Öffnen Sie `http://localhost:5001` im Browser

2. Stellen Sie Fragen wie:
   - "Wie ist das Wetter in Wien?"
   - "Hotels in Barcelona finden"
   - "Sehenswürdigkeiten in Paris"
   - "Empfehlungen für Amsterdam"

3. **Feedback-System**: Nach jeder Antwort erscheint automatisch ein Feedback-Widget zur Bewertung

## Evaluierung

### Automatische Qualitätsbewertung
Das System bewertet jede Antwort in 5 Dimensionen:
- **Relevanz**: TF-IDF + Keyword-Überlappung zur ursprünglichen Frage
- **Vollständigkeit**: Struktur und Inhalt der Antwort
- **Genauigkeit**: Fehlerfreiheit und API-Validierung
- **Hilfreichkeit**: Handlungsorientierung und Vorschläge
- **Kohärenz**: Logik und Verständlichkeit

### User-Feedback-System
- **Interaktives Feedback-Widget** nach jeder Antwort
- **Sterne-Bewertung** (1-5) für Antwortqualität
- **Schnelle Bewertungen**: Hilfreich/Nicht hilfreich/Mehr Info
- **Spezifisches Feedback** für Verbesserungsvorschläge

### Intent-Erkennung-Bewertung
- **Intent-Erkennungsgenauigkeit** mit Konfidenz-Scores
- **Entity-Extraktion-Genauigkeit** für Named Entities
- **Kontextverständnis-Bewertung** für bessere Intent-Analyse

### Performance-Metriken
- **Response-Zeit** und API-Erfolgsrate
- **Tool-Ausführungsrate** und MCP-Integration-Erfolg
- **Qualitäts-Insights** mit automatischen Verbesserungsvorschlägen

### API-Endpoints
- `GET /api/evaluation/report` - Vollständiger Evaluierungsbericht
- `GET /api/evaluation/quality-insights` - Qualitäts-Insights
- `GET /api/feedback/statistics` - Feedback-Statistiken