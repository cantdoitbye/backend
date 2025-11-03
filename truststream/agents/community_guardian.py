# Community Guardian Agent for TrustStream v4.4
# The primary AI moderator responsible for overall community health and safety

import logging
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class CommunityGuardianAgent(BaseAIAgent):
    """
    Community Guardian Agent - The Primary AI Moderator
    
    This agent serves as the central guardian of community health and safety.
    It has the broadest scope of responsibility and coordinates with other
    specialized agents to maintain community standards.
    
    Key Responsibilities:
    - Overall community health monitoring
    - Coordinating with specialized agents
    - Escalating serious violations
    - Maintaining community culture and values
    - Emergency response coordination
    - User behavior pattern analysis
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Community Guardian specific configuration
        self.escalation_threshold = 0.8
        self.pattern_analysis_window = timedelta(hours=24)
        self.community_health_metrics = {
            'toxicity_trend': [],
            'engagement_quality': [],
            'rule_violations': [],
            'user_satisfaction': []
        }
        
        logger.info(f"Community Guardian Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content from a holistic community health perspective.
        
        The Community Guardian takes a comprehensive approach, considering:
        - Content safety and appropriateness
        - Community culture alignment
        - User behavior patterns
        - Potential for escalation
        - Impact on community health
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features for analysis
            content_features = self._extract_content_features(content)
            
            # Get user behavior history
            user_history = await self._get_user_behavior_history(content.get('author_id'))
            
            # Analyze content using multiple AI providers for consensus
            ai_analyses = await self._get_multi_provider_analysis(content, trust_score, context)
            
            # Perform pattern analysis
            pattern_analysis = await self._analyze_behavior_patterns(content, user_history)
            
            # Calculate community impact score
            community_impact = await self._calculate_community_impact(content, content_features)
            
            # Make final decision based on all factors
            decision = await self._make_guardian_decision(
                content=content,
                trust_score=trust_score,
                ai_analyses=ai_analyses,
                pattern_analysis=pattern_analysis,
                community_impact=community_impact,
                content_features=content_features
            )
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Community Guardian analysis failed: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.3,
                'reasoning': f'Analysis failed due to error: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'community_guardian', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Community Guardian Agent."""
        return [
            'holistic_content_analysis',
            'community_health_monitoring',
            'behavior_pattern_analysis',
            'emergency_response',
            'multi_agent_coordination',
            'escalation_management',
            'culture_preservation',
            'user_education',
            'trend_analysis',
            'risk_assessment'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Community Guardian Agent."""
        return (
            "Primary AI moderator responsible for overall community health and safety. "
            "Provides holistic content analysis, coordinates with specialized agents, "
            "monitors behavior patterns, and maintains community culture and values."
        )
    
    async def get_community_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive community health report.
        
        Returns:
            Dictionary containing community health metrics and insights
        """
        try:
            # Calculate health scores
            toxicity_score = await self._calculate_toxicity_trend()
            engagement_score = await self._calculate_engagement_quality()
            safety_score = await self._calculate_safety_score()
            culture_score = await self._calculate_culture_alignment()
            
            # Overall health score (weighted average)
            overall_health = (
                toxicity_score * 0.3 +
                engagement_score * 0.25 +
                safety_score * 0.3 +
                culture_score * 0.15
            )
            
            return {
                'community_id': self.community_id,
                'overall_health_score': round(overall_health, 3),
                'metrics': {
                    'toxicity_trend': round(toxicity_score, 3),
                    'engagement_quality': round(engagement_score, 3),
                    'safety_score': round(safety_score, 3),
                    'culture_alignment': round(culture_score, 3)
                },
                'recommendations': await self._generate_health_recommendations(overall_health),
                'alerts': await self._get_active_alerts(),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate community health report: {str(e)}")
            return {
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    # Private helper methods
    
    async def _get_multi_provider_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get analysis from multiple AI providers for consensus."""
        analyses = []
        
        # Create comprehensive analysis prompt
        prompt = self._create_guardian_prompt(content, trust_score, context)
        content_text = content.get('content', '')
        
        # Try multiple AI providers for consensus
        providers_to_try = ['openai', 'claude', 'gemini']
        
        for provider in providers_to_try:
            if provider in self.ai_providers:
                try:
                    response = await self._call_ai_provider(
                        provider=provider,
                        prompt=prompt,
                        content=content_text,
                        additional_context=context
                    )
                    
                    # Parse AI response
                    analysis = await self._parse_ai_response(response['response'], provider)
                    if analysis:
                        analyses.append({
                            'provider': provider,
                            'analysis': analysis,
                            'raw_response': response
                        })
                        
                except Exception as e:
                    logger.warning(f"AI provider {provider} failed: {str(e)}")
                    continue
        
        return analyses
    
    def _create_guardian_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a comprehensive prompt for the Community Guardian analysis."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='comprehensive community health and safety'
        )
        
        guardian_specific = f"""
COMMUNITY GUARDIAN ANALYSIS

You are the primary AI moderator responsible for overall community health and safety.
Your analysis should be comprehensive and consider multiple factors:

User Trust Context:
- Author Trust Score: {trust_score}
- Trust Level: {'High' if trust_score > 0.7 else 'Medium' if trust_score > 0.4 else 'Low'}

Community Context:
- Community Size: {self.community_analysis.get('size', 'unknown')}
- Risk Level: {self.community_analysis.get('risk_level', 'medium')}
- Primary Language: {self.community_analysis.get('primary_language', 'en')}

Analysis Focus Areas:
1. Content Safety: Harmful, toxic, or dangerous content
2. Community Standards: Alignment with community values and rules
3. User Behavior: Patterns that might indicate problematic behavior
4. Community Impact: Potential effect on community health and engagement
5. Escalation Risk: Likelihood of content causing conflicts or issues

Decision Guidelines:
- APPROVE: Content is safe, appropriate, and positive for community
- FLAG: Content needs human review or has minor issues
- WARN: Content violates guidelines but user can be educated
- REMOVE: Content clearly violates policies and harms community

Consider the user's trust score in your decision:
- High trust users (>0.7): Give benefit of doubt, prefer education over punishment
- Medium trust users (0.4-0.7): Standard enforcement
- Low trust users (<0.4): Stricter enforcement, closer monitoring

Provide detailed reasoning and specific evidence for your decision.
"""
        
        return base_prompt + guardian_specific
    
    async def _parse_ai_response(self, response: str, provider: str) -> Dict[str, Any]:
        """Parse AI provider response into structured analysis."""
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                
                analysis = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['action', 'confidence', 'reasoning']
                if all(field in analysis for field in required_fields):
                    # Ensure confidence is a float between 0 and 1
                    analysis['confidence'] = max(0.0, min(1.0, float(analysis['confidence'])))
                    
                    # Ensure action is valid
                    valid_actions = ['approve', 'flag', 'remove', 'warn']
                    if analysis['action'].lower() not in valid_actions:
                        analysis['action'] = 'flag'
                    
                    analysis['provider'] = provider
                    return analysis
            
            # If JSON parsing fails, try to extract key information
            return self._extract_analysis_from_text(response, provider)
            
        except Exception as e:
            logger.error(f"Failed to parse AI response from {provider}: {str(e)}")
            return None
    
    def _extract_analysis_from_text(self, response: str, provider: str) -> Dict[str, Any]:
        """Extract analysis from unstructured text response."""
        response_lower = response.lower()
        
        # Determine action based on keywords
        if any(word in response_lower for word in ['remove', 'delete', 'ban', 'harmful']):
            action = 'remove'
            confidence = 0.8
        elif any(word in response_lower for word in ['flag', 'review', 'concern', 'questionable']):
            action = 'flag'
            confidence = 0.6
        elif any(word in response_lower for word in ['warn', 'educate', 'minor', 'guideline']):
            action = 'warn'
            confidence = 0.7
        else:
            action = 'approve'
            confidence = 0.5
        
        return {
            'action': action,
            'confidence': confidence,
            'reasoning': f'Analysis from {provider}: {response[:200]}...',
            'provider': provider,
            'parsed_from_text': True
        }
    
    async def _get_user_behavior_history(self, user_id: str) -> Dict[str, Any]:
        """Get user behavior history for pattern analysis."""
        try:
            # This would integrate with existing user activity tracking
            # For now, return mock data structure
            return {
                'user_id': user_id,
                'recent_violations': 0,
                'trust_trend': 'stable',
                'engagement_pattern': 'normal',
                'warning_count': 0,
                'last_violation': None,
                'account_age_days': 30
            }
            
        except Exception as e:
            logger.error(f"Failed to get user behavior history: {str(e)}")
            return {}
    
    async def _analyze_behavior_patterns(
        self, 
        content: Dict[str, Any], 
        user_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns for risk assessment."""
        try:
            patterns = {
                'risk_level': 'low',
                'concerning_patterns': [],
                'positive_indicators': [],
                'recommendations': []
            }
            
            # Analyze posting frequency
            if user_history.get('recent_violations', 0) > 2:
                patterns['risk_level'] = 'high'
                patterns['concerning_patterns'].append('multiple_recent_violations')
                patterns['recommendations'].append('increased_monitoring')
            
            # Analyze account age vs behavior
            account_age = user_history.get('account_age_days', 0)
            if account_age < 7 and user_history.get('warning_count', 0) > 0:
                patterns['risk_level'] = 'medium'
                patterns['concerning_patterns'].append('new_account_with_warnings')
                patterns['recommendations'].append('new_user_education')
            
            # Positive indicators
            if user_history.get('trust_trend') == 'improving':
                patterns['positive_indicators'].append('improving_trust_score')
            
            if account_age > 90 and user_history.get('recent_violations', 0) == 0:
                patterns['positive_indicators'].append('established_good_standing')
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze behavior patterns: {str(e)}")
            return {'risk_level': 'unknown', 'error': str(e)}
    
    async def _calculate_community_impact(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate potential impact of content on community health."""
        try:
            impact = {
                'visibility_score': 0.5,
                'engagement_potential': 0.5,
                'controversy_risk': 0.3,
                'educational_value': 0.4,
                'overall_impact': 0.4
            }
            
            # Calculate visibility based on content characteristics
            if content_features.get('has_mentions', False):
                impact['visibility_score'] += 0.2
            
            if content_features.get('has_hashtags', False):
                impact['visibility_score'] += 0.1
            
            # Engagement potential based on content type and length
            word_count = content_features.get('word_count', 0)
            if 50 <= word_count <= 200:  # Optimal length for engagement
                impact['engagement_potential'] += 0.2
            
            # Controversy risk based on content analysis
            text_content = content.get('content', '').lower()
            controversial_topics = ['politics', 'religion', 'controversial', 'debate']
            if any(topic in text_content for topic in controversial_topics):
                impact['controversy_risk'] += 0.3
            
            # Educational value
            educational_indicators = ['learn', 'explain', 'understand', 'knowledge', 'help']
            if any(indicator in text_content for indicator in educational_indicators):
                impact['educational_value'] += 0.3
            
            # Calculate overall impact
            impact['overall_impact'] = (
                impact['visibility_score'] * 0.3 +
                impact['engagement_potential'] * 0.25 +
                (1 - impact['controversy_risk']) * 0.25 +  # Lower controversy = positive impact
                impact['educational_value'] * 0.2
            )
            
            return impact
            
        except Exception as e:
            logger.error(f"Failed to calculate community impact: {str(e)}")
            return {'overall_impact': 0.5, 'error': str(e)}
    
    async def _make_guardian_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        ai_analyses: List[Dict[str, Any]],
        pattern_analysis: Dict[str, Any],
        community_impact: Dict[str, Any],
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make final moderation decision based on all analysis factors."""
        try:
            # Aggregate AI provider decisions
            if ai_analyses:
                ai_decision = self._aggregate_ai_decisions(ai_analyses)
            else:
                ai_decision = {'action': 'flag', 'confidence': 0.3, 'reasoning': 'No AI analysis available'}
            
            # Adjust decision based on trust score
            adjusted_decision = self._adjust_for_trust_score(ai_decision, trust_score)
            
            # Adjust based on behavior patterns
            pattern_adjusted = self._adjust_for_patterns(adjusted_decision, pattern_analysis)
            
            # Adjust based on community impact
            final_decision = self._adjust_for_community_impact(pattern_adjusted, community_impact)
            
            # Add Guardian-specific metadata
            final_decision['metadata'] = {
                'agent': 'community_guardian',
                'trust_score': trust_score,
                'ai_consensus': len(ai_analyses),
                'risk_level': pattern_analysis.get('risk_level', 'unknown'),
                'community_impact': community_impact.get('overall_impact', 0.5),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            # Add evidence from all sources
            final_decision['evidence'] = {
                'ai_analyses': [analysis['analysis'] for analysis in ai_analyses],
                'behavior_patterns': pattern_analysis,
                'community_impact': community_impact,
                'content_features': content_features
            }
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Failed to make guardian decision: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.3,
                'reasoning': f'Decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'community_guardian', 'error': True}
            }
    
    def _aggregate_ai_decisions(self, ai_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate decisions from multiple AI providers."""
        if not ai_analyses:
            return {'action': 'flag', 'confidence': 0.3, 'reasoning': 'No AI analysis'}
        
        # Count votes for each action
        action_votes = {}
        confidence_sum = 0
        reasoning_parts = []
        
        for analysis in ai_analyses:
            ai_result = analysis['analysis']
            action = ai_result.get('action', 'flag')
            confidence = ai_result.get('confidence', 0.5)
            
            action_votes[action] = action_votes.get(action, 0) + confidence
            confidence_sum += confidence
            reasoning_parts.append(f"{analysis['provider']}: {ai_result.get('reasoning', 'No reasoning')}")
        
        # Determine consensus action
        consensus_action = max(action_votes, key=action_votes.get)
        average_confidence = confidence_sum / len(ai_analyses)
        
        return {
            'action': consensus_action,
            'confidence': round(average_confidence, 3),
            'reasoning': '; '.join(reasoning_parts),
            'consensus_strength': len(ai_analyses)
        }
    
    def _adjust_for_trust_score(self, decision: Dict[str, Any], trust_score: float) -> Dict[str, Any]:
        """Adjust decision based on user trust score."""
        adjusted = decision.copy()
        
        if trust_score > 0.8:  # High trust users
            if decision['action'] == 'remove':
                adjusted['action'] = 'flag'  # Give benefit of doubt
                adjusted['confidence'] *= 0.9
                adjusted['reasoning'] += ' (Adjusted for high trust user)'
        elif trust_score < 0.3:  # Low trust users
            if decision['action'] == 'approve':
                adjusted['action'] = 'flag'  # Extra scrutiny
                adjusted['confidence'] *= 0.8
                adjusted['reasoning'] += ' (Adjusted for low trust user)'
        
        return adjusted
    
    def _adjust_for_patterns(self, decision: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust decision based on behavior patterns."""
        adjusted = decision.copy()
        risk_level = pattern_analysis.get('risk_level', 'low')
        
        if risk_level == 'high':
            if decision['action'] == 'approve':
                adjusted['action'] = 'flag'
                adjusted['reasoning'] += ' (High risk behavior pattern detected)'
        elif risk_level == 'low' and pattern_analysis.get('positive_indicators'):
            if decision['action'] == 'flag':
                adjusted['action'] = 'approve'
                adjusted['reasoning'] += ' (Positive behavior patterns noted)'
        
        return adjusted
    
    def _adjust_for_community_impact(self, decision: Dict[str, Any], community_impact: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust decision based on potential community impact."""
        adjusted = decision.copy()
        impact_score = community_impact.get('overall_impact', 0.5)
        controversy_risk = community_impact.get('controversy_risk', 0.3)
        
        if controversy_risk > 0.7 and decision['action'] == 'approve':
            adjusted['action'] = 'flag'
            adjusted['reasoning'] += ' (High controversy risk)'
        elif impact_score > 0.8 and decision['action'] == 'remove':
            adjusted['action'] = 'flag'
            adjusted['reasoning'] += ' (High positive community impact)'
        
        return adjusted
    
    # Community health monitoring methods
    
    async def _calculate_toxicity_trend(self) -> float:
        """Calculate community toxicity trend score."""
        # This would analyze recent moderation decisions and trends
        # For now, return a mock score
        return 0.75  # 0.75 = low toxicity (good)
    
    async def _calculate_engagement_quality(self) -> float:
        """Calculate community engagement quality score."""
        # This would analyze engagement patterns and quality
        return 0.82
    
    async def _calculate_safety_score(self) -> float:
        """Calculate community safety score."""
        # This would analyze safety incidents and violations
        return 0.88
    
    async def _calculate_culture_alignment(self) -> float:
        """Calculate how well content aligns with community culture."""
        # This would analyze cultural fit and community values
        return 0.79
    
    async def _generate_health_recommendations(self, overall_health: float) -> List[str]:
        """Generate recommendations based on community health score."""
        recommendations = []
        
        if overall_health < 0.6:
            recommendations.extend([
                'Increase moderation vigilance',
                'Review community guidelines',
                'Consider additional AI agent deployment'
            ])
        elif overall_health < 0.8:
            recommendations.extend([
                'Monitor trending topics closely',
                'Encourage positive engagement',
                'Review user education materials'
            ])
        else:
            recommendations.extend([
                'Maintain current moderation approach',
                'Celebrate community achievements',
                'Consider expanding community features'
            ])
        
        return recommendations
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts for the community."""
        # This would check for active issues requiring attention
        return [
            {
                'type': 'trend_monitoring',
                'message': 'Monitoring increased activity in political discussions',
                'severity': 'medium',
                'created_at': datetime.utcnow().isoformat()
            }
        ]