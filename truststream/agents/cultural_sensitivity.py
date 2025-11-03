# Cultural Sensitivity Agent for TrustStream v4.4
# Specialized agent for promoting cultural awareness and preventing discrimination

import logging
import json
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class CulturalSensitivityAgent(BaseAIAgent):
    """
    Cultural Sensitivity Agent - Specialized Cultural Awareness and Inclusion
    
    This agent focuses on promoting cultural sensitivity, preventing discrimination,
    ensuring inclusive communication, and fostering cross-cultural understanding
    within community interactions.
    
    Key Responsibilities:
    - Cultural bias detection and prevention
    - Discrimination and prejudice identification
    - Inclusive language promotion
    - Cross-cultural communication facilitation
    - Stereotype and prejudice prevention
    - Cultural appropriation detection
    - Religious sensitivity monitoring
    - Ethnic and racial bias prevention
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Cultural sensitivity configuration
        self.cultural_config = {
            'cultural_dimensions': [
                'ethnicity', 'race', 'nationality', 'religion', 'language',
                'gender', 'age', 'socioeconomic_status', 'disability',
                'sexual_orientation', 'political_affiliation', 'regional_identity'
            ],
            'bias_types': [
                'racial_bias', 'ethnic_bias', 'religious_bias', 'gender_bias',
                'age_bias', 'linguistic_bias', 'cultural_bias', 'national_bias',
                'socioeconomic_bias', 'disability_bias', 'orientation_bias'
            ],
            'sensitivity_levels': {
                'critical': 0.9,  # Severe discrimination or hate
                'high': 0.7,      # Significant bias or insensitivity
                'medium': 0.5,    # Moderate cultural insensitivity
                'low': 0.3        # Minor cultural awareness issue
            }
        }
        
        # Cultural bias detection patterns
        self.bias_patterns = {
            'racial_slurs': [
                # Note: These would be actual slurs in production - using placeholders
                'racial_slur_1', 'racial_slur_2', 'racial_slur_3'
            ],
            'ethnic_stereotypes': [
                'all [ethnicity] are', 'typical [ethnicity]', '[ethnicity] always',
                '[ethnicity] never', 'you people', 'those people'
            ],
            'religious_bias': [
                'religious extremist', 'fanatic', 'infidel', 'heathen',
                'godless', 'religious nut', 'cult member'
            ],
            'cultural_appropriation': [
                'costume', 'dress up as', 'playing [culture]', 'pretending to be',
                'cultural costume', 'ethnic outfit'
            ],
            'linguistic_discrimination': [
                'speak english', 'go back to', 'learn the language',
                'foreign accent', 'broken english', 'can\'t understand'
            ],
            'national_bias': [
                'go back to your country', 'not from here', 'foreign',
                'immigrant problem', 'invasion', 'taking over'
            ]
        }
        
        # Inclusive language alternatives
        self.inclusive_alternatives = {
            'guys': ['everyone', 'folks', 'team', 'all'],
            'mankind': ['humanity', 'people', 'human beings'],
            'manpower': ['workforce', 'staff', 'personnel'],
            'blacklist': ['blocklist', 'denylist', 'exclude list'],
            'whitelist': ['allowlist', 'permit list', 'include list'],
            'master/slave': ['primary/secondary', 'main/replica', 'leader/follower']
        }
        
        # Cultural sensitivity thresholds
        self.sensitivity_thresholds = {
            'discrimination_score': 0.8,
            'bias_detection': 0.7,
            'cultural_insensitivity': 0.6,
            'stereotype_usage': 0.65,
            'inclusive_language': 0.5
        }
        
        # Cultural sensitivity metrics
        self.cultural_metrics = {
            'total_content_analyzed': 0,
            'bias_incidents_detected': 0,
            'discrimination_prevented': 0,
            'inclusive_language_promoted': 0,
            'cultural_education_provided': 0,
            'cross_cultural_facilitation': 0
        }
        
        logger.info(f"Cultural Sensitivity Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content with focus on cultural sensitivity and inclusion.
        
        The Cultural Sensitivity Agent evaluates:
        - Cultural bias and discrimination
        - Stereotypes and prejudices
        - Inclusive language usage
        - Cross-cultural communication quality
        - Cultural appropriation risks
        - Religious sensitivity issues
        - Ethnic and racial bias
        - Gender and orientation sensitivity
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Detect cultural bias and discrimination
            bias_analysis = await self._detect_cultural_bias(content, context)
            
            # Analyze stereotypes and prejudices
            stereotype_analysis = await self._analyze_stereotypes(content, context)
            
            # Evaluate inclusive language usage
            language_analysis = await self._evaluate_inclusive_language(content, context)
            
            # Check for cultural appropriation
            appropriation_analysis = await self._check_cultural_appropriation(content, context)
            
            # Assess religious sensitivity
            religious_analysis = await self._assess_religious_sensitivity(content, context)
            
            # Analyze cross-cultural communication
            communication_analysis = await self._analyze_cross_cultural_communication(content, context)
            
            # Evaluate diversity and inclusion
            inclusion_analysis = await self._evaluate_diversity_inclusion(content, context)
            
            # Get AI provider analysis for cultural sensitivity
            ai_analysis = await self._get_ai_cultural_analysis(content, trust_score, context)
            
            # Make cultural sensitivity decision
            decision = await self._make_cultural_decision(
                content=content,
                trust_score=trust_score,
                bias_analysis=bias_analysis,
                stereotype_analysis=stereotype_analysis,
                language_analysis=language_analysis,
                appropriation_analysis=appropriation_analysis,
                religious_analysis=religious_analysis,
                communication_analysis=communication_analysis,
                inclusion_analysis=inclusion_analysis,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Update cultural metrics
            await self._update_cultural_metrics(content, decision, context)
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Cultural sensitivity analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Cultural sensitivity analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'cultural_sensitivity', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Cultural Sensitivity Agent."""
        return [
            'cultural_bias_detection',
            'discrimination_prevention',
            'stereotype_identification',
            'inclusive_language_promotion',
            'cross_cultural_facilitation',
            'cultural_appropriation_detection',
            'religious_sensitivity_monitoring',
            'diversity_inclusion_assessment',
            'cultural_education_provision',
            'bias_mitigation_strategies'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Cultural Sensitivity Agent."""
        return (
            "Specialized agent for promoting cultural sensitivity and preventing discrimination. "
            "Detects cultural bias, prevents stereotyping, promotes inclusive language, and "
            "facilitates respectful cross-cultural communication within communities."
        )
    
    # Private analysis methods
    
    async def _detect_cultural_bias(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect cultural bias and discrimination in content."""
        try:
            bias_analysis = {
                'bias_detected': False,
                'bias_types': [],
                'bias_score': 0.0,
                'discrimination_indicators': [],
                'severity_level': 'low'
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for racial bias
            racial_bias_indicators = [
                'inferior race', 'superior race', 'racial purity', 'mixed race problem',
                'race mixing', 'racial hierarchy', 'genetic superiority', 'racial supremacy'
            ]
            
            racial_bias_count = sum(1 for indicator in racial_bias_indicators 
                                  if indicator in content_text)
            
            if racial_bias_count > 0:
                bias_analysis['bias_detected'] = True
                bias_analysis['bias_types'].append('racial_bias')
                bias_analysis['discrimination_indicators'].append('racial_discrimination')
                bias_analysis['bias_score'] += 0.4
            
            # Check for ethnic bias
            ethnic_bias_indicators = [
                'ethnic cleansing', 'ethnic purity', 'ethnic superiority',
                'primitive culture', 'backward people', 'uncivilized'
            ]
            
            ethnic_bias_count = sum(1 for indicator in ethnic_bias_indicators 
                                  if indicator in content_text)
            
            if ethnic_bias_count > 0:
                bias_analysis['bias_detected'] = True
                bias_analysis['bias_types'].append('ethnic_bias')
                bias_analysis['discrimination_indicators'].append('ethnic_discrimination')
                bias_analysis['bias_score'] += 0.35
            
            # Check for religious bias
            religious_bias_indicators = [
                'religious war', 'holy war', 'infidel', 'heretic',
                'false religion', 'cult', 'religious extremist', 'fanatic'
            ]
            
            religious_bias_count = sum(1 for indicator in religious_bias_indicators 
                                     if indicator in content_text)
            
            if religious_bias_count > 0:
                bias_analysis['bias_detected'] = True
                bias_analysis['bias_types'].append('religious_bias')
                bias_analysis['discrimination_indicators'].append('religious_discrimination')
                bias_analysis['bias_score'] += 0.3
            
            # Check for gender bias
            gender_bias_indicators = [
                'women belong', 'men are better', 'gender roles', 'natural order',
                'biological destiny', 'weaker sex', 'stronger sex', 'gender superiority'
            ]
            
            gender_bias_count = sum(1 for indicator in gender_bias_indicators 
                                  if indicator in content_text)
            
            if gender_bias_count > 0:
                bias_analysis['bias_detected'] = True
                bias_analysis['bias_types'].append('gender_bias')
                bias_analysis['discrimination_indicators'].append('gender_discrimination')
                bias_analysis['bias_score'] += 0.25
            
            # Check for linguistic bias
            linguistic_bias_indicators = [
                'speak english', 'learn the language', 'foreign accent',
                'broken english', 'language barrier', 'communication problem'
            ]
            
            linguistic_bias_count = sum(1 for indicator in linguistic_bias_indicators 
                                      if indicator in content_text)
            
            if linguistic_bias_count > 0:
                bias_analysis['bias_detected'] = True
                bias_analysis['bias_types'].append('linguistic_bias')
                bias_analysis['discrimination_indicators'].append('linguistic_discrimination')
                bias_analysis['bias_score'] += 0.2
            
            # Check for national bias
            national_bias_indicators = [
                'go back to your country', 'not from here', 'foreign invasion',
                'immigrant problem', 'taking over', 'cultural invasion'
            ]
            
            national_bias_count = sum(1 for indicator in national_bias_indicators 
                                    if indicator in content_text)
            
            if national_bias_count > 0:
                bias_analysis['bias_detected'] = True
                bias_analysis['bias_types'].append('national_bias')
                bias_analysis['discrimination_indicators'].append('national_discrimination')
                bias_analysis['bias_score'] += 0.3
            
            # Determine severity level
            if bias_analysis['bias_score'] >= self.cultural_config['sensitivity_levels']['critical']:
                bias_analysis['severity_level'] = 'critical'
            elif bias_analysis['bias_score'] >= self.cultural_config['sensitivity_levels']['high']:
                bias_analysis['severity_level'] = 'high'
            elif bias_analysis['bias_score'] >= self.cultural_config['sensitivity_levels']['medium']:
                bias_analysis['severity_level'] = 'medium'
            
            return bias_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect cultural bias: {str(e)}")
            return {'bias_score': 0.5, 'error': str(e)}
    
    async def _analyze_stereotypes(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for stereotypes and prejudices."""
        try:
            stereotype_analysis = {
                'stereotypes_detected': False,
                'stereotype_types': [],
                'stereotype_score': 0.0,
                'prejudice_indicators': [],
                'generalization_patterns': []
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for racial stereotypes
            racial_stereotype_patterns = [
                r'all \w+ (people|men|women) are',
                r'\w+ (people|men|women) always',
                r'\w+ (people|men|women) never',
                r'typical \w+ behavior',
                r'\w+ (people|men|women) can\'t'
            ]
            
            racial_stereotype_count = 0
            for pattern in racial_stereotype_patterns:
                matches = re.findall(pattern, content_text)
                racial_stereotype_count += len(matches)
            
            if racial_stereotype_count > 0:
                stereotype_analysis['stereotypes_detected'] = True
                stereotype_analysis['stereotype_types'].append('racial_stereotypes')
                stereotype_analysis['generalization_patterns'].append('racial_generalizations')
                stereotype_analysis['stereotype_score'] += 0.35
            
            # Check for gender stereotypes
            gender_stereotype_indicators = [
                'women are emotional', 'men don\'t cry', 'girls are weak',
                'boys don\'t play', 'women drivers', 'men are aggressive',
                'feminine weakness', 'masculine strength', 'gender typical'
            ]
            
            gender_stereotype_count = sum(1 for indicator in gender_stereotype_indicators 
                                        if indicator in content_text)
            
            if gender_stereotype_count > 0:
                stereotype_analysis['stereotypes_detected'] = True
                stereotype_analysis['stereotype_types'].append('gender_stereotypes')
                stereotype_analysis['prejudice_indicators'].append('gender_prejudice')
                stereotype_analysis['stereotype_score'] += 0.25
            
            # Check for cultural stereotypes
            cultural_stereotype_indicators = [
                'cultural trait', 'national character', 'ethnic behavior',
                'cultural tendency', 'typical of their kind', 'cultural genetics'
            ]
            
            cultural_stereotype_count = sum(1 for indicator in cultural_stereotype_indicators 
                                          if indicator in content_text)
            
            if cultural_stereotype_count > 0:
                stereotype_analysis['stereotypes_detected'] = True
                stereotype_analysis['stereotype_types'].append('cultural_stereotypes')
                stereotype_analysis['prejudice_indicators'].append('cultural_prejudice')
                stereotype_analysis['stereotype_score'] += 0.3
            
            # Check for religious stereotypes
            religious_stereotype_indicators = [
                'all believers', 'religious people always', 'faith makes them',
                'religious extremism', 'typical believer', 'religious behavior'
            ]
            
            religious_stereotype_count = sum(1 for indicator in religious_stereotype_indicators 
                                           if indicator in content_text)
            
            if religious_stereotype_count > 0:
                stereotype_analysis['stereotypes_detected'] = True
                stereotype_analysis['stereotype_types'].append('religious_stereotypes')
                stereotype_analysis['prejudice_indicators'].append('religious_prejudice')
                stereotype_analysis['stereotype_score'] += 0.25
            
            # Check for age stereotypes
            age_stereotype_indicators = [
                'old people can\'t', 'young people always', 'generational trait',
                'age typical', 'too old for', 'too young to understand'
            ]
            
            age_stereotype_count = sum(1 for indicator in age_stereotype_indicators 
                                     if indicator in content_text)
            
            if age_stereotype_count > 0:
                stereotype_analysis['stereotypes_detected'] = True
                stereotype_analysis['stereotype_types'].append('age_stereotypes')
                stereotype_analysis['prejudice_indicators'].append('age_prejudice')
                stereotype_analysis['stereotype_score'] += 0.2
            
            return stereotype_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze stereotypes: {str(e)}")
            return {'stereotype_score': 0.5, 'error': str(e)}
    
    async def _evaluate_inclusive_language(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate inclusive language usage."""
        try:
            language_analysis = {
                'inclusive_score': 0.8,  # Start with good assumption
                'non_inclusive_terms': [],
                'suggested_alternatives': {},
                'language_barriers': [],
                'accessibility_issues': []
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for non-inclusive terms
            for term, alternatives in self.inclusive_alternatives.items():
                if term in content_text:
                    language_analysis['non_inclusive_terms'].append(term)
                    language_analysis['suggested_alternatives'][term] = alternatives
                    language_analysis['inclusive_score'] -= 0.1
            
            # Check for gendered language
            gendered_terms = [
                'guys', 'mankind', 'manpower', 'chairman', 'policeman',
                'fireman', 'businessman', 'spokesman', 'workman'
            ]
            
            gendered_count = sum(1 for term in gendered_terms if term in content_text)
            
            if gendered_count > 0:
                language_analysis['inclusive_score'] -= 0.15
                language_analysis['language_barriers'].append('gendered_language')
            
            # Check for ableist language
            ableist_terms = [
                'crazy', 'insane', 'lame', 'blind to', 'deaf to',
                'dumb', 'stupid', 'retarded', 'mental', 'psycho'
            ]
            
            ableist_count = sum(1 for term in ableist_terms if term in content_text)
            
            if ableist_count > 0:
                language_analysis['inclusive_score'] -= 0.2
                language_analysis['accessibility_issues'].append('ableist_language')
            
            # Check for age-discriminatory language
            age_discriminatory_terms = [
                'too old', 'too young', 'outdated', 'old-fashioned',
                'boomer', 'millennial problem', 'generation gap'
            ]
            
            age_discriminatory_count = sum(1 for term in age_discriminatory_terms 
                                         if term in content_text)
            
            if age_discriminatory_count > 0:
                language_analysis['inclusive_score'] -= 0.1
                language_analysis['language_barriers'].append('age_discriminatory')
            
            # Check for positive inclusive language
            inclusive_terms = [
                'everyone', 'all people', 'inclusive', 'diverse',
                'accessible', 'welcoming', 'respectful', 'understanding'
            ]
            
            inclusive_count = sum(1 for term in inclusive_terms if term in content_text)
            
            if inclusive_count > 0:
                language_analysis['inclusive_score'] += 0.1
            
            # Ensure score stays within bounds
            language_analysis['inclusive_score'] = max(0.0, min(1.0, language_analysis['inclusive_score']))
            
            return language_analysis
            
        except Exception as e:
            logger.error(f"Failed to evaluate inclusive language: {str(e)}")
            return {'inclusive_score': 0.5, 'error': str(e)}
    
    async def _check_cultural_appropriation(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for cultural appropriation issues."""
        try:
            appropriation_analysis = {
                'appropriation_risk': 0.0,
                'appropriation_indicators': [],
                'cultural_elements_misused': [],
                'respect_level': 'respectful'
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for costume/dress-up language
            costume_indicators = [
                'dress up as', 'costume', 'playing [culture]', 'pretending to be',
                'cultural outfit', 'ethnic costume', 'traditional dress'
            ]
            
            costume_count = sum(1 for indicator in costume_indicators 
                              if indicator in content_text)
            
            if costume_count > 0:
                appropriation_analysis['appropriation_indicators'].append('costume_usage')
                appropriation_analysis['appropriation_risk'] += 0.3
            
            # Check for sacred/religious element misuse
            sacred_misuse_indicators = [
                'sacred symbol', 'religious artifact', 'spiritual item',
                'ceremonial object', 'holy symbol', 'ritual item'
            ]
            
            sacred_misuse_count = sum(1 for indicator in sacred_misuse_indicators 
                                    if indicator in content_text)
            
            if sacred_misuse_count > 0:
                appropriation_analysis['cultural_elements_misused'].append('sacred_elements')
                appropriation_analysis['appropriation_risk'] += 0.4
            
            # Check for cultural trivialization
            trivialization_indicators = [
                'just for fun', 'it\'s just fashion', 'cultural trend',
                'exotic look', 'tribal style', 'ethnic fashion'
            ]
            
            trivialization_count = sum(1 for indicator in trivialization_indicators 
                                     if indicator in content_text)
            
            if trivialization_count > 0:
                appropriation_analysis['appropriation_indicators'].append('cultural_trivialization')
                appropriation_analysis['appropriation_risk'] += 0.25
            
            # Check for positive cultural appreciation
            appreciation_indicators = [
                'cultural appreciation', 'respectful use', 'cultural learning',
                'honor tradition', 'respect culture', 'cultural understanding'
            ]
            
            appreciation_count = sum(1 for indicator in appreciation_indicators 
                                   if indicator in content_text)
            
            if appreciation_count > 0:
                appropriation_analysis['appropriation_risk'] -= 0.2
            
            # Determine respect level
            if appropriation_analysis['appropriation_risk'] >= 0.6:
                appropriation_analysis['respect_level'] = 'disrespectful'
            elif appropriation_analysis['appropriation_risk'] >= 0.3:
                appropriation_analysis['respect_level'] = 'questionable'
            elif appropriation_analysis['appropriation_risk'] <= -0.1:
                appropriation_analysis['respect_level'] = 'highly_respectful'
            
            # Ensure risk doesn't go below 0
            appropriation_analysis['appropriation_risk'] = max(0.0, appropriation_analysis['appropriation_risk'])
            
            return appropriation_analysis
            
        except Exception as e:
            logger.error(f"Failed to check cultural appropriation: {str(e)}")
            return {'appropriation_risk': 0.5, 'error': str(e)}
    
    async def _assess_religious_sensitivity(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess religious sensitivity and respect."""
        try:
            religious_analysis = {
                'sensitivity_score': 0.8,  # Start with good assumption
                'religious_issues': [],
                'blasphemy_indicators': [],
                'interfaith_respect': 'respectful'
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for religious mockery
            mockery_indicators = [
                'religious joke', 'mock religion', 'make fun of faith',
                'ridicule belief', 'religious satire', 'faith mockery'
            ]
            
            mockery_count = sum(1 for indicator in mockery_indicators 
                              if indicator in content_text)
            
            if mockery_count > 0:
                religious_analysis['religious_issues'].append('religious_mockery')
                religious_analysis['sensitivity_score'] -= 0.3
            
            # Check for blasphemy
            blasphemy_indicators = [
                'blasphemy', 'sacrilege', 'profane', 'desecrate',
                'religious insult', 'sacred mockery', 'holy ridicule'
            ]
            
            blasphemy_count = sum(1 for indicator in blasphemy_indicators 
                                if indicator in content_text)
            
            if blasphemy_count > 0:
                religious_analysis['blasphemy_indicators'].append('direct_blasphemy')
                religious_analysis['sensitivity_score'] -= 0.4
            
            # Check for religious intolerance
            intolerance_indicators = [
                'false religion', 'wrong faith', 'religious error',
                'misguided belief', 'religious delusion', 'faith problem'
            ]
            
            intolerance_count = sum(1 for indicator in intolerance_indicators 
                                  if indicator in content_text)
            
            if intolerance_count > 0:
                religious_analysis['religious_issues'].append('religious_intolerance')
                religious_analysis['sensitivity_score'] -= 0.35
            
            # Check for positive religious respect
            respect_indicators = [
                'religious respect', 'faith diversity', 'spiritual understanding',
                'interfaith dialogue', 'religious tolerance', 'sacred respect'
            ]
            
            respect_count = sum(1 for indicator in respect_indicators 
                              if indicator in content_text)
            
            if respect_count > 0:
                religious_analysis['sensitivity_score'] += 0.1
            
            # Determine interfaith respect level
            if religious_analysis['sensitivity_score'] >= 0.8:
                religious_analysis['interfaith_respect'] = 'highly_respectful'
            elif religious_analysis['sensitivity_score'] >= 0.6:
                religious_analysis['interfaith_respect'] = 'respectful'
            elif religious_analysis['sensitivity_score'] >= 0.4:
                religious_analysis['interfaith_respect'] = 'questionable'
            else:
                religious_analysis['interfaith_respect'] = 'disrespectful'
            
            # Ensure score stays within bounds
            religious_analysis['sensitivity_score'] = max(0.0, min(1.0, religious_analysis['sensitivity_score']))
            
            return religious_analysis
            
        except Exception as e:
            logger.error(f"Failed to assess religious sensitivity: {str(e)}")
            return {'sensitivity_score': 0.5, 'error': str(e)}
    
    async def _analyze_cross_cultural_communication(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cross-cultural communication quality."""
        try:
            communication_analysis = {
                'communication_quality': 0.7,
                'cultural_barriers': [],
                'bridge_building_elements': [],
                'misunderstanding_risks': []
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for cultural bridge-building
            bridge_building_indicators = [
                'cultural exchange', 'learn from each other', 'different perspectives',
                'cultural sharing', 'mutual understanding', 'cross-cultural learning'
            ]
            
            bridge_building_count = sum(1 for indicator in bridge_building_indicators 
                                      if indicator in content_text)
            
            if bridge_building_count > 0:
                communication_analysis['bridge_building_elements'].append('cultural_exchange')
                communication_analysis['communication_quality'] += 0.2
            
            # Check for cultural barriers
            barrier_indicators = [
                'cultural difference', 'language barrier', 'cultural gap',
                'misunderstanding', 'cultural conflict', 'communication problem'
            ]
            
            barrier_count = sum(1 for indicator in barrier_indicators 
                              if indicator in content_text)
            
            if barrier_count > 0:
                communication_analysis['cultural_barriers'].append('communication_barriers')
                communication_analysis['communication_quality'] -= 0.1
            
            # Check for ethnocentrism
            ethnocentric_indicators = [
                'our way is better', 'superior culture', 'primitive culture',
                'advanced society', 'backward people', 'civilized vs uncivilized'
            ]
            
            ethnocentric_count = sum(1 for indicator in ethnocentric_indicators 
                                   if indicator in content_text)
            
            if ethnocentric_count > 0:
                communication_analysis['misunderstanding_risks'].append('ethnocentrism')
                communication_analysis['communication_quality'] -= 0.3
            
            # Ensure score stays within bounds
            communication_analysis['communication_quality'] = max(0.0, min(1.0, communication_analysis['communication_quality']))
            
            return communication_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze cross-cultural communication: {str(e)}")
            return {'communication_quality': 0.5, 'error': str(e)}
    
    async def _evaluate_diversity_inclusion(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate diversity and inclusion aspects."""
        try:
            inclusion_analysis = {
                'inclusion_score': 0.7,
                'diversity_elements': [],
                'exclusion_indicators': [],
                'representation_quality': 'adequate'
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for positive diversity elements
            diversity_indicators = [
                'diverse perspectives', 'inclusive environment', 'all welcome',
                'different backgrounds', 'variety of views', 'multicultural'
            ]
            
            diversity_count = sum(1 for indicator in diversity_indicators 
                                if indicator in content_text)
            
            if diversity_count > 0:
                inclusion_analysis['diversity_elements'].append('positive_diversity')
                inclusion_analysis['inclusion_score'] += 0.2
            
            # Check for exclusion indicators
            exclusion_indicators = [
                'not welcome', 'don\'t belong', 'outsider', 'not one of us',
                'different kind', 'not our type', 'doesn\'t fit in'
            ]
            
            exclusion_count = sum(1 for indicator in exclusion_indicators 
                                if indicator in content_text)
            
            if exclusion_count > 0:
                inclusion_analysis['exclusion_indicators'].append('exclusionary_language')
                inclusion_analysis['inclusion_score'] -= 0.3
            
            # Determine representation quality
            if inclusion_analysis['inclusion_score'] >= 0.8:
                inclusion_analysis['representation_quality'] = 'excellent'
            elif inclusion_analysis['inclusion_score'] >= 0.6:
                inclusion_analysis['representation_quality'] = 'good'
            elif inclusion_analysis['inclusion_score'] >= 0.4:
                inclusion_analysis['representation_quality'] = 'adequate'
            else:
                inclusion_analysis['representation_quality'] = 'poor'
            
            # Ensure score stays within bounds
            inclusion_analysis['inclusion_score'] = max(0.0, min(1.0, inclusion_analysis['inclusion_score']))
            
            return inclusion_analysis
            
        except Exception as e:
            logger.error(f"Failed to evaluate diversity inclusion: {str(e)}")
            return {'inclusion_score': 0.5, 'error': str(e)}
    
    async def _get_ai_cultural_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on cultural sensitivity."""
        try:
            prompt = self._create_cultural_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (Claude for cultural analysis)
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
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': 'No AI providers available for cultural analysis'
            }
            
        except Exception as e:
            logger.error(f"AI cultural analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_cultural_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a cultural sensitivity focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='cultural sensitivity, inclusion, and cross-cultural respect'
        )
        
        cultural_specific = f"""
CULTURAL SENSITIVITY ANALYSIS

You are a specialized Cultural Sensitivity Agent focused on promoting cultural
awareness, preventing discrimination, and fostering inclusive communication.

User Trust Context:
- Author Trust Score: {trust_score}

Cultural Sensitivity Framework:
1. Cultural Bias Detection: Identify racial, ethnic, religious, and cultural biases
2. Discrimination Prevention: Stop prejudice and discriminatory language
3. Stereotype Analysis: Detect and prevent harmful stereotyping
4. Inclusive Language: Promote respectful and inclusive communication
5. Cultural Appropriation: Identify misuse of cultural elements
6. Religious Sensitivity: Ensure respectful treatment of all faiths
7. Cross-Cultural Communication: Facilitate understanding across cultures
8. Diversity & Inclusion: Support diverse perspectives and representation

Critical Cultural Threats:
- Racial and ethnic discrimination and bias
- Religious intolerance and blasphemy
- Cultural stereotyping and prejudice
- Gender, age, and orientation bias
- Cultural appropriation and disrespect
- Linguistic discrimination and barriers
- Exclusionary and non-inclusive language
- Cross-cultural misunderstanding and conflict

Decision Guidelines:
- BLOCK: Direct discrimination, hate speech, and severe cultural insensitivity
- FLAG: Stereotyping, bias, and cultural appropriation concerns
- MONITOR: Potential cultural insensitivity and communication barriers
- APPROVE: Culturally sensitive and inclusive content

Cultural Priorities:
- Prevent discrimination and promote equality
- Foster cross-cultural understanding and respect
- Support inclusive and accessible communication
- Protect cultural heritage and sacred elements
- Encourage diverse perspectives and representation
- Build bridges across cultural differences
- Educate about cultural sensitivity and awareness

CRITICAL: Any content that promotes discrimination, perpetuates harmful stereotypes,
or disrespects cultural, religious, or ethnic groups must be flagged or blocked.
"""
        
        return base_prompt + cultural_specific
    
    async def _make_cultural_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        bias_analysis: Dict[str, Any],
        stereotype_analysis: Dict[str, Any],
        language_analysis: Dict[str, Any],
        appropriation_analysis: Dict[str, Any],
        religious_analysis: Dict[str, Any],
        communication_analysis: Dict[str, Any],
        inclusion_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make cultural sensitivity focused moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Calculate overall cultural sensitivity risk
            risk_scores = [
                bias_analysis.get('bias_score', 0.0),
                stereotype_analysis.get('stereotype_score', 0.0),
                1.0 - language_analysis.get('inclusive_score', 0.8),
                appropriation_analysis.get('appropriation_risk', 0.0),
                1.0 - religious_analysis.get('sensitivity_score', 0.8),
                1.0 - communication_analysis.get('communication_quality', 0.7),
                1.0 - inclusion_analysis.get('inclusion_score', 0.7)
            ]
            
            overall_cultural_risk = max(risk_scores)  # Use highest risk
            
            # Make decision based on cultural sensitivity risk
            if overall_cultural_risk >= self.cultural_config['sensitivity_levels']['critical']:
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'Critical cultural insensitivity or discrimination detected'
                base_decision['priority'] = 'critical'
                
            elif overall_cultural_risk >= self.cultural_config['sensitivity_levels']['high']:
                if base_decision['action'] == 'approve':
                    base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'High cultural sensitivity risk - requires review'
                base_decision['priority'] = 'high'
                
            elif overall_cultural_risk >= self.cultural_config['sensitivity_levels']['medium']:
                base_decision['monitoring_required'] = True
                base_decision['priority'] = 'medium'
            
            # Handle severe bias
            if bias_analysis.get('severity_level') == 'critical':
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'Critical cultural bias or discrimination detected'
                base_decision['bias_violation'] = True
            
            # Handle cultural appropriation
            if appropriation_analysis.get('respect_level') == 'disrespectful':
                if base_decision['action'] == 'approve':
                    base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Cultural appropriation concerns detected'
                base_decision['appropriation_concern'] = True
            
            # Add cultural-specific metadata
            base_decision['metadata'] = base_decision.get('metadata', {})
            base_decision['metadata'].update({
                'agent': 'cultural_sensitivity',
                'overall_cultural_risk': round(overall_cultural_risk, 3),
                'bias_detected': bias_analysis.get('bias_detected', False),
                'bias_types': bias_analysis.get('bias_types', []),
                'stereotypes_detected': stereotype_analysis.get('stereotypes_detected', False),
                'inclusive_score': round(language_analysis.get('inclusive_score', 0.8), 3),
                'appropriation_risk': round(appropriation_analysis.get('appropriation_risk', 0.0), 3),
                'religious_sensitivity': round(religious_analysis.get('sensitivity_score', 0.8), 3),
                'inclusion_score': round(inclusion_analysis.get('inclusion_score', 0.7), 3)
            })
            
            # Add detailed evidence
            base_decision['evidence'] = base_decision.get('evidence', {})
            base_decision['evidence'].update({
                'bias_analysis': bias_analysis,
                'stereotype_analysis': stereotype_analysis,
                'language_analysis': language_analysis,
                'appropriation_analysis': appropriation_analysis,
                'religious_analysis': religious_analysis,
                'communication_analysis': communication_analysis,
                'inclusion_analysis': inclusion_analysis
            })
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make cultural decision: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Cultural decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'cultural_sensitivity', 'error': True}
            }
    
    async def _update_cultural_metrics(
        self, 
        content: Dict[str, Any], 
        decision: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> None:
        """Update cultural sensitivity metrics for performance tracking."""
        try:
            self.cultural_metrics['total_content_analyzed'] += 1
            
            # Track bias detection
            if decision.get('metadata', {}).get('bias_detected', False):
                self.cultural_metrics['bias_incidents_detected'] += 1
            
            # Track discrimination prevention
            if decision.get('action') in ['block', 'flag'] and 'discrimination' in decision.get('reasoning', '').lower():
                self.cultural_metrics['discrimination_prevented'] += 1
            
            # Track inclusive language promotion
            if decision.get('metadata', {}).get('inclusive_score', 0.8) < 0.6:
                self.cultural_metrics['inclusive_language_promoted'] += 1
            
            # Track cultural education
            if decision.get('appropriation_concern', False):
                self.cultural_metrics['cultural_education_provided'] += 1
            
            # Track cross-cultural facilitation
            if 'cross-cultural' in decision.get('reasoning', '').lower():
                self.cultural_metrics['cross_cultural_facilitation'] += 1
            
        except Exception as e:
            logger.error(f"Failed to update cultural metrics: {str(e)}")