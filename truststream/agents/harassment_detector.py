# Harassment Detection Agent for TrustStream v4.4
# Specialized agent for detecting and preventing harassment, bullying, and toxic behavior

import logging
import json
import re
from typing import Dict, Any, List, Set
from datetime import datetime, timedelta

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class HarassmentDetectorAgent(BaseAIAgent):
    """
    Harassment Detection Agent - Specialized Toxicity and Harassment Prevention
    
    This agent focuses on detecting and preventing harassment, bullying, toxic behavior,
    and personal attacks. It maintains a safe and respectful community environment.
    
    Key Responsibilities:
    - Harassment and bullying detection
    - Personal attack identification
    - Toxic behavior pattern analysis
    - Targeted harassment prevention
    - Hate speech detection
    - Cyberbullying intervention
    - Victim protection measures
    - Escalation to human moderators
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Harassment detection configuration
        self.harassment_thresholds = {
            'toxicity_threshold': 0.7,
            'personal_attack_threshold': 0.6,
            'harassment_pattern_threshold': 3,  # Number of incidents to flag pattern
            'escalation_threshold': 0.8
        }
        
        # Harassment indicators and patterns
        self.harassment_keywords = {
            'direct_insults': [
                'idiot', 'stupid', 'moron', 'loser', 'pathetic', 'worthless',
                'disgusting', 'ugly', 'freak', 'weirdo', 'creep'
            ],
            'personal_attacks': [
                'kill yourself', 'die', 'nobody likes you', 'you suck',
                'go away', 'shut up', 'you\'re trash', 'waste of space'
            ],
            'discriminatory_language': [
                # Note: This would include slurs and discriminatory terms
                # Implemented with careful consideration for context
                'discriminatory_pattern_detected'
            ],
            'threatening_language': [
                'threat', 'hurt you', 'find you', 'get you', 'destroy you',
                'ruin your life', 'make you pay', 'you\'ll regret'
            ]
        }
        
        # Harassment behavior patterns
        self.harassment_patterns = [
            'repeated_targeting',
            'coordinated_harassment',
            'doxxing_attempt',
            'impersonation',
            'stalking_behavior',
            'brigading'
        ]
        
        # Protected characteristics for hate speech detection
        self.protected_characteristics = [
            'race', 'ethnicity', 'religion', 'gender', 'sexual_orientation',
            'disability', 'age', 'nationality', 'political_affiliation'
        ]
        
        logger.info(f"Harassment Detection Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content for harassment, toxicity, and harmful behavior.
        
        The Harassment Detection Agent evaluates:
        - Direct harassment and personal attacks
        - Toxic language and behavior
        - Hate speech and discriminatory content
        - Threatening or intimidating language
        - Harassment patterns and targeting
        - Cyberbullying indicators
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Analyze harassment indicators
            harassment_analysis = await self._analyze_harassment_indicators(content, content_features)
            
            # Check for personal attacks
            personal_attack_analysis = await self._analyze_personal_attacks(content, context)
            
            # Analyze toxic behavior patterns
            toxicity_analysis = await self._analyze_toxicity_patterns(content, content_features)
            
            # Check for hate speech
            hate_speech_analysis = await self._analyze_hate_speech(content, content_features)
            
            # Analyze harassment patterns
            pattern_analysis = await self._analyze_harassment_patterns(content, context)
            
            # Get AI provider analysis
            ai_analysis = await self._get_ai_harassment_analysis(content, trust_score, context)
            
            # Make final harassment decision
            decision = await self._make_harassment_decision(
                content=content,
                trust_score=trust_score,
                harassment_analysis=harassment_analysis,
                personal_attack_analysis=personal_attack_analysis,
                toxicity_analysis=toxicity_analysis,
                hate_speech_analysis=hate_speech_analysis,
                pattern_analysis=pattern_analysis,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Harassment detection analysis failed: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.6,
                'reasoning': f'Harassment analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'harassment_detector', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Harassment Detection Agent."""
        return [
            'harassment_detection',
            'personal_attack_identification',
            'toxic_behavior_analysis',
            'hate_speech_detection',
            'cyberbullying_prevention',
            'threatening_language_detection',
            'harassment_pattern_analysis',
            'victim_protection',
            'discriminatory_content_detection',
            'coordinated_harassment_detection'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Harassment Detection Agent."""
        return (
            "Specialized agent for detecting and preventing harassment, bullying, and toxic behavior. "
            "Identifies personal attacks, hate speech, threatening language, and harassment patterns "
            "to maintain a safe and respectful community environment."
        )
    
    # Private analysis methods
    
    async def _analyze_harassment_indicators(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for direct harassment indicators."""
        try:
            text_content = content.get('content', '').lower()
            harassment_analysis = {
                'direct_insults_count': 0,
                'personal_attacks_count': 0,
                'threatening_language_count': 0,
                'harassment_keywords_found': [],
                'harassment_severity': 0.0
            }
            
            # Check for direct insults
            insults_found = []
            for insult in self.harassment_keywords['direct_insults']:
                if insult in text_content:
                    insults_found.append(insult)
                    harassment_analysis['direct_insults_count'] += 1
            
            # Check for personal attacks
            attacks_found = []
            for attack in self.harassment_keywords['personal_attacks']:
                if attack in text_content:
                    attacks_found.append(attack)
                    harassment_analysis['personal_attacks_count'] += 1
            
            # Check for threatening language
            threats_found = []
            for threat in self.harassment_keywords['threatening_language']:
                if threat in text_content:
                    threats_found.append(threat)
                    harassment_analysis['threatening_language_count'] += 1
            
            # Compile all found keywords
            harassment_analysis['harassment_keywords_found'] = insults_found + attacks_found + threats_found
            
            # Calculate harassment severity
            severity = 0
            if harassment_analysis['direct_insults_count'] > 0:
                severity += min(0.4, harassment_analysis['direct_insults_count'] * 0.2)
            if harassment_analysis['personal_attacks_count'] > 0:
                severity += min(0.5, harassment_analysis['personal_attacks_count'] * 0.25)
            if harassment_analysis['threatening_language_count'] > 0:
                severity += min(0.6, harassment_analysis['threatening_language_count'] * 0.3)
            
            harassment_analysis['harassment_severity'] = min(1.0, severity)
            
            return harassment_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze harassment indicators: {str(e)}")
            return {'harassment_severity': 0.3, 'error': str(e)}
    
    async def _analyze_personal_attacks(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for personal attacks and targeted harassment."""
        try:
            text_content = content.get('content', '')
            attack_analysis = {
                'is_targeted': False,
                'target_user': None,
                'attack_type': None,
                'attack_severity': 0.0,
                'requires_immediate_action': False
            }
            
            # Check if content mentions or targets specific users
            mentioned_users = context.get('mentioned_users', [])
            replied_to_user = context.get('replied_to_user')
            
            if mentioned_users or replied_to_user:
                attack_analysis['is_targeted'] = True
                attack_analysis['target_user'] = replied_to_user or mentioned_users[0] if mentioned_users else None
            
            # Analyze attack patterns
            text_lower = text_content.lower()
            
            # Direct personal attacks
            if any(attack in text_lower for attack in self.harassment_keywords['personal_attacks']):
                attack_analysis['attack_type'] = 'direct_personal_attack'
                attack_analysis['attack_severity'] = 0.8
                attack_analysis['requires_immediate_action'] = True
            
            # Character assassination
            character_attack_patterns = ['you always', 'you never', 'you are', 'typical of you']
            if any(pattern in text_lower for pattern in character_attack_patterns):
                if attack_analysis['attack_severity'] < 0.6:
                    attack_analysis['attack_type'] = 'character_attack'
                    attack_analysis['attack_severity'] = 0.6
            
            # Identity-based attacks
            if any(char in text_lower for char in self.protected_characteristics):
                negative_context = any(neg in text_lower for neg in ['because you are', 'typical', 'all you'])
                if negative_context:
                    attack_analysis['attack_type'] = 'identity_based_attack'
                    attack_analysis['attack_severity'] = max(attack_analysis['attack_severity'], 0.7)
                    attack_analysis['requires_immediate_action'] = True
            
            return attack_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze personal attacks: {str(e)}")
            return {'attack_severity': 0.3, 'error': str(e)}
    
    async def _analyze_toxicity_patterns(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for toxic behavior patterns."""
        try:
            text_content = content.get('content', '').lower()
            toxicity_analysis = {
                'toxicity_score': 0.0,
                'toxic_patterns': [],
                'aggression_level': 0.0,
                'dismissiveness_score': 0.0
            }
            
            # Analyze aggressive language patterns
            aggressive_patterns = [
                'shut up', 'get lost', 'go away', 'nobody asked',
                'who cares', 'so what', 'whatever', 'deal with it'
            ]
            
            aggression_count = sum(1 for pattern in aggressive_patterns if pattern in text_content)
            toxicity_analysis['aggression_level'] = min(1.0, aggression_count * 0.3)
            
            if aggression_count > 0:
                toxicity_analysis['toxic_patterns'].append('aggressive_language')
            
            # Analyze dismissive behavior
            dismissive_patterns = [
                'you don\'t understand', 'you\'re wrong', 'that\'s stupid',
                'you have no idea', 'you don\'t know', 'educate yourself'
            ]
            
            dismissive_count = sum(1 for pattern in dismissive_patterns if pattern in text_content)
            toxicity_analysis['dismissiveness_score'] = min(1.0, dismissive_count * 0.25)
            
            if dismissive_count > 0:
                toxicity_analysis['toxic_patterns'].append('dismissive_behavior')
            
            # Check for excessive capitalization (shouting)
            if content.get('content', ''):
                caps_ratio = sum(1 for c in content['content'] if c.isupper()) / len(content['content'])
                if caps_ratio > 0.5:
                    toxicity_analysis['toxic_patterns'].append('excessive_shouting')
                    toxicity_analysis['aggression_level'] = max(toxicity_analysis['aggression_level'], 0.4)
            
            # Calculate overall toxicity score
            toxicity_analysis['toxicity_score'] = max(
                toxicity_analysis['aggression_level'],
                toxicity_analysis['dismissiveness_score']
            )
            
            return toxicity_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze toxicity patterns: {str(e)}")
            return {'toxicity_score': 0.3, 'error': str(e)}
    
    async def _analyze_hate_speech(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for hate speech and discriminatory language."""
        try:
            text_content = content.get('content', '').lower()
            hate_speech_analysis = {
                'hate_speech_probability': 0.0,
                'targeted_characteristics': [],
                'discriminatory_language_detected': False,
                'hate_speech_type': None
            }
            
            # Check for discriminatory language patterns
            # This is a simplified implementation - real systems use more sophisticated detection
            discriminatory_indicators = [
                'all [group] are', 'typical [group]', '[group] people are',
                'i hate [group]', '[group] should', 'ban all [group]'
            ]
            
            # Check for hate speech patterns
            hate_patterns = [
                'should be banned', 'don\'t belong here', 'go back to',
                'not welcome', 'inferior', 'subhuman', 'vermin'
            ]
            
            hate_pattern_count = sum(1 for pattern in hate_patterns if pattern in text_content)
            
            if hate_pattern_count > 0:
                hate_speech_analysis['hate_speech_probability'] = min(1.0, hate_pattern_count * 0.4)
                hate_speech_analysis['discriminatory_language_detected'] = True
                hate_speech_analysis['hate_speech_type'] = 'general_hate_speech'
            
            # Check for references to protected characteristics in negative context
            for characteristic in self.protected_characteristics:
                if characteristic in text_content:
                    # Check if it's in a negative context
                    negative_context_words = ['hate', 'disgusting', 'wrong', 'bad', 'inferior', 'stupid']
                    if any(neg_word in text_content for neg_word in negative_context_words):
                        hate_speech_analysis['targeted_characteristics'].append(characteristic)
                        hate_speech_analysis['hate_speech_probability'] = max(
                            hate_speech_analysis['hate_speech_probability'], 0.6
                        )
                        hate_speech_analysis['hate_speech_type'] = 'targeted_hate_speech'
            
            return hate_speech_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze hate speech: {str(e)}")
            return {'hate_speech_probability': 0.2, 'error': str(e)}
    
    async def _analyze_harassment_patterns(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze for harassment patterns and coordinated attacks."""
        try:
            pattern_analysis = {
                'repeated_targeting': False,
                'coordinated_harassment': False,
                'harassment_pattern_score': 0.0,
                'pattern_type': None
            }
            
            author_id = content.get('author_id')
            target_user = context.get('replied_to_user') or context.get('mentioned_users', [None])[0]
            
            if author_id and target_user:
                # Check for repeated targeting (this would query historical data)
                # For now, simulate pattern detection
                recent_interactions = context.get('recent_author_interactions', [])
                
                # Count recent negative interactions with the same user
                negative_interactions = [
                    interaction for interaction in recent_interactions
                    if interaction.get('target_user') == target_user and
                    interaction.get('sentiment', 'neutral') == 'negative'
                ]
                
                if len(negative_interactions) >= self.harassment_thresholds['harassment_pattern_threshold']:
                    pattern_analysis['repeated_targeting'] = True
                    pattern_analysis['harassment_pattern_score'] = 0.8
                    pattern_analysis['pattern_type'] = 'repeated_targeting'
            
            # Check for coordinated harassment indicators
            # This would analyze timing, similar language, etc.
            if context.get('similar_content_recently', False):
                pattern_analysis['coordinated_harassment'] = True
                pattern_analysis['harassment_pattern_score'] = max(
                    pattern_analysis['harassment_pattern_score'], 0.7
                )
                pattern_analysis['pattern_type'] = 'coordinated_harassment'
            
            return pattern_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze harassment patterns: {str(e)}")
            return {'harassment_pattern_score': 0.2, 'error': str(e)}
    
    async def _get_ai_harassment_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on harassment detection."""
        try:
            prompt = self._create_harassment_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (Claude for harassment detection)
            if 'claude' in self.ai_providers:
                response = await self._call_ai_provider(
                    provider='claude',
                    prompt=prompt,
                    content=content_text,
                    additional_context=context
                )
                
                return await self._parse_ai_response(response['response'], 'claude')
            
            # Fallback to other providers
            for provider in ['openai', 'gemini']:
                if provider in self.ai_providers:
                    try:
                        response = await self._call_ai_provider(
                            provider=provider,
                            prompt=prompt,
                            content=content_text,
                            additional_context=context
                        )
                        
                        return await self._parse_ai_response(response['response'], provider)
                        
                    except Exception as e:
                        logger.warning(f"AI provider {provider} failed: {str(e)}")
                        continue
            
            # No AI providers available
            return {
                'action': 'flag',
                'confidence': 0.5,
                'reasoning': 'No AI providers available for harassment analysis'
            }
            
        except Exception as e:
            logger.error(f"AI harassment analysis failed: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_harassment_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a harassment-focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='harassment, toxicity, and harmful behavior detection'
        )
        
        harassment_specific = f"""
HARASSMENT DETECTION ANALYSIS

You are a specialized Harassment Detection Agent focused on identifying and preventing
harassment, bullying, toxic behavior, and personal attacks.

User Trust Context:
- Author Trust Score: {trust_score}
- Target User: {context.get('replied_to_user', 'None')}
- Mentioned Users: {context.get('mentioned_users', [])}

Harassment Detection Criteria:
1. Personal Attacks: Direct insults, character assassination, identity-based attacks
2. Threatening Language: Threats of harm, intimidation, doxxing attempts
3. Toxic Behavior: Aggressive language, dismissiveness, excessive hostility
4. Hate Speech: Discriminatory language targeting protected characteristics
5. Harassment Patterns: Repeated targeting, coordinated attacks, stalking behavior
6. Cyberbullying: Systematic intimidation, social exclusion, public humiliation

Decision Guidelines:
- REMOVE: Direct threats, severe harassment, hate speech
- FLAG: Potential harassment that needs human review
- WARN: Toxic behavior that warrants user education
- APPROVE: Content that doesn't violate harassment policies

Harassment Thresholds:
- Toxicity threshold: {self.harassment_thresholds['toxicity_threshold']}
- Personal attack threshold: {self.harassment_thresholds['personal_attack_threshold']}
- Escalation threshold: {self.harassment_thresholds['escalation_threshold']}

CRITICAL: Prioritize victim safety and community well-being. When in doubt about
potential harassment, err on the side of caution and flag for human review.
Consider the power dynamics and potential for harm in your analysis.
"""
        
        return base_prompt + harassment_specific
    
    async def _make_harassment_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        harassment_analysis: Dict[str, Any],
        personal_attack_analysis: Dict[str, Any],
        toxicity_analysis: Dict[str, Any],
        hate_speech_analysis: Dict[str, Any],
        pattern_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make final harassment-based moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Extract key metrics
            harassment_severity = harassment_analysis.get('harassment_severity', 0.0)
            attack_severity = personal_attack_analysis.get('attack_severity', 0.0)
            toxicity_score = toxicity_analysis.get('toxicity_score', 0.0)
            hate_speech_probability = hate_speech_analysis.get('hate_speech_probability', 0.0)
            pattern_score = pattern_analysis.get('harassment_pattern_score', 0.0)
            
            # Determine highest severity
            max_severity = max(harassment_severity, attack_severity, toxicity_score, 
                             hate_speech_probability, pattern_score)
            
            # Make decision based on severity and patterns
            if (hate_speech_probability > 0.7 or 
                personal_attack_analysis.get('requires_immediate_action', False) or
                harassment_severity > self.harassment_thresholds['escalation_threshold']):
                
                base_decision['action'] = 'remove'
                base_decision['confidence'] = 0.9
                base_decision['reasoning'] = 'Severe harassment or hate speech detected - immediate removal required'
                base_decision['escalate_to_human'] = True
                
            elif (max_severity > self.harassment_thresholds['toxicity_threshold'] or
                  pattern_analysis.get('repeated_targeting', False)):
                
                base_decision['action'] = 'flag'
                base_decision['confidence'] = 0.8
                base_decision['reasoning'] = 'Potential harassment detected - requires human review'
                base_decision['escalate_to_human'] = True
                
            elif max_severity > 0.4:
                if trust_score > 0.7:
                    base_decision['action'] = 'warn'
                    base_decision['reasoning'] = 'Toxic behavior from trusted user - education opportunity'
                else:
                    base_decision['action'] = 'flag'
                    base_decision['reasoning'] = 'Toxic behavior requires review'
            
            # Special handling for targeted harassment
            if personal_attack_analysis.get('is_targeted', False):
                if base_decision['action'] == 'approve' and max_severity > 0.3:
                    base_decision['action'] = 'flag'
                    base_decision['reasoning'] += ' (Targeted content requires review)'
                
                # Notify target user if harassment is detected
                if max_severity > 0.5:
                    base_decision['notify_target'] = True
                    base_decision['target_user'] = personal_attack_analysis.get('target_user')
            
            # Add harassment-specific metadata
            base_decision['metadata'] = {
                'agent': 'harassment_detector',
                'harassment_severity': round(harassment_severity, 3),
                'attack_severity': round(attack_severity, 3),
                'toxicity_score': round(toxicity_score, 3),
                'hate_speech_probability': round(hate_speech_probability, 3),
                'pattern_score': round(pattern_score, 3),
                'max_severity': round(max_severity, 3),
                'trust_score': trust_score,
                'is_targeted': personal_attack_analysis.get('is_targeted', False)
            }
            
            # Add detailed evidence
            base_decision['evidence'] = {
                'harassment_analysis': harassment_analysis,
                'personal_attack_analysis': personal_attack_analysis,
                'toxicity_analysis': toxicity_analysis,
                'hate_speech_analysis': hate_speech_analysis,
                'pattern_analysis': pattern_analysis,
                'ai_analysis': ai_analysis
            }
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make harassment decision: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.6,
                'reasoning': f'Harassment decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'harassment_detector', 'error': True},
                'escalate_to_human': True
            }