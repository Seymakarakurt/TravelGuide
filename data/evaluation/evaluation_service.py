import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class ResponseQualityMetrics:
    relevance_score: float
    completeness_score: float
    accuracy_score: float
    helpfulness_score: float
    coherence_score: float
    overall_quality: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class UserFeedback:
    rating: int
    helpful: bool
    follow_up_needed: bool
    specific_feedback: str
    timestamp: str

@dataclass
class IntentEvaluation:
    detected_intent: str
    confidence_score: float
    expected_intent: Optional[str] = None
    intent_correct: Optional[bool] = None
    entity_extraction_accuracy: float = 0.0
    context_understanding: float = 0.0

class ResponseQualityEvaluator:
    
    def __init__(self):
        self.quality_keywords = {
            'relevance': ['relevant', 'passend', 'angemessen', 'zutreffend'],
            'completeness': ['vollständig', 'umfassend', 'detailliert', 'ausführlich'],
            'accuracy': ['korrekt', 'genau', 'präzise', 'zuverlässig'],
            'helpfulness': ['hilfreich', 'nützlich', 'praktisch', 'brauchbar'],
            'coherence': ['logisch', 'verständlich', 'klar', 'strukturiert']
        }
    
    def evaluate_response_quality(self, user_message: str, response: Dict[str, Any]) -> ResponseQualityMetrics:
        response_text = self._extract_response_text(response)
        
        relevance_score = self._calculate_relevance_score(user_message, response_text)
        completeness_score = self._calculate_completeness_score(response)
        accuracy_score = self._calculate_accuracy_score(response)
        helpfulness_score = self._calculate_helpfulness_score(response)
        coherence_score = self._calculate_coherence_score(response_text)
        
        overall_quality = np.mean([
            relevance_score, completeness_score, accuracy_score, 
            helpfulness_score, coherence_score
        ])
        
        return ResponseQualityMetrics(
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            helpfulness_score=helpfulness_score,
            coherence_score=coherence_score,
            overall_quality=overall_quality
        )
    
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        if isinstance(response, dict):
            if 'message' in response:
                return str(response['message'])
            elif 'response' in response:
                return str(response['response'])
            else:
                return str(response)
        return str(response)
    
    def _calculate_relevance_score(self, user_message: str, response_text: str) -> float:
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
            vectors = vectorizer.fit_transform([user_message, response_text])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            keyword_overlap = self._calculate_keyword_overlap(user_message, response_text)
            
            relevance_score = (similarity * 0.7) + (keyword_overlap * 0.3)
            return min(1.0, max(0.0, relevance_score))
            
        except Exception:
            return 0.5
    
    def _calculate_keyword_overlap(self, message: str, response: str) -> float:
        message_words = set(re.findall(r'\b\w+\b', message.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        if not message_words:
            return 0.0
        
        overlap = len(message_words.intersection(response_words))
        return min(1.0, overlap / len(message_words))
    
    def _calculate_completeness_score(self, response: Dict[str, Any]) -> float:
        score = 0.5
        
        if isinstance(response, dict):
            if 'message' in response and response['message']:
                score += 0.2
            
            if 'suggestions' in response and response['suggestions']:
                score += 0.15
            
            if 'data' in response or 'results' in response:
                score += 0.15
            
            if 'type' in response and response['type'] != 'error':
                score += 0.1
        
        return min(1.0, score)
    
    def _calculate_accuracy_score(self, response: Dict[str, Any]) -> float:
        score = 0.5
        
        if isinstance(response, dict):
            if response.get('type') != 'error':
                score += 0.3
            
            if 'data' in response or 'results' in response:
                score += 0.2
            
            message = response.get('message', '')
            if message and len(message) > 50:
                score += 0.1
        
        return min(1.0, score)
    
    def _calculate_helpfulness_score(self, response: Dict[str, Any]) -> float:
        score = 0.5
        
        if isinstance(response, dict):
            if 'suggestions' in response and response['suggestions']:
                score += 0.2
            
            message = response.get('message', '')
            action_words = ['können', 'sollten', 'empfehle', 'buchen', 'besuchen', 'planen']
            if any(word in message.lower() for word in action_words):
                score += 0.15
            
            if 'data' in response or 'results' in response:
                score += 0.15
        
        return min(1.0, score)
    
    def _calculate_coherence_score(self, response_text: str) -> float:
        if not response_text:
            return 0.0
        
        score = 0.5
        
        sentences = re.split(r'[.!?]+', response_text)
        if len(sentences) > 1:
            score += 0.2
        
        logical_connectors = ['daher', 'deshalb', 'außerdem', 'zudem', 'jedoch', 'aber', 'und', 'oder']
        if any(connector in response_text.lower() for connector in logical_connectors):
            score += 0.15
        
        if any(char in response_text for char in ['•', '-', '*', '1.', '2.', '3.']):
            score += 0.15
        
        return min(1.0, score)

class UserFeedbackCollector:
    
    def __init__(self, feedback_file: str = 'data/evaluation/user_feedback.json'):
        self.feedback_file = feedback_file
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> Dict[str, Any]:
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'feedback_entries': [], 'statistics': {}}
    
    def save_feedback(self, user_id: str, interaction_id: str, feedback: UserFeedback):
        feedback_entry = {
            'user_id': user_id,
            'interaction_id': interaction_id,
            'feedback': asdict(feedback)
        }
        
        self.feedback_data['feedback_entries'].append(feedback_entry)
        self._update_statistics()
        self._save_to_file()
    
    def _update_statistics(self):
        entries = self.feedback_data['feedback_entries']
        
        if not entries:
            return
        
        ratings = [entry['feedback']['rating'] for entry in entries]
        helpful_count = sum(1 for entry in entries if entry['feedback']['helpful'])
        follow_up_count = sum(1 for entry in entries if entry['feedback']['follow_up_needed'])
        
        self.feedback_data['statistics'] = {
            'total_feedback': len(entries),
            'average_rating': np.mean(ratings),
            'helpful_percentage': (helpful_count / len(entries)) * 100,
            'follow_up_percentage': (follow_up_count / len(entries)) * 100,
            'rating_distribution': {
                '1_star': ratings.count(1),
                '2_star': ratings.count(2),
                '3_star': ratings.count(3),
                '4_star': ratings.count(4),
                '5_star': ratings.count(5)
            }
        }
    
    def _save_to_file(self):
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_data, f, indent=2, ensure_ascii=False)
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        return self.feedback_data.get('statistics', {})

