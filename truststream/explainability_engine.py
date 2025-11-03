# TrustStream Explainability Engine v4.4
# Transparent AI Decision Making and User Appeal System

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import shap
import lime
from lime.lime_text import LimeTextExplainer
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px

from .ai_providers import AIProviderManager, AIResponse
from .agents.manager import AgentManager
from .trust_pyramid import TrustPyramidCalculator, TrustProfile

logger = logging.getLogger(__name__)


class ExplanationType(Enum):
    """Types of explanations available"""
    DECISION_BREAKDOWN = "decision_breakdown"
    FEATURE_IMPORTANCE = "feature_importance"
    SIMILAR_CASES = "similar_cases"
    COUNTERFACTUAL = "counterfactual"
    TRUST_FACTORS = "trust_factors"
    AGENT_REASONING = "agent_reasoning"
    CONFIDENCE_ANALYSIS = "confidence_analysis"


class ExplanationAudience(Enum):
    """Target audience for explanations"""
    END_USER = "end_user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    DEVELOPER = "developer"
    AUDITOR = "auditor"


@dataclass
class ExplanationRequest:
    """Request for AI decision explanation"""
    decision_id: str
    content: str
    decision: str
    confidence: float
    ai_responses: List[AIResponse]
    trust_profile: Optional[TrustProfile]
    audience: ExplanationAudience
    explanation_types: List[ExplanationType]
    user_id: Optional[str]
    context: Dict[str, Any]


@dataclass
class FeatureImportance:
    """Feature importance for decision explanation"""
    feature_name: str
    importance_score: float
    contribution: str  # positive, negative, neutral
    description: str
    evidence: List[str]


@dataclass
class SimilarCase:
    """Similar case for comparison"""
    case_id: str
    content_similarity: float
    decision_similarity: float
    outcome: str
    explanation: str
    timestamp: datetime


@dataclass
class CounterfactualExample:
    """Counterfactual explanation example"""
    original_text: str
    modified_text: str
    original_decision: str
    new_decision: str
    changes_made: List[str]
    confidence_change: float


@dataclass
class DecisionExplanation:
    """Comprehensive explanation of AI decision"""
    decision_id: str
    timestamp: datetime
    audience: ExplanationAudience
    
    # Core explanation
    summary: str
    detailed_reasoning: str
    confidence_explanation: str
    
    # Feature analysis
    key_factors: List[FeatureImportance]
    trust_factor_breakdown: Dict[str, float]
    
    # Comparative analysis
    similar_cases: List[SimilarCase]
    counterfactuals: List[CounterfactualExample]
    
    # Agent insights
    agent_contributions: Dict[str, Dict[str, Any]]
    consensus_analysis: Dict[str, Any]
    
    # Transparency metrics
    explanation_confidence: float
    bias_indicators: List[str]
    uncertainty_factors: List[str]
    
    # Appeal information
    appeal_options: List[str]
    improvement_suggestions: List[str]
    
    # Visualizations
    charts: Dict[str, Any]
    metadata: Dict[str, Any]


