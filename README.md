# TravelGuide - Intelligenter Reiseplanungs-Assistent

Ein Chatbot für Reiseplanung mit KI-gestützter Entscheidungslogik und Tool-Calling-Integration.

## Features

- **Intelligente Entscheidungslogik**: Das System wählt automatisch die passenden Tools
- **Hotel-Suche**: Automatische Hotelsuche mit Preisvergleich
- **Wetter-Abfragen**: Aktuelle Wetterdaten für beliebige Städte
- **Attraktionen**: Sehenswürdigkeiten und Reiseempfehlungen
- **Reiseplanung**: Intelligente Reisevorschläge
- **Feedback-System**: Bewertung der Antwortqualität

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