class IntentEvaluator:
    
    def __init__(self):
        self.intent_patterns = {
            'weather_query': [r'wetter', r'temperatur', r'regnet', r'sonne', r'klima'],
            'hotel_search': [r'hotel', r'unterkunft', r'buchen', r'zimmer', r'übernachtung'],
            'attraction_search': [r'sehenswürdigkeit', r'attraktion', r'museum', r'denkmal', r'besichtigen'],
            'travel_planning': [r'planen', r'reise', r'urlaub', r'trip', r'route'],
            'general_inquiry': [r'was', r'wie', r'wo', r'wann', r'kann']
        }
    
    def evaluate_intent_recognition(self, user_message: str, detected_intent: str, 
                                  confidence: float, expected_intent: Optional[str] = None) -> IntentEvaluation:
        intent_correct = None
        if expected_intent:
            intent_correct = detected_intent == expected_intent
        
        entity_accuracy = self._evaluate_entity_extraction(user_message)
        context_understanding = self._evaluate_context_understanding(user_message, detected_intent)
        
        return IntentEvaluation(
            detected_intent=detected_intent,
            confidence_score=confidence,
            expected_intent=expected_intent,
            intent_correct=intent_correct,
            entity_extraction_accuracy=entity_accuracy,
            context_understanding=context_understanding
        )
    
    def _evaluate_entity_extraction(self, message: str) -> float:
        entities_found = 0
        total_entities = 0
        
        city_patterns = [r'\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*\b']
        for pattern in city_patterns:
            matches = re.findall(pattern, message)
            total_entities += len(matches)
            entities_found += len(matches)
        
        number_patterns = [r'\d+', r'\d+\.\d+']
        for pattern in number_patterns:
            matches = re.findall(pattern, message)
            total_entities += len(matches)
            entities_found += len(matches)
        
        if total_entities == 0:
            return 0.5
        
        return min(1.0, entities_found / total_entities)
    
    def _evaluate_context_understanding(self, message: str, detected_intent: str) -> float:
        score = 0.5
        
        if detected_intent in self.intent_patterns:
            patterns = self.intent_patterns[detected_intent]
            matches = sum(1 for pattern in patterns if re.search(pattern, message.lower()))
            if matches > 0:
                score += 0.3
        
        context_indicators = ['jetzt', 'heute', 'morgen', 'nächste', 'letzte', 'während']
        if any(indicator in message.lower() for indicator in context_indicators):
            score += 0.2
        
        return min(1.0, score)