class TrustStreamExplainabilityEngine:
    """
    TrustStream Explainability Engine v4.4
    
    Provides transparent, interpretable explanations for AI moderation decisions:
    - Multi-level explanations for different audiences (users, moderators, admins)
    - Feature importance analysis using SHAP and LIME
    - Similar case retrieval and comparison
    - Counterfactual examples showing decision boundaries
    - Trust factor breakdown and contribution analysis
    - Agent reasoning transparency and consensus analysis
    - Bias detection and uncertainty quantification
    - Interactive visualizations and decision trees
    - Appeal guidance and improvement suggestions
    - Audit trail and compliance documentation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize TrustStream components
        self.ai_manager = AIProviderManager(config.get('ai_providers', {}))
        self.agent_manager = AgentManager(config.get('agents', {}))
        self.trust_calculator = TrustPyramidCalculator(config.get('trust_pyramid', {}))
        
        # Explanation models
        self.lime_explainer = LimeTextExplainer(
            class_names=['approve', 'flag', 'block'],
            feature_selection='auto',
            discretize_continuous=True
        )
        
        # Feature extractors
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        
        # Case database for similarity matching
        self.case_database: List[Dict[str, Any]] = []
        self.feature_importance_cache: Dict[str, List[FeatureImportance]] = {}
        
        # Explanation templates
        self.explanation_templates = self._load_explanation_templates()
        
        # Bias detection patterns
        self.bias_patterns = self._load_bias_patterns()
        
        logger.info("TrustStream Explainability Engine initialized")
    
    async def explain_decision(self, request: ExplanationRequest) -> DecisionExplanation:
        """
        Generate comprehensive explanation for AI moderation decision.
        """
        try:
            logger.info(f"Generating explanation for decision {request.decision_id}")
            
            # Initialize explanation components
            explanation_components = {}
            
            # Generate core explanation
            if ExplanationType.DECISION_BREAKDOWN in request.explanation_types:
                explanation_components['breakdown'] = await self._generate_decision_breakdown(request)
            
            # Feature importance analysis
            if ExplanationType.FEATURE_IMPORTANCE in request.explanation_types:
                explanation_components['features'] = await self._analyze_feature_importance(request)
            
            # Similar cases
            if ExplanationType.SIMILAR_CASES in request.explanation_types:
                explanation_components['similar_cases'] = await self._find_similar_cases(request)
            
            # Counterfactual examples
            if ExplanationType.COUNTERFACTUAL in request.explanation_types:
                explanation_components['counterfactuals'] = await self._generate_counterfactuals(request)
            
            # Trust factor analysis
            if ExplanationType.TRUST_FACTORS in request.explanation_types:
                explanation_components['trust_factors'] = await self._analyze_trust_factors(request)
            
            # Agent reasoning
            if ExplanationType.AGENT_REASONING in request.explanation_types:
                explanation_components['agent_reasoning'] = await self._analyze_agent_reasoning(request)
            
            # Confidence analysis
            if ExplanationType.CONFIDENCE_ANALYSIS in request.explanation_types:
                explanation_components['confidence'] = await self._analyze_confidence(request)
            
            # Compile comprehensive explanation
            explanation = await self._compile_explanation(request, explanation_components)
            
            # Store for future similarity matching
            await self._store_case(request, explanation)
            
            logger.info(f"Explanation generated for decision {request.decision_id}")
            return explanation
            
        except Exception as e:
            logger.error(f"Explanation generation failed: {str(e)}")
            return await self._generate_fallback_explanation(request)
    
    async def _generate_decision_breakdown(self, request: ExplanationRequest) -> Dict[str, Any]:
        """Generate high-level decision breakdown."""
        try:
            # Analyze AI responses
            response_analysis = self._analyze_ai_responses(request.ai_responses)
            
            # Generate summary based on audience
            if request.audience == ExplanationAudience.END_USER:
                summary = await self._generate_user_friendly_summary(request, response_analysis)
            elif request.audience == ExplanationAudience.MODERATOR:
                summary = await self._generate_moderator_summary(request, response_analysis)
            else:
                summary = await self._generate_technical_summary(request, response_analysis)
            
            return {
                'summary': summary,
                'response_analysis': response_analysis,
                'decision_path': self._trace_decision_path(request.ai_responses),
                'key_indicators': self._extract_key_indicators(request.ai_responses)
            }
            
        except Exception as e:
            logger.error(f"Decision breakdown failed: {str(e)}")
            return {'summary': 'Unable to generate decision breakdown', 'error': str(e)}
    
    async def _analyze_feature_importance(self, request: ExplanationRequest) -> List[FeatureImportance]:
        """Analyze feature importance using LIME and custom analysis."""
        try:
            # Check cache first
            cache_key = f"{request.decision_id}_{request.content[:100]}"
            if cache_key in self.feature_importance_cache:
                return self.feature_importance_cache[cache_key]
            
            features = []
            
            # Text-based features using LIME
            text_features = await self._analyze_text_features(request.content, request.decision)
            features.extend(text_features)
            
            # Trust-based features
            if request.trust_profile:
                trust_features = await self._analyze_trust_features(request.trust_profile)
                features.extend(trust_features)
            
            # Context-based features
            context_features = await self._analyze_context_features(request.context)
            features.extend(context_features)
            
            # Agent-specific features
            agent_features = await self._analyze_agent_features(request.ai_responses)
            features.extend(agent_features)
            
            # Sort by importance
            features.sort(key=lambda x: abs(x.importance_score), reverse=True)
            
            # Cache results
            self.feature_importance_cache[cache_key] = features[:20]  # Top 20 features
            
            return features[:20]
            
        except Exception as e:
            logger.error(f"Feature importance analysis failed: {str(e)}")
            return []
    
    async def _analyze_text_features(self, content: str, decision: str) -> List[FeatureImportance]:
        """Analyze text-based features using LIME."""
        try:
            # Create prediction function for LIME
            def predict_fn(texts):
                # Simplified prediction function
                predictions = []
                for text in texts:
                    # Basic sentiment and toxicity indicators
                    score = self._calculate_text_score(text)
                    predictions.append([1-score, score, 0])  # [approve, flag, block]
                return np.array(predictions)
            
            # Generate LIME explanation
            explanation = self.lime_explainer.explain_instance(
                content,
                predict_fn,
                num_features=10,
                num_samples=100
            )
            
            features = []
            for feature, importance in explanation.as_list():
                features.append(FeatureImportance(
                    feature_name=f"Text: {feature}",
                    importance_score=importance,
                    contribution="positive" if importance > 0 else "negative",
                    description=f"Text feature '{feature}' contributes to the decision",
                    evidence=[feature]
                ))
            
            return features
            
        except Exception as e:
            logger.error(f"Text feature analysis failed: {str(e)}")
            return []
    
    async def _analyze_trust_features(self, trust_profile: TrustProfile) -> List[FeatureImportance]:
        """Analyze trust-based features."""
        try:
            features = []
            
            # Overall trust score
            features.append(FeatureImportance(
                feature_name="Overall Trust Score",
                importance_score=trust_profile.overall_score * 2 - 1,  # Convert to -1 to 1 range
                contribution="positive" if trust_profile.overall_score > 0.5 else "negative",
                description=f"User's overall trust score of {trust_profile.overall_score:.2f}",
                evidence=[f"Trust score: {trust_profile.overall_score:.2f}"]
            ))
            
            # Individual layer scores
            layer_weights = {'iq': 0.3, 'appeal': 0.25, 'social': 0.25, 'humanity': 0.2}
            
            for layer_name, weight in layer_weights.items():
                layer_score = getattr(trust_profile.layers, layer_name)
                importance = (layer_score - 0.5) * weight * 2  # Weighted importance
                
                features.append(FeatureImportance(
                    feature_name=f"Trust Layer: {layer_name.title()}",
                    importance_score=importance,
                    contribution="positive" if layer_score > 0.5 else "negative",
                    description=f"{layer_name.title()} layer score affects trust assessment",
                    evidence=[f"{layer_name.title()}: {layer_score:.2f}"]
                ))
            
            return features
            
        except Exception as e:
            logger.error(f"Trust feature analysis failed: {str(e)}")
            return []
    
    async def _analyze_context_features(self, context: Dict[str, Any]) -> List[FeatureImportance]:
        """Analyze context-based features."""
        try:
            features = []
            
            # Time-based features
            if 'timestamp' in context:
                hour = datetime.fromisoformat(context['timestamp']).hour
                if 22 <= hour or hour <= 6:  # Late night/early morning
                    features.append(FeatureImportance(
                        feature_name="Time of Day",
                        importance_score=0.3,
                        contribution="negative",
                        description="Posted during late night hours when moderation is stricter",
                        evidence=[f"Posted at {hour:02d}:xx"]
                    ))
            
            # Room/community context
            if 'room_id' in context:
                room_moderation_level = context.get('room_moderation_level', 'moderate')
                if room_moderation_level == 'strict':
                    features.append(FeatureImportance(
                        feature_name="Room Moderation Level",
                        importance_score=0.4,
                        contribution="negative",
                        description="Posted in a strictly moderated room",
                        evidence=[f"Room moderation: {room_moderation_level}"]
                    ))
            
            # User history context
            if 'recent_violations' in context:
                violation_count = context['recent_violations']
                if violation_count > 0:
                    importance = min(violation_count * 0.2, 0.8)
                    features.append(FeatureImportance(
                        feature_name="Recent Violations",
                        importance_score=importance,
                        contribution="negative",
                        description=f"User has {violation_count} recent violations",
                        evidence=[f"Recent violations: {violation_count}"]
                    ))
            
            return features
            
        except Exception as e:
            logger.error(f"Context feature analysis failed: {str(e)}")
            return []
    
    async def _analyze_agent_features(self, ai_responses: List[AIResponse]) -> List[FeatureImportance]:
        """Analyze agent-specific features."""
        try:
            features = []
            
            # Agent consensus
            decisions = [r.decision for r in ai_responses]
            decision_counts = {d: decisions.count(d) for d in set(decisions)}
            consensus_strength = max(decision_counts.values()) / len(decisions)
            
            features.append(FeatureImportance(
                feature_name="Agent Consensus",
                importance_score=consensus_strength,
                contribution="positive" if consensus_strength > 0.7 else "neutral",
                description=f"Agent consensus strength: {consensus_strength:.2f}",
                evidence=[f"Consensus: {consensus_strength:.1%}"]
            ))
            
            # Individual agent contributions
            for response in ai_responses:
                if response.confidence > 0.8:  # High confidence responses
                    features.append(FeatureImportance(
                        feature_name=f"Agent: {response.provider}",
                        importance_score=response.confidence * (1 if response.decision != 'APPROVE' else -1),
                        contribution="positive" if response.decision != 'APPROVE' else "negative",
                        description=f"{response.provider} agent decision with high confidence",
                        evidence=[f"{response.provider}: {response.decision} ({response.confidence:.2f})"]
                    ))
            
            return features
            
        except Exception as e:
            logger.error(f"Agent feature analysis failed: {str(e)}")
            return []
    
    async def _find_similar_cases(self, request: ExplanationRequest) -> List[SimilarCase]:
        """Find similar cases for comparison."""
        try:
            if not self.case_database:
                return []
            
            # Vectorize current content
            current_vector = self._vectorize_content(request.content)
            
            similar_cases = []
            
            for case in self.case_database[-1000:]:  # Check last 1000 cases
                # Calculate content similarity
                case_vector = self._vectorize_content(case['content'])
                content_similarity = cosine_similarity([current_vector], [case_vector])[0][0]
                
                if content_similarity > 0.3:  # Minimum similarity threshold
                    # Calculate decision similarity
                    decision_similarity = 1.0 if case['decision'] == request.decision else 0.0
                    
                    similar_cases.append(SimilarCase(
                        case_id=case['id'],
                        content_similarity=content_similarity,
                        decision_similarity=decision_similarity,
                        outcome=case['decision'],
                        explanation=case.get('explanation_summary', 'No explanation available'),
                        timestamp=datetime.fromisoformat(case['timestamp'])
                    ))
            
            # Sort by similarity and return top 5
            similar_cases.sort(key=lambda x: x.content_similarity, reverse=True)
            return similar_cases[:5]
            
        except Exception as e:
            logger.error(f"Similar case analysis failed: {str(e)}")
            return []
    
    async def _generate_counterfactuals(self, request: ExplanationRequest) -> List[CounterfactualExample]:
        """Generate counterfactual examples."""
        try:
            counterfactuals = []
            
            # Generate text modifications that would change the decision
            modifications = [
                ("Remove potentially offensive words", self._remove_offensive_words),
                ("Add positive sentiment", self._add_positive_sentiment),
                ("Reduce intensity", self._reduce_intensity),
                ("Add context", self._add_context)
            ]
            
            for description, modifier_func in modifications:
                try:
                    modified_text = modifier_func(request.content)
                    
                    if modified_text != request.content:
                        # Simulate decision on modified text
                        new_decision = await self._simulate_decision(modified_text, request.context)
                        
                        if new_decision != request.decision:
                            counterfactuals.append(CounterfactualExample(
                                original_text=request.content,
                                modified_text=modified_text,
                                original_decision=request.decision,
                                new_decision=new_decision,
                                changes_made=[description],
                                confidence_change=0.2  # Placeholder
                            ))
                except Exception as e:
                    logger.warning(f"Counterfactual generation failed for {description}: {str(e)}")
                    continue
            
            return counterfactuals[:3]  # Return top 3
            
        except Exception as e:
            logger.error(f"Counterfactual generation failed: {str(e)}")
            return []
    
    async def _analyze_trust_factors(self, request: ExplanationRequest) -> Dict[str, float]:
        """Analyze trust factor contributions."""
        try:
            if not request.trust_profile:
                return {}
            
            trust_factors = {
                'Content Quality (IQ)': request.trust_profile.layers.iq,
                'Community Appeal': request.trust_profile.layers.appeal,
                'Social Connections': request.trust_profile.layers.social,
                'Human Authenticity': request.trust_profile.layers.humanity,
                'Overall Trust': request.trust_profile.overall_score
            }
            
            # Calculate relative contributions
            total_contribution = sum(trust_factors.values())
            if total_contribution > 0:
                trust_factors = {k: v/total_contribution for k, v in trust_factors.items()}
            
            return trust_factors
            
        except Exception as e:
            logger.error(f"Trust factor analysis failed: {str(e)}")
            return {}
    
    async def _analyze_agent_reasoning(self, request: ExplanationRequest) -> Dict[str, Dict[str, Any]]:
        """Analyze individual agent reasoning."""
        try:
            agent_analysis = {}
            
            for response in request.ai_responses:
                agent_analysis[response.provider] = {
                    'decision': response.decision,
                    'confidence': response.confidence,
                    'reasoning': response.reasoning,
                    'key_factors': response.metadata.get('key_factors', []),
                    'risk_indicators': response.metadata.get('risk_indicators', []),
                    'processing_time': response.metadata.get('processing_time', 0)
                }
            
            # Consensus analysis
            decisions = [r.decision for r in request.ai_responses]
            consensus_analysis = {
                'agreement_level': len(set(decisions)) == 1,
                'majority_decision': max(set(decisions), key=decisions.count),
                'disagreement_factors': self._analyze_disagreements(request.ai_responses)
            }
            
            agent_analysis['consensus'] = consensus_analysis
            
            return agent_analysis
            
        except Exception as e:
            logger.error(f"Agent reasoning analysis failed: {str(e)}")
            return {}
    
    async def _analyze_confidence(self, request: ExplanationRequest) -> Dict[str, Any]:
        """Analyze confidence levels and uncertainty."""
        try:
            confidences = [r.confidence for r in request.ai_responses]
            
            confidence_analysis = {
                'average_confidence': np.mean(confidences),
                'confidence_std': np.std(confidences),
                'min_confidence': min(confidences),
                'max_confidence': max(confidences),
                'confidence_range': max(confidences) - min(confidences)
            }
            
            # Uncertainty factors
            uncertainty_factors = []
            
            if confidence_analysis['confidence_std'] > 0.2:
                uncertainty_factors.append("High variance in agent confidence levels")
            
            if confidence_analysis['average_confidence'] < 0.7:
                uncertainty_factors.append("Below-average confidence in decision")
            
            if len(set(r.decision for r in request.ai_responses)) > 1:
                uncertainty_factors.append("Disagreement between AI agents")
            
            confidence_analysis['uncertainty_factors'] = uncertainty_factors
            
            return confidence_analysis
            
        except Exception as e:
            logger.error(f"Confidence analysis failed: {str(e)}")
            return {}
    
    async def _compile_explanation(
        self, 
        request: ExplanationRequest, 
        components: Dict[str, Any]
    ) -> DecisionExplanation:
        """Compile comprehensive explanation from components."""
        try:
            # Generate audience-appropriate summary
            summary = await self._generate_explanation_summary(request, components)
            
            # Extract key factors
            key_factors = components.get('features', [])[:10]  # Top 10 factors
            
            # Trust factor breakdown
            trust_factors = components.get('trust_factors', {})
            
            # Similar cases
            similar_cases = components.get('similar_cases', [])
            
            # Counterfactuals
            counterfactuals = components.get('counterfactuals', [])
            
            # Agent contributions
            agent_contributions = components.get('agent_reasoning', {})
            
            # Confidence analysis
            confidence_info = components.get('confidence', {})
            
            # Generate visualizations
            charts = await self._generate_explanation_charts(components)
            
            # Detect bias indicators
            bias_indicators = await self._detect_bias_indicators(request, components)
            
            # Generate appeal options
            appeal_options = await self._generate_appeal_options(request)
            
            # Generate improvement suggestions
            improvement_suggestions = await self._generate_improvement_suggestions(request, components)
            
            explanation = DecisionExplanation(
                decision_id=request.decision_id,
                timestamp=datetime.utcnow(),
                audience=request.audience,
                summary=summary,
                detailed_reasoning=components.get('breakdown', {}).get('summary', ''),
                confidence_explanation=self._format_confidence_explanation(confidence_info),
                key_factors=key_factors,
                trust_factor_breakdown=trust_factors,
                similar_cases=similar_cases,
                counterfactuals=counterfactuals,
                agent_contributions=agent_contributions,
                consensus_analysis=agent_contributions.get('consensus', {}),
                explanation_confidence=confidence_info.get('average_confidence', 0.5),
                bias_indicators=bias_indicators,
                uncertainty_factors=confidence_info.get('uncertainty_factors', []),
                appeal_options=appeal_options,
                improvement_suggestions=improvement_suggestions,
                charts=charts,
                metadata={
                    'generation_time': datetime.utcnow().isoformat(),
                    'components_used': list(components.keys()),
                    'explanation_version': '4.4'
                }
            )
            
            return explanation
            
        except Exception as e:
            logger.error(f"Explanation compilation failed: {str(e)}")
            return await self._generate_fallback_explanation(request)
    
    # Helper methods
    
    def _analyze_ai_responses(self, responses: List[AIResponse]) -> Dict[str, Any]:
        """Analyze AI responses for patterns."""
        decisions = [r.decision for r in responses]
        confidences = [r.confidence for r in responses]
        
        return {
            'total_responses': len(responses),
            'unique_decisions': len(set(decisions)),
            'majority_decision': max(set(decisions), key=decisions.count),
            'average_confidence': np.mean(confidences),
            'confidence_variance': np.var(confidences),
            'unanimous': len(set(decisions)) == 1
        }
    
    def _trace_decision_path(self, responses: List[AIResponse]) -> List[Dict[str, Any]]:
        """Trace the decision-making path."""
        path = []
        
        for i, response in enumerate(responses):
            path.append({
                'step': i + 1,
                'agent': response.provider,
                'decision': response.decision,
                'confidence': response.confidence,
                'key_reasoning': response.reasoning[:200] + "..." if len(response.reasoning) > 200 else response.reasoning
            })
        
        return path
    
    def _extract_key_indicators(self, responses: List[AIResponse]) -> List[str]:
        """Extract key indicators from AI responses."""
        indicators = []
        
        for response in responses:
            if hasattr(response, 'metadata') and 'key_indicators' in response.metadata:
                indicators.extend(response.metadata['key_indicators'])
        
        # Remove duplicates and return top indicators
        return list(set(indicators))[:10]
    
    def _calculate_text_score(self, text: str) -> float:
        """Calculate basic text toxicity score."""
        # Simplified toxicity calculation
        toxic_words = ['hate', 'stupid', 'idiot', 'kill', 'die', 'worst']
        toxic_count = sum(1 for word in toxic_words if word in text.lower())
        return min(toxic_count / 10, 1.0)
    
    def _vectorize_content(self, content: str) -> np.ndarray:
        """Vectorize content for similarity comparison."""
        try:
            # Fit vectorizer if not already fitted
            if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                # Use a sample of existing cases to fit
                sample_texts = [case['content'] for case in self.case_database[-100:]]
                if sample_texts:
                    sample_texts.append(content)
                    self.tfidf_vectorizer.fit(sample_texts)
                else:
                    self.tfidf_vectorizer.fit([content])
            
            return self.tfidf_vectorizer.transform([content]).toarray()[0]
        except Exception:
            # Fallback to simple word count vector
            words = content.lower().split()
            return np.array([len(words), len(set(words))])
    
    def _remove_offensive_words(self, text: str) -> str:
        """Remove potentially offensive words."""
        offensive_words = ['hate', 'stupid', 'idiot', 'kill', 'die', 'worst']
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in offensive_words]
        return ' '.join(filtered_words)
    
    def _add_positive_sentiment(self, text: str) -> str:
        """Add positive sentiment to text."""
        positive_additions = [
            "I appreciate your perspective.",
            "Thank you for sharing.",
            "This is constructive feedback."
        ]
        return text + " " + positive_additions[0]
    
    def _reduce_intensity(self, text: str) -> str:
        """Reduce intensity of language."""
        intensity_replacements = {
            'hate': 'dislike',
            'love': 'like',
            'terrible': 'not great',
            'amazing': 'good',
            'worst': 'not the best'
        }
        
        for intense, mild in intensity_replacements.items():
            text = text.replace(intense, mild)
        
        return text
    
    def _add_context(self, text: str) -> str:
        """Add context to make text clearer."""
        return f"In my opinion, {text.lower()}"
    
    async def _simulate_decision(self, text: str, context: Dict[str, Any]) -> str:
        """Simulate AI decision on modified text."""
        # Simplified simulation
        score = self._calculate_text_score(text)
        
        if score > 0.7:
            return 'BLOCK'
        elif score > 0.3:
            return 'FLAG'
        else:
            return 'APPROVE'
    
    def _analyze_disagreements(self, responses: List[AIResponse]) -> List[str]:
        """Analyze disagreements between agents."""
        disagreements = []
        
        decisions = [r.decision for r in responses]
        if len(set(decisions)) > 1:
            disagreements.append("Agents disagree on severity level")
        
        confidences = [r.confidence for r in responses]
        if max(confidences) - min(confidences) > 0.3:
            disagreements.append("Significant confidence variance between agents")
        
        return disagreements
    
    async def _generate_explanation_summary(
        self, 
        request: ExplanationRequest, 
        components: Dict[str, Any]
    ) -> str:
        """Generate audience-appropriate explanation summary."""
        if request.audience == ExplanationAudience.END_USER:
            return await self._generate_user_summary(request, components)
        elif request.audience == ExplanationAudience.MODERATOR:
            return await self._generate_moderator_summary(request, components)
        else:
            return await self._generate_technical_summary(request, components)
    
    async def _generate_user_summary(self, request: ExplanationRequest, components: Dict[str, Any]) -> str:
        """Generate user-friendly summary."""
        decision_map = {
            'APPROVE': 'approved',
            'FLAG': 'flagged for review',
            'BLOCK': 'blocked'
        }
        
        decision_text = decision_map.get(request.decision, request.decision.lower())
        
        summary = f"Your content was {decision_text}. "
        
        if request.confidence > 0.8:
            summary += "Our AI systems are confident in this decision. "
        else:
            summary += "This decision had moderate confidence and may be reviewed. "
        
        # Add key factors in simple language
        key_factors = components.get('features', [])[:3]
        if key_factors:
            summary += "Key factors included: "
            factor_descriptions = []
            for factor in key_factors:
                if 'trust' in factor.feature_name.lower():
                    factor_descriptions.append("your trust score")
                elif 'text' in factor.feature_name.lower():
                    factor_descriptions.append("content analysis")
                else:
                    factor_descriptions.append(factor.feature_name.lower())
            
            summary += ", ".join(factor_descriptions) + ". "
        
        return summary
    
    async def _generate_moderator_summary(self, request: ExplanationRequest, components: Dict[str, Any]) -> str:
        """Generate moderator-focused summary."""
        summary = f"Decision: {request.decision} (Confidence: {request.confidence:.2f})\n\n"
        
        # Agent consensus
        agent_info = components.get('agent_reasoning', {})
        if 'consensus' in agent_info:
            consensus = agent_info['consensus']
            summary += f"Agent Consensus: {consensus.get('majority_decision', 'Unknown')}\n"
            if not consensus.get('agreement_level', False):
                summary += "⚠️ Agents disagreed on this decision\n"
        
        # Key risk factors
        key_factors = components.get('features', [])[:5]
        if key_factors:
            summary += "\nKey Factors:\n"
            for factor in key_factors:
                contribution_icon = "🔴" if factor.contribution == "negative" else "🟢"
                summary += f"{contribution_icon} {factor.feature_name}: {factor.importance_score:.2f}\n"
        
        return summary
    
    async def _generate_technical_summary(self, request: ExplanationRequest, components: Dict[str, Any]) -> str:
        """Generate technical summary for developers/admins."""
        summary = f"Decision ID: {request.decision_id}\n"
        summary += f"Decision: {request.decision} (Confidence: {request.confidence:.3f})\n"
        summary += f"Timestamp: {datetime.utcnow().isoformat()}\n\n"
        
        # Technical metrics
        confidence_info = components.get('confidence', {})
        summary += f"Confidence Analysis:\n"
        summary += f"- Average: {confidence_info.get('average_confidence', 0):.3f}\n"
        summary += f"- Std Dev: {confidence_info.get('confidence_std', 0):.3f}\n"
        summary += f"- Range: {confidence_info.get('confidence_range', 0):.3f}\n\n"
        
        # Agent performance
        agent_info = components.get('agent_reasoning', {})
        if agent_info:
            summary += "Agent Responses:\n"
            for agent, info in agent_info.items():
                if agent != 'consensus':
                    summary += f"- {agent}: {info.get('decision', 'N/A')} ({info.get('confidence', 0):.3f})\n"
        
        return summary
    
    def _format_confidence_explanation(self, confidence_info: Dict[str, Any]) -> str:
        """Format confidence explanation."""
        if not confidence_info:
            return "Confidence information not available."
        
        avg_conf = confidence_info.get('average_confidence', 0)
        
        if avg_conf > 0.8:
            return f"High confidence decision ({avg_conf:.2f}). The AI systems strongly agree on this outcome."
        elif avg_conf > 0.6:
            return f"Moderate confidence decision ({avg_conf:.2f}). There is reasonable certainty in this outcome."
        else:
            return f"Low confidence decision ({avg_conf:.2f}). This decision may benefit from human review."
    
    async def _generate_explanation_charts(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualization charts for explanation."""
        charts = {}
        
        try:
            # Feature importance chart
            features = components.get('features', [])[:10]
            if features:
                fig = go.Figure(data=[
                    go.Bar(
                        x=[f.importance_score for f in features],
                        y=[f.feature_name for f in features],
                        orientation='h',
                        marker_color=['red' if f.contribution == 'negative' else 'green' for f in features]
                    )
                ])
                fig.update_layout(
                    title="Feature Importance",
                    xaxis_title="Importance Score",
                    yaxis_title="Features"
                )
                charts['feature_importance'] = fig.to_json()
            
            # Trust factors chart
            trust_factors = components.get('trust_factors', {})
            if trust_factors:
                fig = go.Figure(data=[
                    go.Pie(
                        labels=list(trust_factors.keys()),
                        values=list(trust_factors.values()),
                        hole=0.3
                    )
                ])
                fig.update_layout(title="Trust Factor Breakdown")
                charts['trust_factors'] = fig.to_json()
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
        
        return charts
    
    async def _detect_bias_indicators(self, request: ExplanationRequest, components: Dict[str, Any]) -> List[str]:
        """Detect potential bias indicators."""
        bias_indicators = []
        
        # Check for demographic bias patterns
        for pattern in self.bias_patterns:
            if pattern['type'] == 'demographic' and pattern['pattern'] in request.content.lower():
                bias_indicators.append(f"Potential demographic bias: {pattern['description']}")
        
        # Check for confidence bias
        confidence_info = components.get('confidence', {})
        if confidence_info.get('confidence_std', 0) > 0.3:
            bias_indicators.append("High variance in agent confidence may indicate bias")
        
        return bias_indicators
    
    async def _generate_appeal_options(self, request: ExplanationRequest) -> List[str]:
        """Generate appeal options for users."""
        appeal_options = []
        
        if request.decision in ['FLAG', 'BLOCK']:
            appeal_options.append("Request human review of this decision")
            appeal_options.append("Provide additional context for reconsideration")
            
            if request.confidence < 0.7:
                appeal_options.append("Challenge low-confidence automated decision")
        
        appeal_options.append("Report potential bias in moderation")
        appeal_options.append("Request explanation of community guidelines")
        
        return appeal_options
    
    async def _generate_improvement_suggestions(self, request: ExplanationRequest, components: Dict[str, Any]) -> List[str]:
        """Generate suggestions for content improvement."""
        suggestions = []
        
        # Analyze key negative factors
        features = components.get('features', [])
        negative_features = [f for f in features if f.contribution == 'negative']
        
        for feature in negative_features[:3]:
            if 'text' in feature.feature_name.lower():
                suggestions.append("Consider rephrasing potentially problematic language")
            elif 'trust' in feature.feature_name.lower():
                suggestions.append("Build trust by engaging positively with the community")
            elif 'time' in feature.feature_name.lower():
                suggestions.append("Consider posting during more active community hours")
        
        if not suggestions:
            suggestions.append("Continue following community guidelines")
        
        return suggestions
    
    async def _store_case(self, request: ExplanationRequest, explanation: DecisionExplanation):
        """Store case for future similarity matching."""
        try:
            case = {
                'id': request.decision_id,
                'content': request.content,
                'decision': request.decision,
                'confidence': request.confidence,
                'timestamp': datetime.utcnow().isoformat(),
                'explanation_summary': explanation.summary,
                'key_factors': [f.feature_name for f in explanation.key_factors[:5]]
            }
            
            self.case_database.append(case)
            
            # Keep only last 10000 cases
            if len(self.case_database) > 10000:
                self.case_database = self.case_database[-10000:]
                
        except Exception as e:
            logger.error(f"Case storage failed: {str(e)}")
    
    async def _generate_fallback_explanation(self, request: ExplanationRequest) -> DecisionExplanation:
        """Generate fallback explanation when main process fails."""
        return DecisionExplanation(
            decision_id=request.decision_id,
            timestamp=datetime.utcnow(),
            audience=request.audience,
            summary=f"Content was {request.decision.lower()} by our AI moderation system.",
            detailed_reasoning="Detailed analysis temporarily unavailable.",
            confidence_explanation=f"Decision confidence: {request.confidence:.2f}",
            key_factors=[],
            trust_factor_breakdown={},
            similar_cases=[],
            counterfactuals=[],
            agent_contributions={},
            consensus_analysis={},
            explanation_confidence=request.confidence,
            bias_indicators=[],
            uncertainty_factors=["Explanation generation failed"],
            appeal_options=["Request human review"],
            improvement_suggestions=["Follow community guidelines"],
            charts={},
            metadata={'fallback': True}
        )
    
    def _load_explanation_templates(self) -> Dict[str, str]:
        """Load explanation templates for different audiences."""
        return {
            'user_friendly': "Your content was {decision} because {reason}. {appeal_info}",
            'moderator': "Decision: {decision} | Confidence: {confidence} | Key factors: {factors}",
            'technical': "ID: {id} | Decision: {decision} | Agents: {agents} | Metrics: {metrics}"
        }
    
    def _load_bias_patterns(self) -> List[Dict[str, Any]]:
        """Load bias detection patterns."""
        return [
            {
                'type': 'demographic',
                'pattern': 'age',
                'description': 'Content mentions age-related terms'
            },
            {
                'type': 'demographic', 
                'pattern': 'gender',
                'description': 'Content mentions gender-related terms'
            },
            {
                'type': 'linguistic',
                'pattern': 'non-native',
                'description': 'Content may be from non-native speaker'
            }
        ]


