# Misinformation Guardian Agent for TrustStream v4.4
# Specialized agent for detecting and preventing misinformation, false claims, and conspiracy theories

import logging
import json
import re
from typing import Dict, Any, List, Set
from datetime import datetime, timedelta

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class MisinformationGuardianAgent(BaseAIAgent):
    """
    Misinformation Guardian Agent - Specialized False Information Detection
    
    This agent focuses on detecting and preventing the spread of misinformation,
    false claims, conspiracy theories, and unverified information that could
    cause harm to individuals or communities.
    
    Key Responsibilities:
    - Misinformation and disinformation detection
    - Fact-checking and source verification
    - Conspiracy theory identification
    - Health misinformation prevention
    - Political misinformation monitoring
    - Scientific misinformation detection
    - Rumor and hoax identification
    - Source credibility assessment
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Misinformation detection configuration
        self.misinformation_thresholds = {
            'false_claim_threshold': 0.7,
            'conspiracy_threshold': 0.6,
            'health_misinformation_threshold': 0.8,  # Lower threshold for health claims
            'source_credibility_threshold': 0.4
        }
        
        # High-risk misinformation categories
        self.high_risk_categories = {
            'health_medical': [
                'cure', 'treatment', 'vaccine', 'medicine', 'disease', 'virus',
                'pandemic', 'epidemic', 'symptoms', 'diagnosis', 'therapy'
            ],
            'political_electoral': [
                'election', 'voting', 'ballot', 'fraud', 'rigged', 'stolen',
                'candidate', 'poll', 'democracy', 'government'
            ],
            'financial_economic': [
                'investment', 'stock', 'crypto', 'bitcoin', 'trading', 'market',
                'economy', 'recession', 'inflation', 'financial advice'
            ],
            'scientific_climate': [
                'climate change', 'global warming', 'research', 'study', 'scientist',
                'data', 'evidence', 'peer review', 'journal'
            ]
        }
        
        # Misinformation indicators
        self.misinformation_indicators = {
            'absolute_claims': [
                'always', 'never', 'all', 'none', 'every', 'completely',
                'totally', 'absolutely', 'definitely', '100%'
            ],
            'conspiracy_language': [
                'they don\'t want you to know', 'hidden truth', 'cover up',
                'conspiracy', 'secret agenda', 'wake up', 'sheeple',
                'mainstream media lies', 'do your own research'
            ],
            'urgency_manipulation': [
                'act now', 'before it\'s too late', 'time is running out',
                'urgent', 'emergency', 'crisis', 'immediate action'
            ],
            'authority_rejection': [
                'experts are wrong', 'don\'t trust', 'they\'re lying',
                'fake news', 'propaganda', 'brainwashed', 'controlled'
            ]
        }
        
        # Credible source indicators
        self.credible_source_indicators = [
            'peer-reviewed', 'published in', 'research shows', 'study found',
            'according to experts', 'scientific evidence', 'data indicates',
            'clinical trial', 'meta-analysis', 'systematic review'
        ]
        
        # Unreliable source indicators
        self.unreliable_source_indicators = [
            'blog post', 'social media', 'anonymous source', 'rumor has it',
            'someone told me', 'I heard that', 'word on the street',
            'unverified report', 'alleged', 'supposedly'
        ]
        
        logger.info(f"Misinformation Guardian Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content for misinformation, false claims, and conspiracy theories.
        
        The Misinformation Guardian Agent evaluates:
        - False or misleading claims
        - Conspiracy theories and unfounded theories
        - Health and medical misinformation
        - Political and electoral misinformation
        - Source credibility and verification
        - Scientific misinformation
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Categorize content by risk level
            risk_categorization = await self._categorize_content_risk(content, content_features)
            
            # Analyze misinformation indicators
            misinformation_analysis = await self._analyze_misinformation_indicators(content, content_features)
            
            # Check for conspiracy theories
            conspiracy_analysis = await self._analyze_conspiracy_theories(content, content_features)
            
            # Assess source credibility
            source_analysis = await self._analyze_source_credibility(content, context)
            
            # Analyze factual claims
            factual_analysis = await self._analyze_factual_claims(content, content_features)
            
            # Get AI provider analysis
            ai_analysis = await self._get_ai_misinformation_analysis(content, trust_score, context)
            
            # Make final misinformation decision
            decision = await self._make_misinformation_decision(
                content=content,
                trust_score=trust_score,
                risk_categorization=risk_categorization,
                misinformation_analysis=misinformation_analysis,
                conspiracy_analysis=conspiracy_analysis,
                source_analysis=source_analysis,
                factual_analysis=factual_analysis,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Misinformation analysis failed: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.6,
                'reasoning': f'Misinformation analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'misinformation_guardian', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Misinformation Guardian Agent."""
        return [
            'misinformation_detection',
            'fact_checking',
            'conspiracy_theory_identification',
            'health_misinformation_prevention',
            'political_misinformation_monitoring',
            'scientific_misinformation_detection',
            'source_credibility_assessment',
            'rumor_detection',
            'hoax_identification',
            'false_claim_verification'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Misinformation Guardian Agent."""
        return (
            "Specialized agent for detecting and preventing misinformation, false claims, and conspiracy theories. "
            "Focuses on fact-checking, source verification, and preventing the spread of harmful false information "
            "across health, political, scientific, and other critical domains."
        )
    
    # Private analysis methods
    
    async def _categorize_content_risk(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Categorize content by misinformation risk level."""
        try:
            text_content = content.get('content', '').lower()
            risk_categorization = {
                'risk_categories': [],
                'risk_level': 'low',
                'high_risk_keywords_found': [],
                'requires_fact_checking': False
            }
            
            # Check each high-risk category
            for category, keywords in self.high_risk_categories.items():
                keywords_found = [keyword for keyword in keywords if keyword in text_content]
                if keywords_found:
                    risk_categorization['risk_categories'].append(category)
                    risk_categorization['high_risk_keywords_found'].extend(keywords_found)
            
            # Determine risk level
            if risk_categorization['risk_categories']:
                if 'health_medical' in risk_categorization['risk_categories']:
                    risk_categorization['risk_level'] = 'critical'
                    risk_categorization['requires_fact_checking'] = True
                elif len(risk_categorization['risk_categories']) > 1:
                    risk_categorization['risk_level'] = 'high'
                    risk_categorization['requires_fact_checking'] = True
                else:
                    risk_categorization['risk_level'] = 'medium'
            
            # Check for claims that require verification
            claim_indicators = ['studies show', 'research proves', 'scientists say', 'data shows']
            if any(indicator in text_content for indicator in claim_indicators):
                risk_categorization['requires_fact_checking'] = True
            
            return risk_categorization
            
        except Exception as e:
            logger.error(f"Failed to categorize content risk: {str(e)}")
            return {'risk_level': 'medium', 'error': str(e)}
    
    async def _analyze_misinformation_indicators(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for misinformation indicators."""
        try:
            text_content = content.get('content', '').lower()
            misinformation_analysis = {
                'absolute_claims_count': 0,
                'conspiracy_language_count': 0,
                'urgency_manipulation_count': 0,
                'authority_rejection_count': 0,
                'misinformation_score': 0.0,
                'indicators_found': []
            }
            
            # Check for absolute claims
            absolute_claims = [claim for claim in self.misinformation_indicators['absolute_claims'] 
                             if claim in text_content]
            misinformation_analysis['absolute_claims_count'] = len(absolute_claims)
            if absolute_claims:
                misinformation_analysis['indicators_found'].extend(absolute_claims)
            
            # Check for conspiracy language
            conspiracy_language = [lang for lang in self.misinformation_indicators['conspiracy_language'] 
                                 if lang in text_content]
            misinformation_analysis['conspiracy_language_count'] = len(conspiracy_language)
            if conspiracy_language:
                misinformation_analysis['indicators_found'].extend(conspiracy_language)
            
            # Check for urgency manipulation
            urgency_manipulation = [urgency for urgency in self.misinformation_indicators['urgency_manipulation'] 
                                  if urgency in text_content]
            misinformation_analysis['urgency_manipulation_count'] = len(urgency_manipulation)
            if urgency_manipulation:
                misinformation_analysis['indicators_found'].extend(urgency_manipulation)
            
            # Check for authority rejection
            authority_rejection = [auth for auth in self.misinformation_indicators['authority_rejection'] 
                                 if auth in text_content]
            misinformation_analysis['authority_rejection_count'] = len(authority_rejection)
            if authority_rejection:
                misinformation_analysis['indicators_found'].extend(authority_rejection)
            
            # Calculate misinformation score
            score = 0
            score += min(0.3, misinformation_analysis['absolute_claims_count'] * 0.1)
            score += min(0.4, misinformation_analysis['conspiracy_language_count'] * 0.2)
            score += min(0.2, misinformation_analysis['urgency_manipulation_count'] * 0.1)
            score += min(0.3, misinformation_analysis['authority_rejection_count'] * 0.15)
            
            misinformation_analysis['misinformation_score'] = min(1.0, score)
            
            return misinformation_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze misinformation indicators: {str(e)}")
            return {'misinformation_score': 0.3, 'error': str(e)}
    
    async def _analyze_conspiracy_theories(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for conspiracy theory patterns."""
        try:
            text_content = content.get('content', '').lower()
            conspiracy_analysis = {
                'conspiracy_probability': 0.0,
                'conspiracy_patterns': [],
                'conspiracy_type': None
            }
            
            # Common conspiracy theory patterns
            conspiracy_patterns = {
                'secret_control': ['secret society', 'illuminati', 'new world order', 'deep state', 'shadow government'],
                'cover_up': ['cover up', 'hiding the truth', 'suppressed information', 'censored'],
                'false_flag': ['false flag', 'staged', 'crisis actor', 'fake event'],
                'population_control': ['population control', 'depopulation', 'agenda 21', 'great reset'],
                'mind_control': ['mind control', 'brainwashing', 'programming', 'manipulation']
            }
            
            # Check for conspiracy patterns
            for pattern_type, keywords in conspiracy_patterns.items():
                if any(keyword in text_content for keyword in keywords):
                    conspiracy_analysis['conspiracy_patterns'].append(pattern_type)
                    conspiracy_analysis['conspiracy_probability'] += 0.2
            
            # Check for conspiracy theory structure
            if ('they' in text_content and 
                any(word in text_content for word in ['control', 'plan', 'agenda', 'scheme'])):
                conspiracy_analysis['conspiracy_probability'] += 0.1
                conspiracy_analysis['conspiracy_patterns'].append('vague_they_control')
            
            # Check for evidence rejection patterns
            evidence_rejection = ['ignore the evidence', 'fake studies', 'bought scientists', 'paid research']
            if any(rejection in text_content for rejection in evidence_rejection):
                conspiracy_analysis['conspiracy_probability'] += 0.15
                conspiracy_analysis['conspiracy_patterns'].append('evidence_rejection')
            
            # Determine conspiracy type
            if conspiracy_analysis['conspiracy_patterns']:
                if len(conspiracy_analysis['conspiracy_patterns']) > 2:
                    conspiracy_analysis['conspiracy_type'] = 'complex_conspiracy'
                else:
                    conspiracy_analysis['conspiracy_type'] = conspiracy_analysis['conspiracy_patterns'][0]
            
            conspiracy_analysis['conspiracy_probability'] = min(1.0, conspiracy_analysis['conspiracy_probability'])
            
            return conspiracy_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze conspiracy theories: {str(e)}")
            return {'conspiracy_probability': 0.2, 'error': str(e)}
    
    async def _analyze_source_credibility(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the credibility of sources mentioned in content."""
        try:
            text_content = content.get('content', '').lower()
            source_analysis = {
                'credible_sources_count': 0,
                'unreliable_sources_count': 0,
                'source_credibility_score': 0.5,
                'sources_mentioned': [],
                'requires_source_verification': False
            }
            
            # Check for credible source indicators
            credible_indicators_found = [indicator for indicator in self.credible_source_indicators 
                                       if indicator in text_content]
            source_analysis['credible_sources_count'] = len(credible_indicators_found)
            
            # Check for unreliable source indicators
            unreliable_indicators_found = [indicator for indicator in self.unreliable_source_indicators 
                                         if indicator in text_content]
            source_analysis['unreliable_sources_count'] = len(unreliable_indicators_found)
            
            # Extract potential source mentions (URLs, publications, etc.)
            # This is a simplified implementation
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, content.get('content', ''))
            source_analysis['sources_mentioned'] = urls
            
            # Calculate source credibility score
            if source_analysis['credible_sources_count'] > 0:
                source_analysis['source_credibility_score'] += min(0.4, source_analysis['credible_sources_count'] * 0.2)
            
            if source_analysis['unreliable_sources_count'] > 0:
                source_analysis['source_credibility_score'] -= min(0.3, source_analysis['unreliable_sources_count'] * 0.15)
            
            # Check if claims require source verification
            claim_words = ['study', 'research', 'data', 'statistics', 'report', 'survey']
            if any(word in text_content for word in claim_words) and not credible_indicators_found:
                source_analysis['requires_source_verification'] = True
            
            source_analysis['source_credibility_score'] = max(0.0, min(1.0, source_analysis['source_credibility_score']))
            
            return source_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze source credibility: {str(e)}")
            return {'source_credibility_score': 0.5, 'error': str(e)}
    
    async def _analyze_factual_claims(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for factual claims that can be verified."""
        try:
            text_content = content.get('content', '').lower()
            factual_analysis = {
                'factual_claims_count': 0,
                'verifiable_claims': [],
                'unverifiable_claims': [],
                'fact_check_priority': 'low'
            }
            
            # Identify factual claim patterns
            factual_claim_patterns = [
                r'\d+%', r'\d+ percent', r'studies show', r'research proves',
                r'according to', r'data shows', r'statistics indicate'
            ]
            
            for pattern in factual_claim_patterns:
                matches = re.findall(pattern, text_content)
                factual_analysis['factual_claims_count'] += len(matches)
                factual_analysis['verifiable_claims'].extend(matches)
            
            # Check for unverifiable claims
            unverifiable_patterns = [
                'many people say', 'everyone knows', 'it\'s obvious that',
                'common sense', 'clearly', 'obviously'
            ]
            
            for pattern in unverifiable_patterns:
                if pattern in text_content:
                    factual_analysis['unverifiable_claims'].append(pattern)
            
            # Determine fact-check priority
            if factual_analysis['factual_claims_count'] > 2:
                factual_analysis['fact_check_priority'] = 'high'
            elif factual_analysis['factual_claims_count'] > 0:
                factual_analysis['fact_check_priority'] = 'medium'
            
            # Higher priority for health claims
            health_keywords = ['cure', 'treatment', 'vaccine', 'medicine', 'health']
            if any(keyword in text_content for keyword in health_keywords):
                if factual_analysis['factual_claims_count'] > 0:
                    factual_analysis['fact_check_priority'] = 'critical'
            
            return factual_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze factual claims: {str(e)}")
            return {'fact_check_priority': 'medium', 'error': str(e)}
    
    async def _get_ai_misinformation_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on misinformation detection."""
        try:
            prompt = self._create_misinformation_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (OpenAI for fact-checking)
            if 'openai' in self.ai_providers:
                response = await self._call_ai_provider(
                    provider='openai',
                    prompt=prompt,
                    content=content_text,
                    additional_context=context
                )
                
                return await self._parse_ai_response(response['response'], 'openai')
            
            # Fallback to other providers
            for provider in ['claude', 'gemini']:
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
                'reasoning': 'No AI providers available for misinformation analysis'
            }
            
        except Exception as e:
            logger.error(f"AI misinformation analysis failed: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_misinformation_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a misinformation-focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='misinformation, false claims, and conspiracy theory detection'
        )
        
        misinformation_specific = f"""
MISINFORMATION DETECTION ANALYSIS

You are a specialized Misinformation Guardian Agent focused on detecting and preventing
the spread of false information, conspiracy theories, and unverified claims.

User Trust Context:
- Author Trust Score: {trust_score}

Misinformation Detection Criteria:
1. False Claims: Factually incorrect statements that can be verified
2. Conspiracy Theories: Unfounded theories about secret plots or cover-ups
3. Health Misinformation: False medical or health-related claims
4. Political Misinformation: False claims about elections, voting, or political processes
5. Scientific Misinformation: False claims contradicting established scientific consensus
6. Source Credibility: Reliability and trustworthiness of cited sources

Decision Guidelines:
- REMOVE: Dangerous health misinformation, election fraud claims without evidence
- FLAG: Potential misinformation requiring fact-checking
- WARN: Misleading content that needs correction or context
- APPROVE: Factual content with credible sources

Misinformation Thresholds:
- False claim threshold: {self.misinformation_thresholds['false_claim_threshold']}
- Conspiracy threshold: {self.misinformation_thresholds['conspiracy_threshold']}
- Health misinformation threshold: {self.misinformation_thresholds['health_misinformation_threshold']}

CRITICAL: Prioritize public safety and health. Be especially cautious with health-related
claims and political misinformation. When in doubt, flag for human fact-checking.
Consider the potential harm of allowing false information to spread.
"""
        
        return base_prompt + misinformation_specific
    
    async def _make_misinformation_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        risk_categorization: Dict[str, Any],
        misinformation_analysis: Dict[str, Any],
        conspiracy_analysis: Dict[str, Any],
        source_analysis: Dict[str, Any],
        factual_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make final misinformation-based moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Extract key metrics
            risk_level = risk_categorization.get('risk_level', 'low')
            misinformation_score = misinformation_analysis.get('misinformation_score', 0.0)
            conspiracy_probability = conspiracy_analysis.get('conspiracy_probability', 0.0)
            source_credibility = source_analysis.get('source_credibility_score', 0.5)
            fact_check_priority = factual_analysis.get('fact_check_priority', 'low')
            
            # Critical health misinformation handling
            if (risk_level == 'critical' and 
                'health_medical' in risk_categorization.get('risk_categories', [])):
                
                if (misinformation_score > self.misinformation_thresholds['health_misinformation_threshold'] or
                    source_credibility < self.misinformation_thresholds['source_credibility_threshold']):
                    
                    base_decision['action'] = 'remove'
                    base_decision['confidence'] = 0.9
                    base_decision['reasoning'] = 'Potential health misinformation - removed for public safety'
                    base_decision['requires_fact_check'] = True
                    base_decision['escalate_to_human'] = True
                
                elif fact_check_priority in ['high', 'critical']:
                    base_decision['action'] = 'flag'
                    base_decision['confidence'] = 0.8
                    base_decision['reasoning'] = 'Health claims require fact-checking verification'
                    base_decision['requires_fact_check'] = True
            
            # Conspiracy theory handling
            elif conspiracy_probability > self.misinformation_thresholds['conspiracy_threshold']:
                if conspiracy_probability > 0.8:
                    base_decision['action'] = 'remove'
                    base_decision['confidence'] = 0.85
                    base_decision['reasoning'] = 'High-confidence conspiracy theory detected'
                else:
                    base_decision['action'] = 'flag'
                    base_decision['confidence'] = 0.7
                    base_decision['reasoning'] = 'Potential conspiracy theory requires review'
            
            # General misinformation handling
            elif misinformation_score > self.misinformation_thresholds['false_claim_threshold']:
                if source_credibility < self.misinformation_thresholds['source_credibility_threshold']:
                    base_decision['action'] = 'flag'
                    base_decision['confidence'] = 0.75
                    base_decision['reasoning'] = 'Potential misinformation with unreliable sources'
                    base_decision['requires_fact_check'] = True
                else:
                    base_decision['action'] = 'warn'
                    base_decision['reasoning'] = 'Content contains claims that may need verification'
            
            # Source credibility issues
            elif (source_analysis.get('requires_source_verification', False) and
                  source_credibility < 0.3):
                
                base_decision['action'] = 'flag'
                base_decision['confidence'] = 0.6
                base_decision['reasoning'] = 'Claims made without credible sources'
                base_decision['requires_fact_check'] = True
            
            # Trust score adjustments
            if trust_score < 0.3 and misinformation_score > 0.4:
                if base_decision['action'] == 'approve':
                    base_decision['action'] = 'flag'
                    base_decision['reasoning'] += ' (Low trust user with questionable claims)'
            elif trust_score > 0.8 and base_decision['action'] == 'flag':
                # Trusted users get benefit of doubt for borderline cases
                if misinformation_score < 0.6:
                    base_decision['action'] = 'warn'
                    base_decision['reasoning'] = 'Trusted user - education opportunity for questionable claims'
            
            # Add misinformation-specific metadata
            base_decision['metadata'] = {
                'agent': 'misinformation_guardian',
                'risk_level': risk_level,
                'misinformation_score': round(misinformation_score, 3),
                'conspiracy_probability': round(conspiracy_probability, 3),
                'source_credibility': round(source_credibility, 3),
                'fact_check_priority': fact_check_priority,
                'trust_score': trust_score,
                'risk_categories': risk_categorization.get('risk_categories', [])
            }
            
            # Add detailed evidence
            base_decision['evidence'] = {
                'risk_categorization': risk_categorization,
                'misinformation_analysis': misinformation_analysis,
                'conspiracy_analysis': conspiracy_analysis,
                'source_analysis': source_analysis,
                'factual_analysis': factual_analysis,
                'ai_analysis': ai_analysis
            }
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make misinformation decision: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.6,
                'reasoning': f'Misinformation decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'misinformation_guardian', 'error': True},
                'requires_fact_check': True
            }