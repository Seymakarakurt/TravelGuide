import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class EvaluationService:
    def __init__(self):
        self.metrics_file = "evaluation/metrics.json"
        self.feedback_file = "evaluation/user_feedback.json"
        self.quality_thresholds = {
            "relevance": 0.7,
            "completeness": 0.6,
            "accuracy": 0.8,
            "helpfulness": 0.7,
            "coherence": 0.6
        }
        
        # Lade bestehende Metriken
        self.metrics = self._load_metrics()
        self.user_feedback = self._load_user_feedback()
        
    def evaluate_response_quality(self, user_message: str, response: Dict[str, Any], 
                                response_time: float, api_success: bool) -> Dict[str, Any]:
        
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "response_type": response.get("type", "unknown"),
            "response_time": response_time,
            "api_success": api_success,
            "quality_scores": {},
            "overall_score": 0.0,
            "improvement_suggestions": []
        }
        
        relevance_score = self._evaluate_relevance(user_message, response)
        evaluation["quality_scores"]["relevance"] = relevance_score
        
        completeness_score = self._evaluate_completeness(response)
        evaluation["quality_scores"]["completeness"] = completeness_score
        
        accuracy_score = self._evaluate_accuracy(response)
        evaluation["quality_scores"]["accuracy"] = accuracy_score
        
        helpfulness_score = self._evaluate_helpfulness(response)
        evaluation["quality_scores"]["helpfulness"] = helpfulness_score
        
        coherence_score = self._evaluate_coherence(response)
        evaluation["quality_scores"]["coherence"] = coherence_score
        
        evaluation["overall_score"] = np.mean(list(evaluation["quality_scores"].values()))
        
        evaluation["improvement_suggestions"] = self._generate_improvement_suggestions(evaluation["quality_scores"])
        
        self._save_evaluation(evaluation)
        
        return evaluation
    
    def collect_user_feedback(self, user_id: str, response_id: str, rating: int, 
                            feedback_type: str, additional_feedback: str = "") -> Dict[str, Any]:
        
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "response_id": response_id,
            "rating": rating,
            "feedback_type": feedback_type,
            "additional_feedback": additional_feedback
        }
        
        if "feedback" not in self.user_feedback:
            self.user_feedback["feedback"] = []
        
        self.user_feedback["feedback"].append(feedback)
        self._save_user_feedback()
        
        return feedback
    
    def evaluate_intent_recognition(self, user_message: str, detected_intent: str, 
                                  confidence: float, entities: Dict[str, Any]) -> Dict[str, Any]:
        
        intent_evaluation = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "detected_intent": detected_intent,
            "confidence": confidence,
            "entities": entities,
            "intent_accuracy": 0.0,
            "entity_accuracy": 0.0,
            "context_understanding": 0.0
        }
        
        intent_accuracy = self._evaluate_intent_accuracy(user_message, detected_intent)
        intent_evaluation["intent_accuracy"] = intent_accuracy
        
        entity_accuracy = self._evaluate_entity_accuracy(user_message, entities)
        intent_evaluation["entity_accuracy"] = entity_accuracy
        
        context_understanding = self._evaluate_context_understanding(user_message, detected_intent, entities)
        intent_evaluation["context_understanding"] = context_understanding
        
        if "intent_evaluations" not in self.metrics:
            self.metrics["intent_evaluations"] = []
        
        self.metrics["intent_evaluations"].append(intent_evaluation)
        self._save_metrics()
        
        return intent_evaluation
    
    def track_performance_metrics(self, response_time: float, api_calls: int, 
                                api_success_rate: float, tool_used: str = None) -> Dict[str, Any]:
        
        performance = {
            "timestamp": datetime.now().isoformat(),
            "response_time": response_time,
            "api_calls": api_calls,
            "api_success_rate": api_success_rate,
            "tool_used": tool_used
        }
        
        if "performance_metrics" not in self.metrics:
            self.metrics["performance_metrics"] = []
        
        self.metrics["performance_metrics"].append(performance)
        self._save_metrics()
        
        return performance
    
    def generate_evaluation_report(self) -> Dict[str, Any]:
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self._calculate_overall_metrics(),
            "feedback_stats": self._calculate_feedback_statistics(),
            "quality_dimensions": self._calculate_quality_dimensions(),
            "performance_trends": self._calculate_performance_trends(),
            "improvement_recommendations": self._generate_improvement_recommendations()
        }
        
        return report
    
    def _evaluate_relevance(self, user_message: str, response: Dict[str, Any]) -> float:
        
        response_message = response.get("message", "")
        if not response_message:
            return 0.0
        
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
            tfidf_matrix = vectorizer.fit_transform([user_message, response_message])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            similarity = 0.0
        
        user_keywords = set(re.findall(r'\b\w+\b', user_message.lower()))
        response_keywords = set(re.findall(r'\b\w+\b', response_message.lower()))
        
        if user_keywords:
            keyword_overlap = len(user_keywords.intersection(response_keywords)) / len(user_keywords)
        else:
            keyword_overlap = 0.0
        
        relevance_score = (similarity * 0.7) + (keyword_overlap * 0.3)
        
        return min(1.0, max(0.0, relevance_score))
    
    def _evaluate_completeness(self, response: Dict[str, Any]) -> float:
        
        response_message = response.get("message", "")
        response_type = response.get("type", "")
        
        completeness = 0.5
        
        if len(response_message) > 50:
            completeness += 0.2
        
        if response_type in ["mcp_response", "tool_response"]:
            completeness += 0.2
        
        if any(keyword in response_message.lower() for keyword in ["hotel", "wetter", "sehenswürdigkeit", "preis", "temperatur"]):
            completeness += 0.1
        
        return min(1.0, completeness)
    
    def _evaluate_accuracy(self, response: Dict[str, Any]) -> float:
        
        response_type = response.get("type", "")
        api_success = response.get("api_success", True)
        
        accuracy = 0.5
        
        if api_success:
            accuracy += 0.3
        
        if response_type in ["mcp_response", "tool_response"]:
            accuracy += 0.2
        
        return min(1.0, accuracy)
    
    def _evaluate_helpfulness(self, response: Dict[str, Any]) -> float:
        
        response_message = response.get("message", "")
        suggestions = response.get("suggestions", [])
        
        helpfulness = 0.4
        
        action_words = ["finden", "buchen", "besuchen", "sehen", "gehen", "nehmen"]
        if any(word in response_message.lower() for word in action_words):
            helpfulness += 0.3
        
        if suggestions:
            helpfulness += 0.2
        
        if "fehler" not in response_message.lower() and "entschuldigung" not in response_message.lower():
            helpfulness += 0.1
        
        return min(1.0, helpfulness)
    
    def _evaluate_coherence(self, response: Dict[str, Any]) -> float:
        
        response_message = response.get("message", "")
        
        coherence = 0.5
        
        sentences = response_message.split('.')
        if len(sentences) > 1:
            coherence += 0.2
        
        if any(word in response_message.lower() for word in ["weil", "da", "daher", "deshalb", "außerdem"]):
            coherence += 0.2
        
        if not any(word in response_message.lower() for word in ["aber", "jedoch", "allerdings", "trotzdem"]):
            coherence += 0.1
        
        return min(1.0, coherence)
    
    def _evaluate_intent_accuracy(self, user_message: str, detected_intent: str) -> float:
        
        message_lower = user_message.lower()
        
        intent_keywords = {
            "hotel_search": ["hotel", "unterkunft", "übernachtung", "zimmer"],
            "weather_query": ["wetter", "temperatur", "regen", "sonne"],
            "attractions_search": ["sehenswürdigkeit", "attraktion", "museum", "denkmal"]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if detected_intent == intent:
                    return 1.0
                else:
                    return 0.3
        
        return 0.5
    
    def _evaluate_entity_accuracy(self, user_message: str, entities: Dict[str, Any]) -> float:
        
        location_entities = entities.get("location", [])
        
        if location_entities:
            return 0.8
        else:
            known_cities = ["berlin", "münchen", "hamburg", "köln", "frankfurt", "paris", "london", "rom", "amsterdam"]
            if any(city in user_message.lower() for city in known_cities):
                return 0.3
        
        return 0.5
    
    def _evaluate_context_understanding(self, user_message: str, detected_intent: str, entities: Dict[str, Any]) -> float:
        
        intent_score = self._evaluate_intent_accuracy(user_message, detected_intent)
        entity_score = self._evaluate_entity_accuracy(user_message, entities)
        
        return (intent_score + entity_score) / 2
    
    def _generate_improvement_suggestions(self, quality_scores: Dict[str, float]) -> List[str]:
        
        suggestions = []
        
        for dimension, score in quality_scores.items():
            if score < self.quality_thresholds.get(dimension, 0.7):
                if dimension == "relevance":
                    suggestions.append("Antwort sollte relevanter zur ursprünglichen Frage sein")
                elif dimension == "completeness":
                    suggestions.append("Antwort sollte vollständigere Informationen enthalten")
                elif dimension == "accuracy":
                    suggestions.append("Antwort sollte genauer und fehlerfreier sein")
                elif dimension == "helpfulness":
                    suggestions.append("Antwort sollte handlungsorientierter sein")
                elif dimension == "coherence":
                    suggestions.append("Antwort sollte kohärenter und verständlicher sein")
        
        return suggestions
    
    def _calculate_overall_metrics(self) -> Dict[str, Any]:
        
        if "evaluations" not in self.metrics:
            return {}
        
        evaluations = self.metrics["evaluations"]
        if not evaluations:
            return {}
        
        total_interactions = len(evaluations)
        avg_response_time = np.mean([e.get("response_time", 0) for e in evaluations])
        avg_quality_score = np.mean([e.get("overall_score", 0) for e in evaluations])
        
        api_successes = sum(1 for e in evaluations if e.get("api_success", False))
        api_success_rate = (api_successes / total_interactions) * 100 if total_interactions > 0 else 0
        
        intent_evaluations = self.metrics.get("intent_evaluations", [])
        if intent_evaluations:
            avg_intent_accuracy = np.mean([e.get("intent_accuracy", 0) for e in intent_evaluations])
        else:
            avg_intent_accuracy = 0.0
        
        return {
            "total_interactions": total_interactions,
            "average_response_time": round(avg_response_time, 2),
            "average_quality_score": round(avg_quality_score, 2),
            "api_success_rate": round(api_success_rate, 1),
            "intent_recognition_rate": round(avg_intent_accuracy * 100, 1)
        }
    
    def _calculate_feedback_statistics(self) -> Dict[str, Any]:
        
        feedback_list = self.user_feedback.get("feedback", [])
        if not feedback_list:
            return {}
        
        total_feedback = len(feedback_list)
        avg_rating = np.mean([f.get("rating", 0) for f in feedback_list])
        
        helpful_count = sum(1 for f in feedback_list if f.get("feedback_type") == "helpful")
        helpful_percentage = (helpful_count / total_feedback) * 100 if total_feedback > 0 else 0
        
        return {
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 1),
            "helpful_percentage": round(helpful_percentage, 1)
        }
    
    def _calculate_quality_dimensions(self) -> Dict[str, float]:
        
        if "evaluations" not in self.metrics:
            return {}
        
        evaluations = self.metrics["evaluations"]
        if not evaluations:
            return {}
        
        dimensions = ["relevance", "completeness", "accuracy", "helpfulness", "coherence"]
        quality_dimensions = {}
        
        for dimension in dimensions:
            scores = [e.get("quality_scores", {}).get(dimension, 0) for e in evaluations]
            if scores:
                quality_dimensions[f"{dimension}_score"] = round(np.mean(scores), 2)
        
        return quality_dimensions
    
    def _calculate_performance_trends(self) -> Dict[str, Any]:
        
        performance_metrics = self.metrics.get("performance_metrics", [])
        if not performance_metrics:
            return {}
        
        recent_metrics = performance_metrics[-10:]
        
        avg_response_time = np.mean([m.get("response_time", 0) for m in recent_metrics])
        avg_api_success_rate = np.mean([m.get("api_success_rate", 0) for m in recent_metrics])
        
        return {
            "recent_avg_response_time": round(avg_response_time, 2),
            "recent_avg_api_success_rate": round(avg_api_success_rate, 1)
        }
    
    def _generate_improvement_recommendations(self) -> List[str]:
        
        recommendations = []
        
        quality_dimensions = self._calculate_quality_dimensions()
        
        for dimension, score in quality_dimensions.items():
            if score < 0.7:
                if "relevance" in dimension:
                    recommendations.append("Verbessere Relevanz der Antworten durch bessere Intent-Erkennung")
                elif "completeness" in dimension:
                    recommendations.append("Erweitere Antworten um mehr Details und Kontext")
                elif "accuracy" in dimension:
                    recommendations.append("Überprüfe API-Integration und Datenqualität")
                elif "helpfulness" in dimension:
                    recommendations.append("Füge mehr handlungsorientierte Vorschläge hinzu")
                elif "coherence" in dimension:
                    recommendations.append("Verbessere die logische Struktur der Antworten")
        
        return recommendations
    
    def _save_evaluation(self, evaluation: Dict[str, Any]):
        
        if "evaluations" not in self.metrics:
            self.metrics["evaluations"] = []
        
        self.metrics["evaluations"].append(evaluation)
        self._save_metrics()
    
    def _save_metrics(self):
        
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Fehler beim Speichern der Metriken: {e}")
    
    def _save_user_feedback(self):
        
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_feedback, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Fehler beim Speichern des User-Feedbacks: {e}")
    
    def _load_metrics(self) -> Dict[str, Any]:
        
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Fehler beim Laden der Metriken: {e}")
            return {}
    
    def _load_user_feedback(self) -> Dict[str, Any]:
        
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Fehler beim Laden des User-Feedbacks: {e}")
            return {} 