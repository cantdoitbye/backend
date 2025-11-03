# Mental Health Support Agent for TrustStream v4.4
# Specialized agent for mental health awareness and crisis intervention

import logging
import json
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class MentalHealthSupportAgent(BaseAIAgent):
    """
    Mental Health Support Agent - Specialized Mental Health and Crisis Intervention
    
    This agent focuses on identifying mental health concerns, providing crisis
    intervention, offering support resources, and promoting mental wellness
    within community interactions.
    
    Key Responsibilities:
    - Crisis intervention and suicide prevention
    - Mental health concern identification
    - Support resource provision
    - Wellness promotion and education
    - Stigma reduction and awareness
    - Self-harm prevention
    - Emotional support facilitation
    - Professional help referrals
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Mental health configuration
        self.mental_health_config = {
            'crisis_indicators': [
                'suicide', 'self_harm', 'ending_it_all', 'no_point_living',
                'better_off_dead', 'kill_myself', 'hurt_myself', 'can_not_go_on'
            ],
            'mental_health_concerns': [
                'depression', 'anxiety', 'panic_attacks', 'bipolar',
                'ptsd', 'eating_disorder', 'addiction', 'ocd',
                'schizophrenia', 'borderline', 'trauma', 'grief'
            ],
            'emotional_distress_signals': [
                'hopeless', 'worthless', 'empty', 'numb', 'overwhelmed',
                'trapped', 'burden', 'alone', 'scared', 'angry'
            ],
            'risk_levels': {
                'critical': 0.9,  # Immediate crisis intervention needed
                'high': 0.7,      # Urgent mental health support required
                'medium': 0.5,    # Mental health resources recommended
                'low': 0.3        # General wellness support
            }
        }
        
        # Crisis detection patterns
        self.crisis_patterns = {
            'suicide_ideation': [
                r'want to (die|kill myself|end it all)',
                r'(thinking about|planning) suicide',
                r'better off (dead|gone)',
                r'no reason to (live|continue)',
                r'can\'t (take it|go on) anymore'
            ],
            'self_harm': [
                r'(cutting|hurting) myself',
                r'want to (hurt|harm) myself',
                r'self (injury|harm|mutilation)',
                r'(burning|scratching) myself'
            ],
            'hopelessness': [
                r'no (hope|point|future)',
                r'nothing (matters|helps)',
                r'(completely|totally) hopeless',
                r'no way (out|forward)'
            ],
            'isolation': [
                r'(completely|totally) alone',
                r'no one (cares|understands)',
                r'(isolated|abandoned) by everyone',
                r'nobody (loves|wants) me'
            ]
        }
        
        # Support resources
        self.support_resources = {
            'crisis_hotlines': {
                'national_suicide_prevention': '988',
                'crisis_text_line': 'Text HOME to 741741',
                'international_association': '+1-703-312-9400'
            },
            'mental_health_resources': {
                'nami': 'National Alliance on Mental Illness',
                'samhsa': 'Substance Abuse and Mental Health Services',
                'psychology_today': 'Find a Therapist Directory'
            },
            'online_support': {
                'betterhelp': 'Online Therapy Platform',
                'talkspace': 'Online Therapy Services',
                'crisis_chat': '7cups.com - Free Emotional Support'
            }
        }
        
        # Mental health thresholds
        self.mental_health_thresholds = {
            'crisis_intervention': 0.85,
            'urgent_support': 0.7,
            'mental_health_resources': 0.5,
            'wellness_promotion': 0.3
        }
        
        # Mental health metrics
        self.mental_health_metrics = {
            'total_content_analyzed': 0,
            'crisis_interventions': 0,
            'mental_health_support_provided': 0,
            'resources_shared': 0,
            'wellness_promotion': 0,
            'stigma_reduction_efforts': 0
        }
        
        logger.info(f"Mental Health Support Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content with focus on mental health support and crisis intervention.
        
        The Mental Health Support Agent evaluates:
        - Crisis indicators and suicide risk
        - Mental health concerns and distress signals
        - Self-harm and dangerous behaviors
        - Emotional support needs
        - Stigma and discrimination issues
        - Wellness and recovery opportunities
        - Professional help requirements
        - Community support facilitation
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Detect crisis indicators
            crisis_analysis = await self._detect_crisis_indicators(content, context)
            
            # Analyze mental health concerns
            mental_health_analysis = await self._analyze_mental_health_concerns(content, context)
            
            # Assess emotional distress
            distress_analysis = await self._assess_emotional_distress(content, context)
            
            # Evaluate support needs
            support_analysis = await self._evaluate_support_needs(content, context)
            
            # Check for stigma and discrimination
            stigma_analysis = await self._check_mental_health_stigma(content, context)
            
            # Analyze wellness opportunities
            wellness_analysis = await self._analyze_wellness_opportunities(content, context)
            
            # Assess professional help needs
            professional_help_analysis = await self._assess_professional_help_needs(content, context)
            
            # Get AI provider analysis for mental health support
            ai_analysis = await self._get_ai_mental_health_analysis(content, trust_score, context)
            
            # Make mental health support decision
            decision = await self._make_mental_health_decision(
                content=content,
                trust_score=trust_score,
                crisis_analysis=crisis_analysis,
                mental_health_analysis=mental_health_analysis,
                distress_analysis=distress_analysis,
                support_analysis=support_analysis,
                stigma_analysis=stigma_analysis,
                wellness_analysis=wellness_analysis,
                professional_help_analysis=professional_help_analysis,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Update mental health metrics
            await self._update_mental_health_metrics(content, decision, context)
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Mental health support analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Mental health support analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'mental_health_support', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Mental Health Support Agent."""
        return [
            'crisis_intervention',
            'suicide_prevention',
            'mental_health_assessment',
            'emotional_support_facilitation',
            'resource_provision',
            'stigma_reduction',
            'wellness_promotion',
            'professional_referrals',
            'self_harm_prevention',
            'community_support_coordination'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Mental Health Support Agent."""
        return (
            "Specialized agent for mental health support and crisis intervention. "
            "Identifies mental health concerns, provides crisis intervention, offers "
            "support resources, and promotes mental wellness within communities."
        )
    
    # Private analysis methods
    
    async def _detect_crisis_indicators(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect crisis indicators and suicide risk."""
        try:
            crisis_analysis = {
                'crisis_detected': False,
                'crisis_types': [],
                'crisis_severity': 'low',
                'immediate_intervention_needed': False,
                'crisis_score': 0.0
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for suicide ideation patterns
            suicide_score = 0.0
            for pattern in self.crisis_patterns['suicide_ideation']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    crisis_analysis['crisis_detected'] = True
                    crisis_analysis['crisis_types'].append('suicide_ideation')
                    suicide_score += 0.4
            
            # Check for self-harm patterns
            self_harm_score = 0.0
            for pattern in self.crisis_patterns['self_harm']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    crisis_analysis['crisis_detected'] = True
                    crisis_analysis['crisis_types'].append('self_harm')
                    self_harm_score += 0.35
            
            # Check for hopelessness patterns
            hopelessness_score = 0.0
            for pattern in self.crisis_patterns['hopelessness']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    crisis_analysis['crisis_detected'] = True
                    crisis_analysis['crisis_types'].append('hopelessness')
                    hopelessness_score += 0.25
            
            # Check for isolation patterns
            isolation_score = 0.0
            for pattern in self.crisis_patterns['isolation']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    crisis_analysis['crisis_detected'] = True
                    crisis_analysis['crisis_types'].append('isolation')
                    isolation_score += 0.2
            
            # Check for direct crisis keywords
            crisis_keywords = self.mental_health_config['crisis_indicators']
            crisis_keyword_count = sum(1 for keyword in crisis_keywords 
                                     if keyword in content_text)
            
            if crisis_keyword_count > 0:
                crisis_analysis['crisis_detected'] = True
                crisis_analysis['crisis_score'] += crisis_keyword_count * 0.3
            
            # Calculate overall crisis score
            crisis_analysis['crisis_score'] = max([
                suicide_score, self_harm_score, hopelessness_score, 
                isolation_score, crisis_analysis['crisis_score']
            ])
            
            # Determine crisis severity
            if crisis_analysis['crisis_score'] >= self.mental_health_config['risk_levels']['critical']:
                crisis_analysis['crisis_severity'] = 'critical'
                crisis_analysis['immediate_intervention_needed'] = True
            elif crisis_analysis['crisis_score'] >= self.mental_health_config['risk_levels']['high']:
                crisis_analysis['crisis_severity'] = 'high'
                crisis_analysis['immediate_intervention_needed'] = True
            elif crisis_analysis['crisis_score'] >= self.mental_health_config['risk_levels']['medium']:
                crisis_analysis['crisis_severity'] = 'medium'
            
            return crisis_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect crisis indicators: {str(e)}")
            return {'crisis_score': 0.5, 'error': str(e)}
    
    async def _analyze_mental_health_concerns(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze mental health concerns and conditions."""
        try:
            mental_health_analysis = {
                'concerns_detected': False,
                'condition_types': [],
                'concern_severity': 'low',
                'support_needed': False,
                'mental_health_score': 0.0
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for mental health conditions
            conditions = self.mental_health_config['mental_health_concerns']
            condition_mentions = []
            
            for condition in conditions:
                if condition in content_text:
                    mental_health_analysis['concerns_detected'] = True
                    mental_health_analysis['condition_types'].append(condition)
                    condition_mentions.append(condition)
                    
                    # Weight different conditions by severity
                    if condition in ['suicide', 'self_harm', 'bipolar', 'schizophrenia']:
                        mental_health_analysis['mental_health_score'] += 0.4
                    elif condition in ['depression', 'anxiety', 'ptsd', 'eating_disorder']:
                        mental_health_analysis['mental_health_score'] += 0.3
                    else:
                        mental_health_analysis['mental_health_score'] += 0.2
            
            # Check for treatment-related language
            treatment_indicators = [
                'therapy', 'counseling', 'medication', 'psychiatrist',
                'psychologist', 'treatment', 'mental health professional'
            ]
            
            treatment_mentions = sum(1 for indicator in treatment_indicators 
                                   if indicator in content_text)
            
            if treatment_mentions > 0:
                mental_health_analysis['concerns_detected'] = True
                mental_health_analysis['mental_health_score'] += 0.1
            
            # Check for symptom descriptions
            symptom_indicators = [
                'can\'t sleep', 'no appetite', 'panic attacks', 'flashbacks',
                'mood swings', 'hallucinations', 'delusions', 'paranoia',
                'intrusive thoughts', 'compulsions', 'dissociation'
            ]
            
            symptom_count = sum(1 for symptom in symptom_indicators 
                              if symptom in content_text)
            
            if symptom_count > 0:
                mental_health_analysis['concerns_detected'] = True
                mental_health_analysis['mental_health_score'] += symptom_count * 0.15
            
            # Determine concern severity
            if mental_health_analysis['mental_health_score'] >= self.mental_health_config['risk_levels']['high']:
                mental_health_analysis['concern_severity'] = 'high'
                mental_health_analysis['support_needed'] = True
            elif mental_health_analysis['mental_health_score'] >= self.mental_health_config['risk_levels']['medium']:
                mental_health_analysis['concern_severity'] = 'medium'
                mental_health_analysis['support_needed'] = True
            elif mental_health_analysis['mental_health_score'] >= self.mental_health_config['risk_levels']['low']:
                mental_health_analysis['concern_severity'] = 'low'
            
            return mental_health_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze mental health concerns: {str(e)}")
            return {'mental_health_score': 0.5, 'error': str(e)}
    
    async def _assess_emotional_distress(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess emotional distress signals."""
        try:
            distress_analysis = {
                'distress_detected': False,
                'distress_signals': [],
                'emotional_state': 'stable',
                'distress_level': 0.0,
                'support_recommended': False
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for emotional distress signals
            distress_signals = self.mental_health_config['emotional_distress_signals']
            
            for signal in distress_signals:
                if signal in content_text:
                    distress_analysis['distress_detected'] = True
                    distress_analysis['distress_signals'].append(signal)
                    
                    # Weight different signals by intensity
                    if signal in ['hopeless', 'worthless', 'trapped']:
                        distress_analysis['distress_level'] += 0.3
                    elif signal in ['overwhelmed', 'empty', 'numb']:
                        distress_analysis['distress_level'] += 0.25
                    else:
                        distress_analysis['distress_level'] += 0.2
            
            # Check for emotional intensity indicators
            intensity_indicators = [
                'extremely', 'completely', 'totally', 'absolutely',
                'unbearably', 'incredibly', 'devastatingly'
            ]
            
            intensity_count = sum(1 for indicator in intensity_indicators 
                                if indicator in content_text)
            
            if intensity_count > 0:
                distress_analysis['distress_level'] += intensity_count * 0.1
            
            # Check for crying/emotional expression
            emotional_expression = [
                'crying', 'tears', 'sobbing', 'weeping',
                'breaking down', 'falling apart', 'emotional wreck'
            ]
            
            expression_count = sum(1 for expression in emotional_expression 
                                 if expression in content_text)
            
            if expression_count > 0:
                distress_analysis['distress_detected'] = True
                distress_analysis['distress_level'] += expression_count * 0.15
            
            # Determine emotional state
            if distress_analysis['distress_level'] >= 0.7:
                distress_analysis['emotional_state'] = 'severe_distress'
                distress_analysis['support_recommended'] = True
            elif distress_analysis['distress_level'] >= 0.5:
                distress_analysis['emotional_state'] = 'moderate_distress'
                distress_analysis['support_recommended'] = True
            elif distress_analysis['distress_level'] >= 0.3:
                distress_analysis['emotional_state'] = 'mild_distress'
            
            return distress_analysis
            
        except Exception as e:
            logger.error(f"Failed to assess emotional distress: {str(e)}")
            return {'distress_level': 0.5, 'error': str(e)}
    
    async def _evaluate_support_needs(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate support needs and resource requirements."""
        try:
            support_analysis = {
                'support_needed': False,
                'support_types': [],
                'urgency_level': 'low',
                'resource_recommendations': [],
                'community_support_potential': 0.0
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for explicit help requests
            help_requests = [
                'need help', 'please help', 'can someone help',
                'looking for support', 'need advice', 'desperate for help'
            ]
            
            help_request_count = sum(1 for request in help_requests 
                                   if request in content_text)
            
            if help_request_count > 0:
                support_analysis['support_needed'] = True
                support_analysis['support_types'].append('explicit_help_request')
                support_analysis['urgency_level'] = 'medium'
            
            # Check for professional help indicators
            professional_indicators = [
                'need therapy', 'see a therapist', 'professional help',
                'mental health professional', 'psychiatrist', 'counselor'
            ]
            
            professional_count = sum(1 for indicator in professional_indicators 
                                   if indicator in content_text)
            
            if professional_count > 0:
                support_analysis['support_needed'] = True
                support_analysis['support_types'].append('professional_help')
                support_analysis['resource_recommendations'].append('professional_therapy')
            
            # Check for peer support indicators
            peer_support_indicators = [
                'talk to someone', 'need someone to listen', 'share my story',
                'others who understand', 'support group', 'peer support'
            ]
            
            peer_support_count = sum(1 for indicator in peer_support_indicators 
                                   if indicator in content_text)
            
            if peer_support_count > 0:
                support_analysis['support_needed'] = True
                support_analysis['support_types'].append('peer_support')
                support_analysis['resource_recommendations'].append('support_groups')
                support_analysis['community_support_potential'] += 0.3
            
            # Check for crisis support indicators
            crisis_support_indicators = [
                'crisis', 'emergency', 'urgent help', 'immediate help',
                'can\'t wait', 'right now', 'tonight'
            ]
            
            crisis_support_count = sum(1 for indicator in crisis_support_indicators 
                                     if indicator in content_text)
            
            if crisis_support_count > 0:
                support_analysis['support_needed'] = True
                support_analysis['support_types'].append('crisis_intervention')
                support_analysis['urgency_level'] = 'critical'
                support_analysis['resource_recommendations'].append('crisis_hotline')
            
            # Check for medication/treatment support
            treatment_support_indicators = [
                'medication help', 'treatment options', 'therapy types',
                'finding a doctor', 'insurance coverage', 'affordable help'
            ]
            
            treatment_support_count = sum(1 for indicator in treatment_support_indicators 
                                        if indicator in content_text)
            
            if treatment_support_count > 0:
                support_analysis['support_needed'] = True
                support_analysis['support_types'].append('treatment_navigation')
                support_analysis['resource_recommendations'].append('treatment_resources')
            
            return support_analysis
            
        except Exception as e:
            logger.error(f"Failed to evaluate support needs: {str(e)}")
            return {'community_support_potential': 0.5, 'error': str(e)}
    
    async def _check_mental_health_stigma(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for mental health stigma and discrimination."""
        try:
            stigma_analysis = {
                'stigma_detected': False,
                'stigma_types': [],
                'discrimination_indicators': [],
                'stigma_severity': 'low',
                'education_needed': False
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for stigmatizing language
            stigmatizing_terms = [
                'crazy', 'insane', 'mental', 'psycho', 'nuts',
                'loony', 'wacko', 'deranged', 'unhinged', 'mad'
            ]
            
            stigma_count = sum(1 for term in stigmatizing_terms 
                             if term in content_text)
            
            if stigma_count > 0:
                stigma_analysis['stigma_detected'] = True
                stigma_analysis['stigma_types'].append('stigmatizing_language')
                stigma_analysis['education_needed'] = True
            
            # Check for mental health discrimination
            discrimination_indicators = [
                'mental health excuse', 'just get over it', 'all in your head',
                'attention seeking', 'weakness', 'character flaw',
                'not real illness', 'just sad', 'everyone gets sad'
            ]
            
            discrimination_count = sum(1 for indicator in discrimination_indicators 
                                     if indicator in content_text)
            
            if discrimination_count > 0:
                stigma_analysis['stigma_detected'] = True
                stigma_analysis['discrimination_indicators'].append('mental_health_denial')
                stigma_analysis['education_needed'] = True
            
            # Check for treatment stigma
            treatment_stigma_indicators = [
                'therapy is for weak', 'medication crutch', 'just talk therapy',
                'pills don\'t help', 'waste of money', 'not real medicine'
            ]
            
            treatment_stigma_count = sum(1 for indicator in treatment_stigma_indicators 
                                       if indicator in content_text)
            
            if treatment_stigma_count > 0:
                stigma_analysis['stigma_detected'] = True
                stigma_analysis['stigma_types'].append('treatment_stigma')
                stigma_analysis['education_needed'] = True
            
            # Determine stigma severity
            total_stigma_indicators = stigma_count + discrimination_count + treatment_stigma_count
            
            if total_stigma_indicators >= 3:
                stigma_analysis['stigma_severity'] = 'high'
            elif total_stigma_indicators >= 2:
                stigma_analysis['stigma_severity'] = 'medium'
            elif total_stigma_indicators >= 1:
                stigma_analysis['stigma_severity'] = 'low'
            
            return stigma_analysis
            
        except Exception as e:
            logger.error(f"Failed to check mental health stigma: {str(e)}")
            return {'stigma_severity': 'low', 'error': str(e)}
    
    async def _analyze_wellness_opportunities(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze wellness and recovery opportunities."""
        try:
            wellness_analysis = {
                'wellness_potential': 0.5,
                'wellness_indicators': [],
                'recovery_elements': [],
                'positive_coping_strategies': [],
                'community_wellness_opportunity': False
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for positive wellness indicators
            wellness_indicators = [
                'feeling better', 'getting help', 'therapy helping',
                'medication working', 'support system', 'coping strategies',
                'self care', 'mindfulness', 'exercise', 'healthy habits'
            ]
            
            wellness_count = sum(1 for indicator in wellness_indicators 
                               if indicator in content_text)
            
            if wellness_count > 0:
                wellness_analysis['wellness_indicators'] = [
                    indicator for indicator in wellness_indicators 
                    if indicator in content_text
                ]
                wellness_analysis['wellness_potential'] += wellness_count * 0.1
            
            # Check for recovery language
            recovery_indicators = [
                'recovery', 'healing', 'progress', 'improvement',
                'getting stronger', 'moving forward', 'hope',
                'resilience', 'overcoming', 'survivor'
            ]
            
            recovery_count = sum(1 for indicator in recovery_indicators 
                               if indicator in content_text)
            
            if recovery_count > 0:
                wellness_analysis['recovery_elements'] = [
                    indicator for indicator in recovery_indicators 
                    if indicator in content_text
                ]
                wellness_analysis['wellness_potential'] += recovery_count * 0.15
            
            # Check for positive coping strategies
            coping_strategies = [
                'meditation', 'journaling', 'talking to friends',
                'exercise', 'art therapy', 'music therapy',
                'breathing exercises', 'grounding techniques'
            ]
            
            coping_count = sum(1 for strategy in coping_strategies 
                             if strategy in content_text)
            
            if coping_count > 0:
                wellness_analysis['positive_coping_strategies'] = [
                    strategy for strategy in coping_strategies 
                    if strategy in content_text
                ]
                wellness_analysis['wellness_potential'] += coping_count * 0.1
            
            # Check for community wellness opportunity
            community_wellness_indicators = [
                'share experience', 'help others', 'support group',
                'peer support', 'mental health awareness',
                'reduce stigma', 'educate others'
            ]
            
            community_wellness_count = sum(1 for indicator in community_wellness_indicators 
                                         if indicator in content_text)
            
            if community_wellness_count > 0:
                wellness_analysis['community_wellness_opportunity'] = True
                wellness_analysis['wellness_potential'] += 0.2
            
            # Cap wellness potential
            wellness_analysis['wellness_potential'] = min(1.0, wellness_analysis['wellness_potential'])
            
            return wellness_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze wellness opportunities: {str(e)}")
            return {'wellness_potential': 0.5, 'error': str(e)}
    
    async def _assess_professional_help_needs(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess need for professional mental health intervention."""
        try:
            professional_help_analysis = {
                'professional_help_needed': False,
                'urgency_level': 'low',
                'recommended_services': [],
                'referral_priority': 'routine',
                'intervention_type': 'none'
            }
            
            content_text = content.get('content', '').lower()
            
            # Check for severe symptoms requiring professional help
            severe_symptoms = [
                'hallucinations', 'delusions', 'paranoia', 'psychosis',
                'manic episode', 'severe depression', 'panic disorder',
                'eating disorder', 'substance abuse', 'addiction'
            ]
            
            severe_symptom_count = sum(1 for symptom in severe_symptoms 
                                     if symptom in content_text)
            
            if severe_symptom_count > 0:
                professional_help_analysis['professional_help_needed'] = True
                professional_help_analysis['urgency_level'] = 'high'
                professional_help_analysis['recommended_services'].append('psychiatric_evaluation')
                professional_help_analysis['referral_priority'] = 'urgent'
                professional_help_analysis['intervention_type'] = 'psychiatric'
            
            # Check for therapy indicators
            therapy_indicators = [
                'trauma', 'ptsd', 'anxiety disorder', 'depression',
                'grief counseling', 'relationship issues', 'family therapy'
            ]
            
            therapy_count = sum(1 for indicator in therapy_indicators 
                              if indicator in content_text)
            
            if therapy_count > 0:
                professional_help_analysis['professional_help_needed'] = True
                professional_help_analysis['recommended_services'].append('psychotherapy')
                if professional_help_analysis['intervention_type'] == 'none':
                    professional_help_analysis['intervention_type'] = 'therapeutic'
            
            # Check for medication management needs
            medication_indicators = [
                'medication not working', 'side effects', 'dosage issues',
                'need medication', 'psychiatric medication', 'mood stabilizer'
            ]
            
            medication_count = sum(1 for indicator in medication_indicators 
                                 if indicator in content_text)
            
            if medication_count > 0:
                professional_help_analysis['professional_help_needed'] = True
                professional_help_analysis['recommended_services'].append('medication_management')
                professional_help_analysis['urgency_level'] = 'medium'
            
            # Check for specialized treatment needs
            specialized_indicators = [
                'eating disorder treatment', 'addiction treatment',
                'trauma therapy', 'couples therapy', 'family therapy',
                'group therapy', 'intensive outpatient'
            ]
            
            specialized_count = sum(1 for indicator in specialized_indicators 
                                  if indicator in content_text)
            
            if specialized_count > 0:
                professional_help_analysis['professional_help_needed'] = True
                professional_help_analysis['recommended_services'].append('specialized_treatment')
            
            return professional_help_analysis
            
        except Exception as e:
            logger.error(f"Failed to assess professional help needs: {str(e)}")
            return {'professional_help_needed': False, 'error': str(e)}
    
    async def _get_ai_mental_health_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on mental health support."""
        try:
            prompt = self._create_mental_health_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (Claude for mental health analysis)
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
                'reasoning': 'No AI providers available for mental health analysis'
            }
            
        except Exception as e:
            logger.error(f"AI mental health analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_mental_health_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a mental health support focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='mental health support, crisis intervention, and wellness promotion'
        )
        
        mental_health_specific = f"""
MENTAL HEALTH SUPPORT ANALYSIS

You are a specialized Mental Health Support Agent focused on crisis intervention,
mental health awareness, and providing appropriate support and resources.

User Trust Context:
- Author Trust Score: {trust_score}

Mental Health Support Framework:
1. Crisis Intervention: Identify suicide risk and self-harm indicators
2. Mental Health Assessment: Recognize mental health concerns and conditions
3. Emotional Support: Provide empathetic and supportive responses
4. Resource Provision: Offer appropriate mental health resources and referrals
5. Stigma Reduction: Combat mental health stigma and discrimination
6. Wellness Promotion: Encourage positive coping and recovery
7. Professional Referrals: Recommend appropriate professional help
8. Community Support: Facilitate peer support and understanding

Critical Mental Health Indicators:
- Suicide ideation and self-harm expressions
- Crisis language and immediate danger signals
- Mental health conditions and severe symptoms
- Emotional distress and hopelessness
- Help-seeking behavior and support requests
- Treatment and medication concerns
- Stigma and discrimination against mental health
- Professional intervention requirements

Decision Guidelines:
- CRISIS: Immediate intervention for suicide risk or self-harm
- SUPPORT: Provide resources and support for mental health concerns
- EDUCATE: Address stigma and promote mental health awareness
- APPROVE: Mental health positive and supportive content

Support Priorities:
- Prioritize immediate safety and crisis intervention
- Provide compassionate and non-judgmental support
- Offer appropriate resources and professional referrals
- Combat stigma and promote mental health awareness
- Encourage help-seeking and treatment engagement
- Foster supportive community environments
- Promote wellness and recovery-oriented approaches

CRITICAL: Any content indicating suicide risk, self-harm, or mental health crisis
requires immediate supportive intervention and resource provision.

Available Resources:
- Crisis Hotlines: 988 (National Suicide Prevention Lifeline)
- Crisis Text Line: Text HOME to 741741
- Online Support: 7cups.com, BetterHelp, Talkspace
- Professional Resources: Psychology Today therapist directory
"""
        
        return base_prompt + mental_health_specific
    
    async def _make_mental_health_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        crisis_analysis: Dict[str, Any],
        mental_health_analysis: Dict[str, Any],
        distress_analysis: Dict[str, Any],
        support_analysis: Dict[str, Any],
        stigma_analysis: Dict[str, Any],
        wellness_analysis: Dict[str, Any],
        professional_help_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make mental health support focused moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Handle crisis situations with highest priority
            if crisis_analysis.get('immediate_intervention_needed', False):
                base_decision['action'] = 'support'  # Special action for mental health support
                base_decision['reasoning'] = 'Mental health crisis detected - immediate support needed'
                base_decision['priority'] = 'critical'
                base_decision['crisis_intervention'] = True
                base_decision['support_resources'] = self.support_resources['crisis_hotlines']
                
            # Handle high mental health concerns
            elif mental_health_analysis.get('support_needed', False):
                base_decision['action'] = 'support'
                base_decision['reasoning'] = 'Mental health support needed'
                base_decision['priority'] = 'high'
                base_decision['mental_health_support'] = True
                base_decision['support_resources'] = self.support_resources['mental_health_resources']
            
            # Handle emotional distress
            elif distress_analysis.get('support_recommended', False):
                base_decision['action'] = 'support'
                base_decision['reasoning'] = 'Emotional distress detected - support recommended'
                base_decision['priority'] = 'medium'
                base_decision['emotional_support'] = True
                base_decision['support_resources'] = self.support_resources['online_support']
            
            # Handle stigma and discrimination
            elif stigma_analysis.get('education_needed', False):
                base_decision['action'] = 'educate'  # Special action for education
                base_decision['reasoning'] = 'Mental health stigma detected - education needed'
                base_decision['priority'] = 'medium'
                base_decision['stigma_education'] = True
            
            # Handle professional help needs
            if professional_help_analysis.get('professional_help_needed', False):
                base_decision['professional_referral'] = True
                base_decision['recommended_services'] = professional_help_analysis.get('recommended_services', [])
                base_decision['referral_priority'] = professional_help_analysis.get('referral_priority', 'routine')
            
            # Add wellness opportunities
            if wellness_analysis.get('community_wellness_opportunity', False):
                base_decision['wellness_opportunity'] = True
                base_decision['community_support_potential'] = True
            
            # Add mental health-specific metadata
            base_decision['metadata'] = base_decision.get('metadata', {})
            base_decision['metadata'].update({
                'agent': 'mental_health_support',
                'crisis_detected': crisis_analysis.get('crisis_detected', False),
                'crisis_severity': crisis_analysis.get('crisis_severity', 'low'),
                'mental_health_concerns': mental_health_analysis.get('condition_types', []),
                'distress_level': round(distress_analysis.get('distress_level', 0.0), 3),
                'support_urgency': support_analysis.get('urgency_level', 'low'),
                'stigma_detected': stigma_analysis.get('stigma_detected', False),
                'wellness_potential': round(wellness_analysis.get('wellness_potential', 0.5), 3),
                'professional_help_needed': professional_help_analysis.get('professional_help_needed', False)
            })
            
            # Add detailed evidence
            base_decision['evidence'] = base_decision.get('evidence', {})
            base_decision['evidence'].update({
                'crisis_analysis': crisis_analysis,
                'mental_health_analysis': mental_health_analysis,
                'distress_analysis': distress_analysis,
                'support_analysis': support_analysis,
                'stigma_analysis': stigma_analysis,
                'wellness_analysis': wellness_analysis,
                'professional_help_analysis': professional_help_analysis
            })
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make mental health decision: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Mental health decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'mental_health_support', 'error': True}
            }
    
    async def _update_mental_health_metrics(
        self, 
        content: Dict[str, Any], 
        decision: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> None:
        """Update mental health support metrics for performance tracking."""
        try:
            self.mental_health_metrics['total_content_analyzed'] += 1
            
            # Track crisis interventions
            if decision.get('crisis_intervention', False):
                self.mental_health_metrics['crisis_interventions'] += 1
            
            # Track mental health support provided
            if decision.get('mental_health_support', False):
                self.mental_health_metrics['mental_health_support_provided'] += 1
            
            # Track resources shared
            if 'support_resources' in decision:
                self.mental_health_metrics['resources_shared'] += 1
            
            # Track wellness promotion
            if decision.get('wellness_opportunity', False):
                self.mental_health_metrics['wellness_promotion'] += 1
            
            # Track stigma reduction efforts
            if decision.get('stigma_education', False):
                self.mental_health_metrics['stigma_reduction_efforts'] += 1
            
        except Exception as e:
            logger.error(f"Failed to update mental health metrics: {str(e)}")