# Public API functions

async def explain_moderation_decision(
    decision_id: str,
    content: str,
    decision: str,
    confidence: float,
    ai_responses: List[AIResponse],
    trust_profile: Optional[TrustProfile] = None,
    audience: ExplanationAudience = ExplanationAudience.END_USER,
    explanation_types: Optional[List[ExplanationType]] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> DecisionExplanation:
    """
    Public API function to explain AI moderation decisions.
    
    Args:
        decision_id: Unique identifier for the decision
        content: The content that was moderated
        decision: The moderation decision (APPROVE, FLAG, BLOCK)
        confidence: Confidence level of the decision
        ai_responses: List of AI provider responses
        trust_profile: User's trust profile (optional)
        audience: Target audience for explanation
        explanation_types: Types of explanations to generate
        user_id: User ID (optional)
        context: Additional context (optional)
        config: Engine configuration (optional)
    
    Returns:
        Comprehensive decision explanation
    """
    
    if explanation_types is None:
        explanation_types = [
            ExplanationType.DECISION_BREAKDOWN,
            ExplanationType.FEATURE_IMPORTANCE,
            ExplanationType.CONFIDENCE_ANALYSIS
        ]
    
    if context is None:
        context = {}
    
    if config is None:
        config = {}
    
    # Create explanation request
    request = ExplanationRequest(
        decision_id=decision_id,
        content=content,
        decision=decision,
        confidence=confidence,
        ai_responses=ai_responses,
        trust_profile=trust_profile,
        audience=audience,
        explanation_types=explanation_types,
        user_id=user_id,
        context=context
    )
    
    # Initialize engine and generate explanation
    engine = TrustStreamExplainabilityEngine(config)
    explanation = await engine.explain_decision(request)
    
    return explanation