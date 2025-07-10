from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RAGService:
    def __init__(self):
        self.travel_knowledge = [
            {"id": 1, "content": "Paris ist die Hauptstadt Frankreichs und bekannt für den Eiffelturm, den Louvre und die Champs-Élysées. Die beste Reisezeit ist von April bis Oktober.", "category": "city_info", "city": "paris"},
            {"id": 2, "content": "Für Reisen nach Paris empfehlen sich mindestens 3-4 Tage. Besuchen Sie den Eiffelturm am besten früh morgens oder abends.", "category": "travel_tips", "city": "paris"},
            {"id": 3, "content": "Der Louvre ist das größte Kunstmuseum der Welt. Kaufen Sie Tickets online und besuchen Sie es am besten dienstags oder donnerstags.", "category": "attractions", "city": "paris"},
            {"id": 4, "content": "Die Champs-Élysées ist eine der berühmtesten Straßen der Welt. Perfekt für Shopping und Menschenbeobachtung.", "category": "attractions", "city": "paris"},
            {"id": 5, "content": "London ist die Hauptstadt Englands mit Sehenswürdigkeiten wie Big Ben, Tower Bridge und Buckingham Palace. Das Wetter ist oft regnerisch.", "category": "city_info", "city": "london"},
            {"id": 6, "content": "In London sollten Sie das London Eye, Westminster Abbey und die Tower of London besuchen. Nutzen Sie die U-Bahn für Transport.", "category": "travel_tips", "city": "london"},
            {"id": 7, "content": "Der Big Ben ist das Wahrzeichen Londons. Die beste Zeit für Fotos ist bei Sonnenuntergang.", "category": "attractions", "city": "london"},
            {"id": 8, "content": "Die Tower Bridge ist eine der berühmtesten Brücken der Welt. Besuchen Sie das Museum im Inneren der Brücke.", "category": "attractions", "city": "london"},
            {"id": 9, "content": "Rom ist die Hauptstadt Italiens mit dem Kolosseum, Vatikan und Trevi-Brunnen. Die beste Reisezeit ist im Frühling oder Herbst.", "category": "city_info", "city": "rom"},
            {"id": 10, "content": "Rom ist am besten zu Fuß zu erkunden. Besuchen Sie das Kolosseum mit Führung und reservieren Sie für den Vatikan im Voraus.", "category": "travel_tips", "city": "rom"},
            {"id": 11, "content": "Das Kolosseum ist das größte antike Amphitheater. Kaufen Sie Skip-the-Line Tickets online.", "category": "attractions", "city": "rom"},
            {"id": 12, "content": "Der Vatikan ist der kleinste Staat der Welt. Besuchen Sie die Sixtinische Kapelle und den Petersdom.", "category": "attractions", "city": "rom"},
            {"id": 13, "content": "Berlin ist die Hauptstadt Deutschlands und bekannt für das Brandenburger Tor, die Berliner Mauer und die Museumsinsel.", "category": "city_info", "city": "berlin"},
            {"id": 14, "content": "Das Brandenburger Tor ist das Wahrzeichen Berlins. Besuchen Sie es am besten bei Sonnenuntergang.", "category": "attractions", "city": "berlin"},
            {"id": 15, "content": "Die Museumsinsel ist UNESCO-Weltkulturerbe. Besuchen Sie das Pergamonmuseum und das Neue Museum.", "category": "attractions", "city": "berlin"},
            {"id": 16, "content": "Amsterdam ist die Hauptstadt der Niederlande und bekannt für seine Grachten, das Van Gogh Museum und das Anne Frank Haus.", "category": "city_info", "city": "amsterdam"},
            {"id": 17, "content": "Die Grachten von Amsterdam sind UNESCO-Weltkulturerbe. Machen Sie eine Bootstour durch die historische Innenstadt.", "category": "attractions", "city": "amsterdam"},
            {"id": 18, "content": "Das Van Gogh Museum beherbergt die größte Van Gogh Sammlung der Welt. Kaufen Sie Tickets online.", "category": "attractions", "city": "amsterdam"},
            {"id": 23, "content": "Wien ist die Hauptstadt Österreichs und bekannt für seine kaiserliche Geschichte, klassische Musik und prächtige Architektur.", "category": "city_info", "city": "wien"},
            {"id": 24, "content": "Wien ist die Stadt der Musik - besuchen Sie die Wiener Staatsoper, das Musikverein und das Haus der Musik.", "category": "attractions", "city": "wien"},
            {"id": 25, "content": "Der Stephansdom ist das Wahrzeichen Wiens. Besteigen Sie den Südturm für einen atemberaubenden Blick über die Stadt.", "category": "attractions", "city": "wien"},
            {"id": 26, "content": "Das Schloss Schönbrunn ist die ehemalige Sommerresidenz der Habsburger. Besuchen Sie die prächtigen Gärten und das Schloss.", "category": "attractions", "city": "wien"},
            {"id": 27, "content": "Die Hofburg war die Winterresidenz der Habsburger. Besuchen Sie die Kaiserappartements und die Schatzkammer.", "category": "attractions", "city": "wien"},
            {"id": 28, "content": "In Wien sollten Sie mindestens 3-4 Tage verbringen. Nutzen Sie die U-Bahn und Straßenbahnen für Transport.", "category": "travel_tips", "city": "wien"},
            {"id": 29, "content": "Genießen Sie Wiener Kaffeehauskultur in Cafés wie dem Café Central oder dem Café Sacher.", "category": "travel_tips", "city": "wien"},
            {"id": 30, "content": "Barcelona ist die Hauptstadt Kataloniens und bekannt für die Sagrada Familia, Park Güell und die Ramblas.", "category": "city_info", "city": "barcelona"},
            {"id": 31, "content": "Die Sagrada Familia ist Gaudís Meisterwerk. Kaufen Sie Tickets online und besuchen Sie es am besten morgens.", "category": "attractions", "city": "barcelona"},
            {"id": 32, "content": "Park Güell ist ein fantastischer Park mit Gaudís Architektur. Besuchen Sie ihn am besten am Nachmittag.", "category": "attractions", "city": "barcelona"},
            {"id": 33, "content": "Die Ramblas ist die berühmteste Straße Barcelonas. Seien Sie vorsichtig mit Taschendieben.", "category": "attractions", "city": "barcelona"},
            {"id": 34, "content": "Kopenhagen ist die Hauptstadt Dänemarks und bekannt für die Kleine Meerjungfrau, Nyhavn und Tivoli.", "category": "city_info", "city": "kopenhagen"},
            {"id": 35, "content": "Nyhavn ist der malerische Hafen Kopenhagens mit bunten Häusern und Restaurants.", "category": "attractions", "city": "kopenhagen"},
            {"id": 36, "content": "Tivoli ist der zweitälteste Vergnügungspark der Welt. Besuchen Sie ihn am besten abends für die Beleuchtung.", "category": "attractions", "city": "kopenhagen"},
            {"id": 19, "content": "Buchen Sie Flüge und Hotels mindestens 3 Monate im Voraus für die besten Preise.", "category": "general_tips", "city": "general"},
            {"id": 20, "content": "Nutzen Sie öffentliche Verkehrsmittel in europäischen Städten - sie sind oft günstiger und schneller als Taxis.", "category": "general_tips", "city": "general"},
            {"id": 21, "content": "Besuchen Sie beliebte Sehenswürdigkeiten früh morgens oder spät abends, um Menschenmassen zu vermeiden.", "category": "general_tips", "city": "general"},
            {"id": 22, "content": "Laden Sie Offline-Karten herunter und lernen Sie ein paar grundlegende Sätze in der Landessprache.", "category": "general_tips", "city": "general"}
        ]
        
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self._build_vector_index()
    
    def _build_vector_index(self):
        documents = [doc["content"] for doc in self.travel_knowledge]
        self.vectors = self.vectorizer.fit_transform(documents)
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.vectors).flatten()
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:
                doc = self.travel_knowledge[idx].copy()
                doc["similarity"] = float(similarities[idx])
                results.append(doc)
        
        return results
    
    def get_city_info(self, city: str) -> List[Dict[str, Any]]:
        city_lower = city.lower()
        return [doc for doc in self.travel_knowledge if doc["city"] == city_lower]
    
    def get_travel_tips(self, city: str = None) -> List[Dict[str, Any]]:
        return [doc for doc in self.travel_knowledge if doc["category"] == "travel_tips" and (city is None or doc["city"] == city.lower())]
    
    def answer_question(self, question: str, city: str = None) -> str:
        relevant_docs = self.search(question, top_k=2)
        
        if not relevant_docs:
            return "Entschuldigung, ich habe keine relevanten Informationen zu Ihrer Frage gefunden."
        
        if city:
            city_docs = [doc for doc in relevant_docs if doc["city"] == city.lower()]
            if city_docs:
                relevant_docs = city_docs
        
        return " ".join([doc["content"] for doc in relevant_docs]) 