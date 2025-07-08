import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
from api_services import ai_service

class EvaluationSystem:
    def __init__(self, metrics_file: str = "evaluation/metrics.json"):
        self.metrics_file = metrics_file
        self.metrics = self._load_metrics()
        
    def _load_metrics(self) -> Dict[str, Any]:
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "interactions": [],
                "evaluation_config": {
                    "quality_thresholds": {
                        "excellent": 0.9,
                        "good": 0.7,
                        "acceptable": 0.5,
                        "poor": 0.3
                    },
                    "response_time_thresholds": {
                        "fast": 1.0,
                        "normal": 3.0,
                        "slow": 5.0
                    }
                },
                "aggregated_metrics": {
                    "total_interactions": 0,
                    "average_response_quality": 0.0,
                    "average_response_time": 0.0,
                    "user_satisfaction_rate": 0.0,
                    "intent_recognition_rate": 0.0,
                    "api_success_rate": 0.0
                },
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_metrics(self):
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)
    
    def evaluate_response_quality(self, message: str, response: Dict[str, Any], response_time: float) -> Dict[str, Any]:
        quality_score = 0.0
        quality_factors = {}
        
        relevance_score = self._evaluate_relevance(message, response)
        quality_factors['relevance'] = relevance_score
        quality_score += relevance_score * 0.25
        
        completeness_score = self._evaluate_completeness(response)
        quality_factors['completeness'] = completeness_score
        quality_score += completeness_score * 0.25
        
        time_score = self._evaluate_response_time(response_time)
        quality_factors['response_time'] = time_score
        quality_score += time_score * 0.20
        
        structure_score = self._evaluate_structure(response)
        quality_factors['structure'] = structure_score
        quality_score += structure_score * 0.15
        
        tool_score = self._evaluate_tool_usage(response)
        quality_factors['tool_usage'] = tool_score
        quality_score += tool_score * 0.15
        
        quality_level = self._determine_quality_level(quality_score)
        
        return {
            'score': round(quality_score, 3),
            'level': quality_level,
            'factors': quality_factors,
            'details': self._generate_quality_details(quality_factors, response)
        }
    
    def _evaluate_relevance(self, message: str, response: Dict[str, Any]) -> float:
        message_lower = message.lower()
        response_message = response.get('message', '').lower()
        
        keywords = self._extract_keywords(message_lower)
        
        if not keywords:
            return 0.5
        
        keyword_matches = sum(1 for keyword in keywords if keyword in response_message)
        relevance_ratio = keyword_matches / len(keywords)
        
        if response.get('type') in ['weather_results', 'hotel_results', 'tool_response']:
            relevance_ratio = min(1.0, relevance_ratio + 0.2)
        
        return min(1.0, relevance_ratio)
    
    def _evaluate_completeness(self, response: Dict[str, Any]) -> float:
        response_message = response.get('message', '')
        
        if not response_message:
            return 0.0
        
        if len(response_message) < 20:
            return 0.3
        elif len(response_message) < 50:
            return 0.6
        elif len(response_message) < 100:
            return 0.8
        else:
            return 1.0
        
        response_type = response.get('type', '')
        
        if response_type == 'weather_results':
            if 'temperatur' in response_message.lower() or 'wetter' in response_message.lower():
                return min(1.0, completeness + 0.2)
        
        elif response_type == 'hotel_results':
            if 'hotel' in response_message.lower() or 'preis' in response_message.lower():
                return min(1.0, completeness + 0.2)
        
        return completeness
    
    def _evaluate_response_time(self, response_time: float) -> float:
        thresholds = self.metrics.get('evaluation_config', {}).get('response_time_thresholds', {
            'fast': 1.0,
            'normal': 3.0,
            'slow': 5.0
        })
        
        if response_time <= thresholds['fast']:
            return 1.0
        elif response_time <= thresholds['normal']:
            return 0.8
        elif response_time <= thresholds['slow']:
            return 0.5
        else:
            return 0.2
    
    def _evaluate_structure(self, response: Dict[str, Any]) -> float:
        response_message = response.get('message', '')
        
        if not response_message:
            return 0.0
        
        structure_score = 0.5
        
        if '\n\n' in response_message:
            structure_score += 0.2
        
        if any(char in response_message for char in ['•', '-', '*', '1.', '2.', '3.']):
            structure_score += 0.2
        
        emoji_count = len(re.findall(r'[🏛️💡🌤️🏨📄]', response_message))
        if emoji_count > 0:
            structure_score += min(0.1, emoji_count * 0.05)
        
        return min(1.0, structure_score)
    
    def _evaluate_tool_usage(self, response: Dict[str, Any]) -> float:
        response_type = response.get('type', '')
        
        if response_type in ['tool_response', 'weather_results', 'hotel_results', 'rag_response']:
            return 1.0
        elif response_type == 'general':
            return 0.7
        elif response_type == 'error':
            return 0.3
        else:
            return 0.5
    
    def _determine_quality_level(self, score: float) -> str:
        thresholds = self.metrics.get('evaluation_config', {}).get('quality_thresholds', {
            'excellent': 0.9,
            'good': 0.7,
            'acceptable': 0.5,
            'poor': 0.3
        })
        
        if score >= thresholds['excellent']:
            return 'excellent'
        elif score >= thresholds['good']:
            return 'good'
        elif score >= thresholds['acceptable']:
            return 'acceptable'
        elif score >= thresholds['poor']:
            return 'poor'
        else:
            return 'very_poor'
    
    def _extract_keywords(self, message: str) -> List[str]:
        stop_words = {'und', 'oder', 'aber', 'für', 'mit', 'nach', 'zu', 'in', 'auf', 'an', 'bei', 'von', 'aus', 'durch', 'ohne', 'gegen', 'um', 'bis', 'seit', 'während', 'trotz', 'wegen', 'statt', 'außer', 'neben', 'zwischen', 'hinter', 'vor', 'über', 'unter', 'neben', 'entlang', 'gegenüber', 'jenseits', 'diesseits', 'oberhalb', 'unterhalb', 'innerhalb', 'außerhalb', 'rechts', 'links', 'oben', 'unten', 'vorne', 'hinten', 'seitlich', 'mittig', 'zentral', 'peripher', 'äußere', 'innere', 'äußerer', 'innerer', 'äußeres', 'inneres', 'äußeren', 'inneren', 'äußerem', 'innerem', 'äußerer', 'innerer', 'äußeres', 'inneres', 'äußeren', 'inneren', 'äußerem', 'innerem'}
        
        message_clean = re.sub(r'[^\w\s]', '', message.lower())
        
        words = [word for word in message_clean.split() if word not in stop_words and len(word) > 2]
        
        return words[:10]
    
    def _generate_quality_details(self, factors: Dict[str, float], response: Dict[str, Any]) -> str:
        details = []
        
        if factors['relevance'] < 0.5:
            details.append("Antwort ist wenig relevant zur Anfrage")
        elif factors['relevance'] > 0.8:
            details.append("Antwort ist sehr relevant zur Anfrage")
        
        if factors['completeness'] < 0.5:
            details.append("Antwort ist unvollständig")
        elif factors['completeness'] > 0.8:
            details.append("Antwort ist vollständig und informativ")
        
        if factors['response_time'] < 0.5:
            details.append("Antwortzeit ist zu lang")
        elif factors['response_time'] > 0.8:
            details.append("Antwortzeit ist optimal")
        
        if factors['structure'] < 0.5:
            details.append("Antwort ist schlecht strukturiert")
        elif factors['structure'] > 0.8:
            details.append("Antwort ist gut strukturiert")
        
        if factors['tool_usage'] > 0.8:
            details.append("Tools wurden effektiv genutzt")
        
        return "; ".join(details) if details else "Antwort erfüllt alle Qualitätskriterien"
    
    def collect_user_feedback(self, user_id: str, interaction_id: str) -> Dict[str, Any]:
        feedback = {
            'rating': self._simulate_user_rating(),
            'satisfaction': self._simulate_satisfaction(),
            'usefulness': self._simulate_usefulness(),
            'comments': self._simulate_comments(),
            'would_recommend': self._simulate_recommendation()
        }
        
        return feedback
    
    def _simulate_user_rating(self) -> int:
        import random
        if random.random() < 0.7:
            return random.randint(4, 5)
        else:
            return random.randint(1, 3)
    
    def _simulate_satisfaction(self) -> str:
        import random
        satisfaction_levels = ['sehr zufrieden', 'zufrieden', 'neutral', 'unzufrieden', 'sehr unzufrieden']
        weights = [0.4, 0.3, 0.2, 0.08, 0.02]
        return random.choices(satisfaction_levels, weights=weights)[0]
    
    def _simulate_usefulness(self) -> str:
        import random
        usefulness_levels = ['sehr nützlich', 'nützlich', 'teilweise nützlich', 'wenig nützlich', 'nicht nützlich']
        weights = [0.35, 0.35, 0.2, 0.08, 0.02]
        return random.choices(usefulness_levels, weights=weights)[0]
    
    def _simulate_comments(self) -> str:
        import random
        positive_comments = [
            "Sehr hilfreich!",
            "Gute Informationen",
            "Schnelle Antwort",
            "Genau das was ich gesucht habe"
        ]
        neutral_comments = [
            "OK",
            "Geht so",
            "Könnte besser sein"
        ]
        negative_comments = [
            "Zu langsam",
            "Unvollständig",
            "Nicht hilfreich"
        ]
        
        if random.random() < 0.7:
            return random.choice(positive_comments)
        elif random.random() < 0.2:
            return random.choice(neutral_comments)
        else:
            return random.choice(negative_comments)
    
    def _simulate_recommendation(self) -> bool:
        import random
        return random.random() < 0.8
    
    def record_interaction(self, user_id: str, message: str, response: Dict[str, Any], 
                          response_time: float, intent_recognized: bool, api_success: bool) -> str:
        interaction_id = f"interaction_{int(time.time())}_{user_id}"
        
        quality_evaluation = self.evaluate_response_quality(message, response, response_time)
        
        user_feedback = self.collect_user_feedback(user_id, interaction_id)
        
        interaction = {
            "id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "message": message,
            "response_type": response.get('type', 'unknown'),
            "response_time": response_time,
            "response_quality": quality_evaluation,
            "user_feedback": user_feedback,
            "intent_recognized": intent_recognized,
            "api_success": api_success,
            "tool_used": response.get('tool_used'),
            "suggestions_provided": len(response.get('suggestions', []))
        }
        
        self.metrics["interactions"].append(interaction)
        self._update_aggregated_metrics()
        self._save_metrics()
        
        return interaction_id
    
    def _update_aggregated_metrics(self):
        interactions = self.metrics["interactions"]
        
        if not interactions:
            return
        
        total_interactions = len(interactions)
        
        quality_scores = [i.get('response_quality', {}).get('score', 0) for i in interactions if i.get('response_quality')]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        response_times = [i.get('response_time', 0) for i in interactions]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        user_ratings = [i.get('user_feedback', {}).get('rating', 0) for i in interactions if i.get('user_feedback')]
        satisfaction_rate = sum(1 for r in user_ratings if r >= 4) / len(user_ratings) if user_ratings else 0.0
        
        intent_recognized_count = sum(1 for i in interactions if i.get('intent_recognized', False))
        intent_recognition_rate = intent_recognized_count / total_interactions if total_interactions > 0 else 0.0
        
        api_success_count = sum(1 for i in interactions if i.get('api_success', False))
        api_success_rate = api_success_count / total_interactions if total_interactions > 0 else 0.0
        
        self.metrics["aggregated_metrics"] = {
            "total_interactions": total_interactions,
            "average_response_quality": round(avg_quality, 3),
            "average_response_time": round(avg_response_time, 3),
            "user_satisfaction_rate": round(satisfaction_rate, 3),
            "intent_recognition_rate": round(intent_recognition_rate, 3),
            "api_success_rate": round(api_success_rate, 3)
        }
        
        self.metrics["last_updated"] = datetime.now().isoformat()
    
    def get_evaluation_report(self) -> Dict[str, Any]:
        aggregated = self.metrics.get("aggregated_metrics", {})
        
        quality_distribution = {}
        for interaction in self.metrics.get("interactions", []):
            quality_level = interaction.get('response_quality', {}).get('level', 'unknown')
            quality_distribution[quality_level] = quality_distribution.get(quality_level, 0) + 1
        
        tool_usage = {}
        for interaction in self.metrics.get("interactions", []):
            tool = interaction.get('tool_used', 'none')
            tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        response_types = {}
        for interaction in self.metrics.get("interactions", []):
            response_type = interaction.get('response_type', 'unknown')
            response_types[response_type] = response_types.get(response_type, 0) + 1
        
        return {
            "summary": {
                "total_interactions": aggregated.get("total_interactions", 0),
                "overall_quality_score": aggregated.get("average_response_quality", 0),
                "user_satisfaction": aggregated.get("user_satisfaction_rate", 0),
                "system_performance": {
                    "avg_response_time": aggregated.get("average_response_time", 0),
                    "intent_recognition_rate": aggregated.get("intent_recognition_rate", 0),
                    "api_success_rate": aggregated.get("api_success_rate", 0)
                }
            },
            "quality_distribution": quality_distribution,
            "tool_usage_statistics": tool_usage,
            "response_type_distribution": response_types,
            "recent_interactions": self.metrics.get("interactions", [])[-10:],
            "evaluation_config": self.metrics.get("evaluation_config", {}),
            "generated_at": datetime.now().isoformat()
        } 