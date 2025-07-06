# TravelGuide

Ein intelligenter Chatbot für Reiseplanung mit modernem Dark Theme Design.

## Features

- **Wetter-Informationen** - Aktuelle Wetterdaten für Reiseziele
- **Hotel-Suche** - Finden Sie passende Unterkünfte
- **KI-Unterstützung** - Intelligente Antworten auf Reisefragen
- **RAG-Pipeline** - Retrieval-Augmented Generation für präzise Antworten
- **MCP-Integration** - Model Context Protocol für strukturierte Funktionsaufrufe

- **Erweiterte Reiseinformationen** - Detaillierte Daten zu 6+ Städten

## Schnellstart

1. **Virtuelle Umgebung erstellen**:
```bash
python -m venv venv
```

2. **Virtuelle Umgebung aktivieren**:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Installieren**:
```bash
pip install -r requirements.txt
```

4. **API-Key hinzufügen**:
```env
# config.env
OPENWEATHER_API_KEY=your-api-key-here
```

5. **Starten**:
```bash
python main.py
```

6. **Öffnen**: http://localhost:5001

## Verwendung
- **Wetter abfragen**: "Wie ist das Wetter in Paris?"
- **Hotels suchen**: "Hotels in London finden"
- **Sehenswürdigkeiten**: "Was kann ich in Rom besichtigen?"
- **Komplexe Anfragen**: "Planen Sie eine 3-tägige Reise nach Berlin"
- **Reiseplanung**: "Empfehlungen für Amsterdam mit Wetter"
- **Alles zurücksetzen**: Für neue Reiseplanung

## Neue Features

### MCP (Model Context Protocol)
- Automatische Tool-Auswahl für komplexe Anfragen
- Strukturierte Funktionsaufrufe mit Ollama
- Intelligente Reiseplanung und -optimierung

### Erweiterte RAG-Pipeline
- Detaillierte Informationen zu Paris, London, Rom, Berlin, Amsterdam
- Kategorisierte Reiseinformationen (Sehenswürdigkeiten, Tipps, allgemeine Infos)
- Verbesserte Suchalgorithmen für präzisere Antworten



## Projektstruktur
```
TravelGuide/
├── main.py              # Flask App
├── decision_logic.py    # Chat-Logik
├── static/              # CSS & JS
├── templates/           # HTML
├── api_services/        # APIs
└── rasa_bot/           # Intent-Erkennung
```

## Lizenz
Für Bildungszwecke erstellt. 