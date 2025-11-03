# Youth Safety Guardian Agent for TrustStream v4.4
# Specialized agent for child protection and age-appropriate content

import logging
import json
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class YouthSafetyGuardianAgent(BaseAIAgent):
    """
    Youth Safety Guardian Agent - Specialized Child Protection and Age-Appropriate Content
    
    This agent focuses on protecting minors, ensuring age-appropriate content,
    preventing exploitation, and maintaining safe digital environments for
    children and teenagers.
    
    Key Responsibilities:
    - Child protection and safety monitoring
    - Age-appropriate content verification
    - Predatory behavior detection and prevention
    - Educational content promotion for youth
    - Cyberbullying prevention among minors
    - Privacy protection for children
    - Parental control and oversight support
    - Digital literacy and safety education
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Youth safety configuration
        self.youth_safety_config = {
            'age_groups': {
                'children': {'min_age': 0, 'max_age': 12},
                'teens': {'min_age': 13, 'max_age': 17},
                'young_adults': {'min_age': 18, 'max_age': 21}
            },
            'content_ratings': ['G', 'PG', 'PG-13', 'R', 'NC-17'],
            'safety_categories': [
                'inappropriate_content', 'predatory_behavior', 'cyberbullying',
                'privacy_violation', 'exploitation', 'grooming', 'harassment',
                'age_inappropriate', 'dangerous_activities', 'substance_abuse'
            ],
            'protection_levels': ['strict', 'moderate', 'relaxed'],
            'educational_topics': [
                'digital_citizenship', 'online_safety', 'privacy_protection',
                'cyberbullying_prevention', 'critical_thinking', 'media_literacy'
            ]
        }
        
        # Predatory behavior patterns
        self.predatory_patterns = {
            'grooming_language': [
                r'you\'re so mature for your age',
                r'don\'t tell your parents',
                r'this is our secret',
                r'you\'re special',
                r'meet me in person',
                r'send me photos',
                r'what are you wearing',
                r'are you alone'
            ],
            'inappropriate_requests': [
                r'send.*photo',
                r'what do you look like',
                r'are you home alone',
                r'meet.*private',
                r'don\'t tell anyone',
                r'personal information',
                r'phone number',
                r'address'
            ],
            'age_targeting': [
                r'how old are you',
                r'what grade are you in',
                r'when do you get home from school',
                r'are your parents home',
                r'young.*beautiful',
                r'cute.*kid'
            ],
            'isolation_tactics': [
                r'nobody understands you like i do',
                r'your parents don\'t get it',
                r'i\'m the only one who cares',
                r'they wouldn\'t understand',
                r'trust me',
                r'i\'m different'
            ]
        }
        
        # Age-inappropriate content patterns
        self.inappropriate_content_patterns = {
            'sexual_content': [
                r'explicit.*sexual',
                r'pornography',
                r'adult.*content',
                r'sexual.*activity',
                r'nude.*photos',
                r'sexual.*education.*explicit'
            ],
            'violence': [
                r'graphic.*violence',
                r'extreme.*violence',
                r'torture',
                r'murder.*details',
                r'gore',
                r'brutal.*attack'
            ],
            'substance_abuse': [
                r'how to.*drugs',
                r'buying.*alcohol',
                r'getting.*high',
                r'drug.*dealing',
                r'underage.*drinking',
                r'substance.*abuse'
            ],
            'dangerous_activities': [
                r'self.*harm',
                r'suicide.*methods',
                r'dangerous.*challenges',
                r'risky.*behavior',
                r'illegal.*activities',
                r'harmful.*pranks'
            ],
            'hate_speech': [
                r'racial.*slurs',
                r'hate.*speech',
                r'discriminatory.*language',
                r'bullying.*language',
                r'threatening.*language'
            ]
        }
        
        # Cyberbullying indicators
        self.cyberbullying_patterns = {
            'direct_attacks': [
                r'you\'re.*stupid',
                r'nobody likes you',
                r'kill yourself',
                r'you\'re ugly',
                r'loser',
                r'freak',
                r'weirdo'
            ],
            'social_exclusion': [
                r'don\'t talk to.*',
                r'ignore.*',
                r'nobody wants you here',
                r'go away',
                r'you don\'t belong'
            ],
            'threats': [
                r'i\'ll hurt you',
                r'watch your back',
                r'you\'ll regret this',
                r'i know where you live',
                r'i\'ll get you'
            ],
            'public_humiliation': [
                r'embarrassing.*photos',
                r'everyone will see',
                r'spread.*rumors',
                r'tell everyone',
                r'humiliate'
            ]
        }
        
        # Educational content indicators
        self.educational_indicators = {
            'digital_citizenship': [
                'online etiquette', 'digital footprint', 'responsible sharing',
                'respectful communication', 'digital rights', 'online behavior'
            ],
            'online_safety': [
                'password security', 'stranger danger', 'privacy settings',
                'safe browsing', 'reporting abuse', 'trusted adults'
            ],
            'critical_thinking': [
                'fact checking', 'reliable sources', 'media literacy',
                'fake news', 'verification', 'critical analysis'
            ],
            'cyberbullying_prevention': [
                'bystander intervention', 'reporting bullying', 'support systems',
                'empathy', 'kindness online', 'conflict resolution'
            ]
        }
        
        # Youth safety thresholds
        self.youth_safety_thresholds = {
            'critical_threat': 0.9,
            'high_risk': 0.7,
            'moderate_risk': 0.5,
            'low_risk': 0.3,
            'educational_opportunity': 0.6
        }
        
        # Youth safety metrics
        self.youth_safety_metrics = {
            'total_content_analyzed': 0,
            'predatory_behavior_detected': 0,
            'inappropriate_content_blocked': 0,
            'cyberbullying_incidents_prevented': 0,
            'educational_content_promoted': 0,
            'privacy_violations_prevented': 0,
            'youth_safety_interventions': 0
        }
        
        logger.info(f"Youth Safety Guardian Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content with focus on youth safety and child protection.
        
        The Youth Safety Guardian Agent evaluates:
        - Predatory behavior and grooming attempts
        - Age-inappropriate content and materials
        - Cyberbullying and harassment of minors
        - Privacy violations affecting children
        - Educational opportunities for digital safety
        - Parental control and oversight needs
        - Child exploitation and abuse indicators
        - Safe digital environment maintenance
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Detect predatory behavior
            predatory_analysis = await self._detect_predatory_behavior(content, context)
            
            # Check age-appropriate content
            age_appropriateness_analysis = await self._check_age_appropriateness(content, context)
            
            # Detect cyberbullying
            cyberbullying_analysis = await self._detect_cyberbullying(content, context)
            
            # Check privacy protection for minors
            privacy_analysis = await self._check_youth_privacy_protection(content, context)
            
            # Assess educational value
            educational_analysis = await self._assess_educational_value(content, context)
            
            # Check parental oversight needs
            parental_oversight_analysis = await self._check_parental_oversight_needs(content, context)
            
            # Detect exploitation indicators
            exploitation_analysis = await self._detect_exploitation_indicators(content, context)
            
            # Get AI provider analysis for youth safety
            ai_analysis = await self._get_ai_youth_safety_analysis(content, trust_score, context)
            
            # Make youth safety decision
            decision = await self._make_youth_safety_decision(
                content=content,
                trust_score=trust_score,
                predatory_analysis=predatory_analysis,
                age_appropriateness_analysis=age_appropriateness_analysis,
                cyberbullying_analysis=cyberbullying_analysis,
                privacy_analysis=privacy_analysis,
                educational_analysis=educational_analysis,
                parental_oversight_analysis=parental_oversight_analysis,
                exploitation_analysis=exploitation_analysis,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Update youth safety metrics
            await self._update_youth_safety_metrics(content, decision, context)
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Youth safety analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Youth safety analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'youth_safety_guardian', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Youth Safety Guardian Agent."""
        return [
            'predatory_behavior_detection',
            'age_appropriate_content_verification',
            'cyberbullying_prevention',
            'child_privacy_protection',
            'educational_content_promotion',
            'parental_oversight_support',
            'exploitation_prevention',
            'digital_safety_education',
            'youth_community_moderation',
            'child_protection_advocacy'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Youth Safety Guardian Agent."""
        return (
            "Specialized agent for child protection and youth safety. "
            "Detects predatory behavior, ensures age-appropriate content, "
            "prevents cyberbullying, and promotes safe digital environments for minors."
        )
    
    # Private analysis methods
    
    async def _detect_predatory_behavior(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect predatory behavior and grooming attempts."""
        try:
            predatory_analysis = {
                'predatory_indicators': [],
                'grooming_score': 0.0,
                'threat_level': 'low',
                'behavior_patterns': [],
                'immediate_intervention_needed': False
            }
            
            content_text = content.get('content', '').lower()
            author_info = context.get('author', {})
            
            # Check for grooming language
            grooming_score = 0.0
            for pattern in self.predatory_patterns['grooming_language']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    predatory_analysis['predatory_indicators'].append('grooming_language')
                    predatory_analysis['behavior_patterns'].append(f"Grooming language: {pattern}")
                    grooming_score += len(matches) * 0.3
            
            # Check for inappropriate requests
            for pattern in self.predatory_patterns['inappropriate_requests']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    predatory_analysis['predatory_indicators'].append('inappropriate_requests')
                    predatory_analysis['behavior_patterns'].append(f"Inappropriate request: {pattern}")
                    grooming_score += len(matches) * 0.4
            
            # Check for age targeting
            for pattern in self.predatory_patterns['age_targeting']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    predatory_analysis['predatory_indicators'].append('age_targeting')
                    predatory_analysis['behavior_patterns'].append(f"Age targeting: {pattern}")
                    grooming_score += len(matches) * 0.35
            
            # Check for isolation tactics
            for pattern in self.predatory_patterns['isolation_tactics']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    predatory_analysis['predatory_indicators'].append('isolation_tactics')
                    predatory_analysis['behavior_patterns'].append(f"Isolation tactic: {pattern}")
                    grooming_score += len(matches) * 0.25
            
            # Check author behavior patterns
            if author_info:
                # Check for adult targeting minors
                author_age = author_info.get('age')
                if author_age and author_age > 21:
                    # Look for targeting younger users
                    youth_targeting_indicators = [
                        'young', 'teen', 'student', 'school', 'kid', 'child'
                    ]
                    youth_mentions = sum(1 for indicator in youth_targeting_indicators 
                                       if indicator in content_text)
                    if youth_mentions > 2:
                        grooming_score += 0.3
                        predatory_analysis['behavior_patterns'].append("Adult targeting youth")
                
                # Check for private communication requests
                private_indicators = [
                    'dm me', 'private message', 'text me', 'call me',
                    'meet offline', 'in person', 'alone'
                ]
                private_requests = sum(1 for indicator in private_indicators 
                                     if indicator in content_text)
                if private_requests > 0:
                    grooming_score += private_requests * 0.2
                    predatory_analysis['behavior_patterns'].append("Private communication request")
            
            predatory_analysis['grooming_score'] = min(1.0, grooming_score)
            
            # Determine threat level
            if predatory_analysis['grooming_score'] >= self.youth_safety_thresholds['critical_threat']:
                predatory_analysis['threat_level'] = 'critical'
                predatory_analysis['immediate_intervention_needed'] = True
            elif predatory_analysis['grooming_score'] >= self.youth_safety_thresholds['high_risk']:
                predatory_analysis['threat_level'] = 'high'
                predatory_analysis['immediate_intervention_needed'] = True
            elif predatory_analysis['grooming_score'] >= self.youth_safety_thresholds['moderate_risk']:
                predatory_analysis['threat_level'] = 'moderate'
            elif predatory_analysis['grooming_score'] >= self.youth_safety_thresholds['low_risk']:
                predatory_analysis['threat_level'] = 'low'
            
            return predatory_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect predatory behavior: {str(e)}")
            return {'grooming_score': 0.0, 'error': str(e)}
    
    async def _check_age_appropriateness(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if content is age-appropriate for minors."""
        try:
            age_analysis = {
                'inappropriate_elements': [],
                'content_rating': 'G',
                'age_appropriateness_score': 1.0,
                'minimum_age': 0,
                'content_warnings': []
            }
            
            content_text = content.get('content', '').lower()
            content_type = content.get('type', 'text')
            
            inappropriateness_score = 0.0
            
            # Check for sexual content
            sexual_content_count = 0
            for pattern in self.inappropriate_content_patterns['sexual_content']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    age_analysis['inappropriate_elements'].append('sexual_content')
                    age_analysis['content_warnings'].append('Contains sexual content')
                    sexual_content_count += len(matches)
            
            if sexual_content_count > 0:
                inappropriateness_score += sexual_content_count * 0.4
                age_analysis['content_rating'] = 'R'
                age_analysis['minimum_age'] = 18
            
            # Check for violence
            violence_count = 0
            for pattern in self.inappropriate_content_patterns['violence']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    age_analysis['inappropriate_elements'].append('violence')
                    age_analysis['content_warnings'].append('Contains graphic violence')
                    violence_count += len(matches)
            
            if violence_count > 0:
                inappropriateness_score += violence_count * 0.3
                if age_analysis['content_rating'] == 'G':
                    age_analysis['content_rating'] = 'PG-13'
                    age_analysis['minimum_age'] = 13
            
            # Check for substance abuse
            substance_count = 0
            for pattern in self.inappropriate_content_patterns['substance_abuse']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    age_analysis['inappropriate_elements'].append('substance_abuse')
                    age_analysis['content_warnings'].append('Contains substance abuse content')
                    substance_count += len(matches)
            
            if substance_count > 0:
                inappropriateness_score += substance_count * 0.35
                age_analysis['content_rating'] = 'R'
                age_analysis['minimum_age'] = max(age_analysis['minimum_age'], 18)
            
            # Check for dangerous activities
            dangerous_count = 0
            for pattern in self.inappropriate_content_patterns['dangerous_activities']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    age_analysis['inappropriate_elements'].append('dangerous_activities')
                    age_analysis['content_warnings'].append('Contains dangerous activities')
                    dangerous_count += len(matches)
            
            if dangerous_count > 0:
                inappropriateness_score += dangerous_count * 0.4
                age_analysis['content_rating'] = 'R'
                age_analysis['minimum_age'] = max(age_analysis['minimum_age'], 18)
            
            # Check for hate speech
            hate_speech_count = 0
            for pattern in self.inappropriate_content_patterns['hate_speech']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    age_analysis['inappropriate_elements'].append('hate_speech')
                    age_analysis['content_warnings'].append('Contains hate speech')
                    hate_speech_count += len(matches)
            
            if hate_speech_count > 0:
                inappropriateness_score += hate_speech_count * 0.3
                if age_analysis['content_rating'] == 'G':
                    age_analysis['content_rating'] = 'PG-13'
                    age_analysis['minimum_age'] = max(age_analysis['minimum_age'], 13)
            
            # Calculate age appropriateness score
            age_analysis['age_appropriateness_score'] = max(0.0, 1.0 - inappropriateness_score)
            
            # Adjust content rating based on overall score
            if age_analysis['age_appropriateness_score'] < 0.3:
                age_analysis['content_rating'] = 'NC-17'
                age_analysis['minimum_age'] = 18
            elif age_analysis['age_appropriateness_score'] < 0.5:
                age_analysis['content_rating'] = 'R'
                age_analysis['minimum_age'] = max(age_analysis['minimum_age'], 17)
            elif age_analysis['age_appropriateness_score'] < 0.7:
                age_analysis['content_rating'] = 'PG-13'
                age_analysis['minimum_age'] = max(age_analysis['minimum_age'], 13)
            elif age_analysis['age_appropriateness_score'] < 0.9:
                age_analysis['content_rating'] = 'PG'
                age_analysis['minimum_age'] = max(age_analysis['minimum_age'], 8)
            
            return age_analysis
            
        except Exception as e:
            logger.error(f"Failed to check age appropriateness: {str(e)}")
            return {'age_appropriateness_score': 0.5, 'error': str(e)}
    
    async def _detect_cyberbullying(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect cyberbullying targeting minors."""
        try:
            cyberbullying_analysis = {
                'bullying_indicators': [],
                'bullying_score': 0.0,
                'bullying_type': 'none',
                'target_vulnerability': 'low',
                'intervention_needed': False
            }
            
            content_text = content.get('content', '').lower()
            target_info = context.get('target_user', {})
            
            bullying_score = 0.0
            
            # Check for direct attacks
            for pattern in self.cyberbullying_patterns['direct_attacks']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    cyberbullying_analysis['bullying_indicators'].append('direct_attacks')
                    cyberbullying_analysis['bullying_type'] = 'direct_attack'
                    bullying_score += len(matches) * 0.4
            
            # Check for social exclusion
            for pattern in self.cyberbullying_patterns['social_exclusion']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    cyberbullying_analysis['bullying_indicators'].append('social_exclusion')
                    cyberbullying_analysis['bullying_type'] = 'social_exclusion'
                    bullying_score += len(matches) * 0.3
            
            # Check for threats
            for pattern in self.cyberbullying_patterns['threats']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    cyberbullying_analysis['bullying_indicators'].append('threats')
                    cyberbullying_analysis['bullying_type'] = 'threats'
                    bullying_score += len(matches) * 0.5
            
            # Check for public humiliation
            for pattern in self.cyberbullying_patterns['public_humiliation']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    cyberbullying_analysis['bullying_indicators'].append('public_humiliation')
                    cyberbullying_analysis['bullying_type'] = 'public_humiliation'
                    bullying_score += len(matches) * 0.35
            
            # Check target vulnerability (if targeting a minor)
            if target_info:
                target_age = target_info.get('age', 0)
                if target_age < 18:
                    cyberbullying_analysis['target_vulnerability'] = 'high'
                    bullying_score += 0.2  # Increase severity for targeting minors
                elif target_age < 21:
                    cyberbullying_analysis['target_vulnerability'] = 'moderate'
                    bullying_score += 0.1
            
            cyberbullying_analysis['bullying_score'] = min(1.0, bullying_score)
            
            # Determine intervention needs
            if cyberbullying_analysis['bullying_score'] >= self.youth_safety_thresholds['high_risk']:
                cyberbullying_analysis['intervention_needed'] = True
            
            return cyberbullying_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect cyberbullying: {str(e)}")
            return {'bullying_score': 0.0, 'error': str(e)}
    
    async def _check_youth_privacy_protection(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check privacy protection for minors."""
        try:
            privacy_analysis = {
                'privacy_violations': [],
                'privacy_risk_score': 0.0,
                'personal_info_exposed': [],
                'coppa_compliance': True,
                'parental_consent_needed': False
            }
            
            content_text = content.get('content', '').lower()
            author_info = context.get('author', {})
            
            privacy_risk = 0.0
            
            # Check for personal information sharing
            personal_info_patterns = {
                'full_name': r'my name is [a-z]+ [a-z]+',
                'phone_number': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                'address': r'\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr)',
                'school_name': r'i go to [a-z\s]+ school',
                'email': r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b',
                'social_media': r'my instagram is|my snapchat is|my tiktok is'
            }
            
            for info_type, pattern in personal_info_patterns.items():
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    privacy_analysis['personal_info_exposed'].append(info_type)
                    privacy_analysis['privacy_violations'].append(f"Personal {info_type} shared")
                    privacy_risk += len(matches) * 0.3
            
            # Check if author is a minor
            author_age = author_info.get('age', 0)
            if author_age < 13:
                # COPPA compliance required
                privacy_analysis['coppa_compliance'] = False
                privacy_analysis['parental_consent_needed'] = True
                privacy_risk += 0.4
            elif author_age < 18:
                # Additional privacy protections for minors
                if privacy_analysis['personal_info_exposed']:
                    privacy_risk += 0.2
                    privacy_analysis['parental_consent_needed'] = True
            
            # Check for location sharing
            location_indicators = [
                'i live in', 'my address is', 'come find me at',
                'meet me at', 'i\'m at', 'currently at'
            ]
            
            location_sharing = sum(1 for indicator in location_indicators 
                                 if indicator in content_text)
            if location_sharing > 0:
                privacy_analysis['privacy_violations'].append('Location information shared')
                privacy_risk += location_sharing * 0.25
            
            # Check for photo/video sharing requests
            media_sharing_patterns = [
                'send me a photo', 'show me what you look like',
                'send a pic', 'video chat', 'facetime me'
            ]
            
            media_requests = sum(1 for pattern in media_sharing_patterns 
                               if pattern in content_text)
            if media_requests > 0:
                privacy_analysis['privacy_violations'].append('Media sharing requested')
                privacy_risk += media_requests * 0.3
            
            privacy_analysis['privacy_risk_score'] = min(1.0, privacy_risk)
            
            return privacy_analysis
            
        except Exception as e:
            logger.error(f"Failed to check youth privacy protection: {str(e)}")
            return {'privacy_risk_score': 0.0, 'error': str(e)}
    
    async def _assess_educational_value(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess educational value for youth development."""
        try:
            educational_analysis = {
                'educational_topics': [],
                'educational_score': 0.0,
                'learning_opportunities': [],
                'age_appropriate_learning': True,
                'promotes_positive_values': False
            }
            
            content_text = content.get('content', '').lower()
            
            educational_score = 0.0
            
            # Check for educational topics
            for topic, indicators in self.educational_indicators.items():
                topic_score = 0
                for indicator in indicators:
                    if indicator in content_text:
                        topic_score += 1
                        educational_analysis['learning_opportunities'].append(indicator)
                
                if topic_score > 0:
                    educational_analysis['educational_topics'].append(topic)
                    educational_score += topic_score * 0.1
            
            # Check for positive values promotion
            positive_values = [
                'kindness', 'respect', 'empathy', 'honesty', 'integrity',
                'responsibility', 'cooperation', 'tolerance', 'fairness',
                'helping others', 'community service', 'volunteering'
            ]
            
            positive_value_count = sum(1 for value in positive_values 
                                     if value in content_text)
            
            if positive_value_count > 0:
                educational_analysis['promotes_positive_values'] = True
                educational_score += positive_value_count * 0.15
            
            # Check for STEM education
            stem_indicators = [
                'science', 'technology', 'engineering', 'mathematics',
                'coding', 'programming', 'robotics', 'experiment',
                'research', 'innovation', 'problem solving'
            ]
            
            stem_count = sum(1 for indicator in stem_indicators 
                           if indicator in content_text)
            
            if stem_count > 0:
                educational_analysis['learning_opportunities'].append('STEM education')
                educational_score += stem_count * 0.12
            
            # Check for creative expression
            creative_indicators = [
                'art', 'music', 'writing', 'creativity', 'imagination',
                'storytelling', 'poetry', 'drawing', 'painting', 'design'
            ]
            
            creative_count = sum(1 for indicator in creative_indicators 
                               if indicator in content_text)
            
            if creative_count > 0:
                educational_analysis['learning_opportunities'].append('Creative expression')
                educational_score += creative_count * 0.1
            
            educational_analysis['educational_score'] = min(1.0, educational_score)
            
            return educational_analysis
            
        except Exception as e:
            logger.error(f"Failed to assess educational value: {str(e)}")
            return {'educational_score': 0.0, 'error': str(e)}
    
    async def _check_parental_oversight_needs(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if parental oversight is needed."""
        try:
            oversight_analysis = {
                'oversight_needed': False,
                'oversight_level': 'none',
                'notification_triggers': [],
                'parental_involvement_recommended': False,
                'supervision_areas': []
            }
            
            content_text = content.get('content', '').lower()
            author_info = context.get('author', {})
            
            # Check author age
            author_age = author_info.get('age', 0)
            
            if author_age < 13:
                oversight_analysis['oversight_needed'] = True
                oversight_analysis['oversight_level'] = 'strict'
                oversight_analysis['parental_involvement_recommended'] = True
                oversight_analysis['supervision_areas'].append('COPPA compliance required')
            elif author_age < 16:
                oversight_analysis['oversight_needed'] = True
                oversight_analysis['oversight_level'] = 'moderate'
                oversight_analysis['supervision_areas'].append('Teen supervision recommended')
            elif author_age < 18:
                oversight_analysis['oversight_level'] = 'minimal'
                oversight_analysis['supervision_areas'].append('Light supervision for minors')
            
            # Check for concerning content patterns
            concerning_patterns = [
                'meet in person', 'don\'t tell parents', 'secret',
                'private message', 'alone', 'send photos'
            ]
            
            concerning_count = sum(1 for pattern in concerning_patterns 
                                 if pattern in content_text)
            
            if concerning_count > 0:
                oversight_analysis['oversight_needed'] = True
                oversight_analysis['notification_triggers'].append('Concerning interaction patterns')
                oversight_analysis['parental_involvement_recommended'] = True
            
            # Check for risky behavior indicators
            risky_indicators = [
                'dangerous challenge', 'risky behavior', 'illegal activity',
                'substance use', 'self harm', 'meeting strangers'
            ]
            
            risky_count = sum(1 for indicator in risky_indicators 
                            if indicator in content_text)
            
            if risky_count > 0:
                oversight_analysis['oversight_needed'] = True
                oversight_analysis['oversight_level'] = 'strict'
                oversight_analysis['notification_triggers'].append('Risky behavior detected')
                oversight_analysis['parental_involvement_recommended'] = True
            
            return oversight_analysis
            
        except Exception as e:
            logger.error(f"Failed to check parental oversight needs: {str(e)}")
            return {'oversight_needed': False, 'error': str(e)}
    
    async def _detect_exploitation_indicators(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect child exploitation indicators."""
        try:
            exploitation_analysis = {
                'exploitation_indicators': [],
                'exploitation_score': 0.0,
                'exploitation_type': 'none',
                'immediate_action_required': False,
                'law_enforcement_alert': False
            }
            
            content_text = content.get('content', '').lower()
            
            exploitation_score = 0.0
            
            # Check for sexual exploitation indicators
            sexual_exploitation_patterns = [
                r'child.*sexual', r'minor.*sexual', r'underage.*sexual',
                r'child.*abuse', r'sexual.*exploitation', r'child.*pornography'
            ]
            
            for pattern in sexual_exploitation_patterns:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    exploitation_analysis['exploitation_indicators'].append('sexual_exploitation')
                    exploitation_analysis['exploitation_type'] = 'sexual'
                    exploitation_analysis['immediate_action_required'] = True
                    exploitation_analysis['law_enforcement_alert'] = True
                    exploitation_score += len(matches) * 1.0
            
            # Check for labor exploitation indicators
            labor_exploitation_patterns = [
                r'child.*labor', r'forced.*work', r'underage.*employment',
                r'exploitation.*work', r'child.*trafficking'
            ]
            
            for pattern in labor_exploitation_patterns:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    exploitation_analysis['exploitation_indicators'].append('labor_exploitation')
                    exploitation_analysis['exploitation_type'] = 'labor'
                    exploitation_analysis['immediate_action_required'] = True
                    exploitation_score += len(matches) * 0.8
            
            # Check for financial exploitation
            financial_exploitation_patterns = [
                r'child.*money', r'minor.*financial', r'underage.*payment',
                r'exploitation.*financial', r'child.*scam'
            ]
            
            for pattern in financial_exploitation_patterns:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    exploitation_analysis['exploitation_indicators'].append('financial_exploitation')
                    exploitation_analysis['exploitation_type'] = 'financial'
                    exploitation_score += len(matches) * 0.6
            
            # Check for emotional exploitation
            emotional_exploitation_patterns = [
                r'manipulate.*child', r'emotional.*abuse', r'psychological.*harm',
                r'child.*manipulation', r'minor.*coercion'
            ]
            
            for pattern in emotional_exploitation_patterns:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    exploitation_analysis['exploitation_indicators'].append('emotional_exploitation')
                    exploitation_analysis['exploitation_type'] = 'emotional'
                    exploitation_score += len(matches) * 0.5
            
            exploitation_analysis['exploitation_score'] = min(1.0, exploitation_score)
            
            # Determine action requirements
            if exploitation_analysis['exploitation_score'] >= 0.8:
                exploitation_analysis['immediate_action_required'] = True
                if exploitation_analysis['exploitation_type'] == 'sexual':
                    exploitation_analysis['law_enforcement_alert'] = True
            
            return exploitation_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect exploitation indicators: {str(e)}")
            return {'exploitation_score': 0.0, 'error': str(e)}
    
    async def _get_ai_youth_safety_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on youth safety."""
        try:
            prompt = self._create_youth_safety_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (Claude for youth safety analysis)
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
                'reasoning': 'No AI providers available for youth safety analysis'
            }
            
        except Exception as e:
            logger.error(f"AI youth safety analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_youth_safety_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a youth safety-focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='youth safety, child protection, and age-appropriate content'
        )
        
        youth_safety_specific = f"""
YOUTH SAFETY ANALYSIS

You are a specialized Youth Safety Guardian Agent focused on child protection,
age-appropriate content, and safe digital environments for minors.

User Trust Context:
- Author Trust Score: {trust_score}

Youth Safety Framework:
1. Predatory Behavior: Detect grooming, inappropriate contact, and exploitation attempts
2. Age Appropriateness: Ensure content is suitable for minors and age-appropriate
3. Cyberbullying: Identify and prevent bullying targeting children and teens
4. Privacy Protection: Safeguard personal information and ensure COPPA compliance
5. Educational Value: Promote positive learning and development opportunities
6. Parental Oversight: Determine when parental involvement is needed
7. Exploitation Prevention: Detect and prevent all forms of child exploitation
8. Digital Safety: Promote safe online behaviors and digital citizenship

Critical Youth Safety Threats:
- Predatory behavior and grooming attempts
- Sexual exploitation or inappropriate content
- Cyberbullying targeting minors
- Privacy violations affecting children
- Age-inappropriate content (violence, sexual, substance abuse)
- Dangerous activities or challenges
- Personal information sharing by minors
- Attempts to isolate children from parents/guardians
- Financial or emotional exploitation
- Hate speech or discrimination

Decision Guidelines:
- BLOCK: Immediate threats to child safety, predatory behavior, exploitation
- FLAG: Concerning interactions, age-inappropriate content, privacy violations
- EDUCATE: Opportunities for digital safety education and positive development
- APPROVE: Safe, age-appropriate, educational content

Youth Protection Priorities:
- Zero tolerance for predatory behavior or exploitation
- Strict age-appropriateness standards for content
- Immediate intervention for cyberbullying of minors
- Strong privacy protection for children under 18
- Promote positive digital citizenship and online safety
- Support educational and developmental content
- Ensure parental oversight when appropriate
- Report serious threats to appropriate authorities

CRITICAL: Any content that poses a threat to child safety, involves predatory
behavior, or exploits minors must be immediately blocked and flagged for
law enforcement review if necessary.

Age Considerations:
- Children (0-12): Strict supervision, COPPA compliance, educational focus
- Teens (13-17): Moderate oversight, privacy protection, cyberbullying prevention
- Young Adults (18-21): Light guidance, transition to adult responsibilities
"""
        
        return base_prompt + youth_safety_specific
    
    async def _make_youth_safety_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        predatory_analysis: Dict[str, Any],
        age_appropriateness_analysis: Dict[str, Any],
        cyberbullying_analysis: Dict[str, Any],
        privacy_analysis: Dict[str, Any],
        educational_analysis: Dict[str, Any],
        parental_oversight_analysis: Dict[str, Any],
        exploitation_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make youth safety-focused moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Handle critical exploitation threats
            if exploitation_analysis.get('immediate_action_required', False):
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'Child exploitation detected - immediate intervention required'
                base_decision['priority'] = 'critical'
                base_decision['law_enforcement_alert'] = exploitation_analysis.get('law_enforcement_alert', False)
                base_decision['immediate_intervention'] = True
                
            # Handle predatory behavior
            elif predatory_analysis.get('immediate_intervention_needed', False):
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'Predatory behavior detected - protecting minors'
                base_decision['priority'] = 'critical'
                base_decision['predatory_behavior_detected'] = True
                
            # Handle severe cyberbullying
            elif cyberbullying_analysis.get('intervention_needed', False):
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Cyberbullying targeting minors detected'
                base_decision['priority'] = 'high'
                base_decision['cyberbullying_intervention'] = True
                
            # Handle age-inappropriate content
            elif age_appropriateness_analysis.get('minimum_age', 0) > 13:
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Age-inappropriate content for minors'
                base_decision['priority'] = 'high'
                base_decision['age_restriction_needed'] = True
                
            # Handle privacy violations
            elif privacy_analysis.get('privacy_risk_score', 0) >= self.youth_safety_thresholds['high_risk']:
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Privacy protection needed for minors'
                base_decision['priority'] = 'medium'
                base_decision['privacy_protection_needed'] = True
                
            # Handle parental oversight needs
            elif parental_oversight_analysis.get('parental_involvement_recommended', False):
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Parental oversight recommended'
                base_decision['priority'] = 'medium'
                base_decision['parental_notification'] = True
                
            # Promote educational content
            elif educational_analysis.get('educational_score', 0) >= self.youth_safety_thresholds['educational_opportunity']:
                base_decision['action'] = 'approve'
                base_decision['reasoning'] = 'Educational content promoting youth development'
                base_decision['educational_value'] = True
            
            # Add youth safety-specific metadata
            base_decision['metadata'] = base_decision.get('metadata', {})
            base_decision['metadata'].update({
                'agent': 'youth_safety_guardian',
                'predatory_threat_level': predatory_analysis.get('threat_level', 'low'),
                'grooming_score': round(predatory_analysis.get('grooming_score', 0.0), 3),
                'content_rating': age_appropriateness_analysis.get('content_rating', 'G'),
                'minimum_age': age_appropriateness_analysis.get('minimum_age', 0),
                'cyberbullying_score': round(cyberbullying_analysis.get('bullying_score', 0.0), 3),
                'privacy_risk_score': round(privacy_analysis.get('privacy_risk_score', 0.0), 3),
                'educational_score': round(educational_analysis.get('educational_score', 0.0), 3),
                'oversight_level': parental_oversight_analysis.get('oversight_level', 'none'),
                'exploitation_score': round(exploitation_analysis.get('exploitation_score', 0.0), 3)
            })
            
            # Add detailed evidence
            base_decision['evidence'] = base_decision.get('evidence', {})
            base_decision['evidence'].update({
                'predatory_analysis': predatory_analysis,
                'age_appropriateness_analysis': age_appropriateness_analysis,
                'cyberbullying_analysis': cyberbullying_analysis,
                'privacy_analysis': privacy_analysis,
                'educational_analysis': educational_analysis,
                'parental_oversight_analysis': parental_oversight_analysis,
                'exploitation_analysis': exploitation_analysis
            })
            
            # Add youth safety recommendations
            if base_decision['action'] in ['block', 'flag']:
                recommendations = []
                
                if predatory_analysis.get('behavior_patterns'):
                    recommendations.extend([f"Address predatory pattern: {pattern}" for pattern in predatory_analysis['behavior_patterns']])
                
                if age_appropriateness_analysis.get('content_warnings'):
                    recommendations.extend([f"Content warning: {warning}" for warning in age_appropriateness_analysis['content_warnings']])
                
                if privacy_analysis.get('privacy_violations'):
                    recommendations.extend([f"Privacy protection: {violation}" for violation in privacy_analysis['privacy_violations']])
                
                if parental_oversight_analysis.get('supervision_areas'):
                    recommendations.extend([f"Supervision needed: {area}" for area in parental_oversight_analysis['supervision_areas']])
                
                base_decision['youth_safety_recommendations'] = recommendations
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make youth safety decision: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Youth safety decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'youth_safety_guardian', 'error': True}
            }
    
    async def _update_youth_safety_metrics(
        self, 
        content: Dict[str, Any], 
        decision: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> None:
        """Update youth safety metrics for performance tracking."""
        try:
            self.youth_safety_metrics['total_content_analyzed'] += 1
            
            # Track predatory behavior detection
            if decision.get('predatory_behavior_detected', False):
                self.youth_safety_metrics['predatory_behavior_detected'] += 1
            
            # Track inappropriate content blocking
            if decision.get('age_restriction_needed', False):
                self.youth_safety_metrics['inappropriate_content_blocked'] += 1
            
            # Track cyberbullying prevention
            if decision.get('cyberbullying_intervention', False):
                self.youth_safety_metrics['cyberbullying_incidents_prevented'] += 1
            
            # Track educational content promotion
            if decision.get('educational_value', False):
                self.youth_safety_metrics['educational_content_promoted'] += 1
            
            # Track privacy protection
            if decision.get('privacy_protection_needed', False):
                self.youth_safety_metrics['privacy_violations_prevented'] += 1
            
            # Track overall interventions
            if decision.get('immediate_intervention', False):
                self.youth_safety_metrics['youth_safety_interventions'] += 1
            
        except Exception as e:
            logger.error(f"Failed to update youth safety metrics: {str(e)}")