class EvaluationService:
    
    def __init__(self, metrics_file: str = 'data/evaluation/metrics.json'):
        self.metrics_file = metrics_file
        self.quality_evaluator = ResponseQualityEvaluator()
        self.feedback_collector = UserFeedbackCollector()
        self.intent_evaluator = IntentEvaluator()
        self.metrics_data = self._load_metrics()
    
    def _load_metrics(self) -> Dict[str, Any]:
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'interactions': [],
                'evaluation_summary': {},
                'last_updated': datetime.now().isoformat()
            }
    
    def evaluate_interaction(self, user_message: str, response: Dict[str, Any], 
                           user_id: str, response_time: float, response_type: str,
                           intent_recognized: bool, api_success: bool,
                           detected_intent: str = '', confidence: float = 0.0) -> Dict[str, Any]:
        quality_metrics = self.quality_evaluator.evaluate_response_quality(user_message, response)
        intent_evaluation = self.intent_evaluator.evaluate_intent_recognition(
            user_message, detected_intent, confidence
        )
        
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'message': user_message,
            'response_type': response_type,
            'response_time': response_time,
            'response_quality': quality_metrics.to_dict(),
            'user_feedback': None,
            'intent_recognized': intent_recognized,
            'intent_evaluation': asdict(intent_evaluation),
            'api_success': api_success,
            'interaction_id': f"{user_id}_{int(time.time())}"
        }
        
        self.metrics_data['interactions'].append(interaction)
        self._update_evaluation_summary()
        self._save_metrics()
        
        return interaction
    
    def add_user_feedback(self, interaction_id: str, user_id: str, 
                         rating: int, helpful: bool, follow_up_needed: bool, 
                         specific_feedback: str = ""):
        feedback = UserFeedback(
            rating=rating,
            helpful=helpful,
            follow_up_needed=follow_up_needed,
            specific_feedback=specific_feedback,
            timestamp=datetime.now().isoformat()
        )
        
        self.feedback_collector.save_feedback(user_id, interaction_id, feedback)
        
        for interaction in self.metrics_data['interactions']:
            if interaction.get('interaction_id') == interaction_id:
                interaction['user_feedback'] = asdict(feedback)
                break
        
        self._update_evaluation_summary()
        self._save_metrics()
    
    def _update_evaluation_summary(self):
        interactions = self.metrics_data['interactions']
        
        if not interactions:
            return
        
        response_times = [i['response_time'] for i in interactions]
        quality_scores = [i['response_quality']['overall_quality'] for i in interactions if i['response_quality']]
        intent_confidences = [i['intent_evaluation']['confidence_score'] for i in interactions if i['intent_evaluation']]
        
        api_success_count = sum(1 for i in interactions if i['api_success'])
        api_success_rate = (api_success_count / len(interactions)) * 100
        
        intent_recognized_count = sum(1 for i in interactions if i['intent_recognized'])
        intent_recognition_rate = (intent_recognized_count / len(interactions)) * 100
        
        feedback_stats = self.feedback_collector.get_feedback_statistics()
        
        self.metrics_data['evaluation_summary'] = {
            'total_interactions': len(interactions),
            'average_response_time': np.mean(response_times) if response_times else 0,
            'average_quality_score': np.mean(quality_scores) if quality_scores else 0,
            'average_intent_confidence': np.mean(intent_confidences) if intent_confidences else 0,
            'api_success_rate': api_success_rate,
            'intent_recognition_rate': intent_recognition_rate,
            'feedback_statistics': feedback_stats,
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_metrics(self):
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics_data, f, indent=2, ensure_ascii=False)
    
    def get_evaluation_report(self) -> Dict[str, Any]:
        return {
            'metrics': self.metrics_data,
            'feedback_stats': self.feedback_collector.get_feedback_statistics(),
            'summary': self.metrics_data.get('evaluation_summary', {})
        }
    
    def get_quality_insights(self) -> Dict[str, Any]:
        interactions = self.metrics_data['interactions']
        
        if not interactions:
            return {}
        
        quality_scores = [i['response_quality'] for i in interactions if i['response_quality']]
        
        if not quality_scores:
            return {}
        
        dimensions = ['relevance_score', 'completeness_score', 'accuracy_score', 
                     'helpfulness_score', 'coherence_score']
        
        insights = {}
        for dimension in dimensions:
            scores = [qs[dimension] for qs in quality_scores if dimension in qs]
            if scores:
                insights[dimension] = {
                    'average': np.mean(scores),
                    'min': np.min(scores),
                    'max': np.max(scores),
                    'std': np.std(scores)
                }
        
        return insights 