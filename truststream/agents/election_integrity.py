# Election Integrity Agent for TrustStream v4.4
# Specialized agent for monitoring and protecting democratic processes and voting integrity

import logging
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import re

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class ElectionIntegrityAgent(BaseAIAgent):
    """
    Election Integrity Agent - Specialized Democratic Process Protection
    
    This agent focuses on protecting the integrity of democratic processes,
    elections, and voting systems within communities. It monitors for
    manipulation attempts, misinformation campaigns, and ensures fair
    and transparent democratic participation.
    
    Key Responsibilities:
    - Election manipulation detection
    - Voting integrity monitoring
    - Democratic process protection
    - Misinformation campaign identification
    - Vote buying/coercion detection
    - Transparency enforcement
    - Fair participation ensuring
    - Electoral fraud prevention
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Election integrity configuration
        self.integrity_config = {
            'manipulation_types': [
                'vote_buying', 'voter_intimidation', 'ballot_stuffing',
                'misinformation_campaigns', 'astroturfing', 'sock_puppeting',
                'coordinated_inauthentic_behavior', 'electoral_fraud'
            ],
            'democratic_indicators': [
                'voting_patterns', 'participation_rates', 'discussion_quality',
                'information_diversity', 'candidate_representation', 'process_transparency'
            ],
            'protection_measures': [
                'identity_verification', 'vote_secrecy', 'audit_trails',
                'transparency_reporting', 'fair_access', 'equal_representation'
            ],
            'threat_levels': {
                'critical': 0.9,  # Immediate threat to election integrity
                'high': 0.7,      # Significant manipulation attempt
                'medium': 0.5,    # Suspicious activity requiring monitoring
                'low': 0.3        # Minor concerns or potential issues
            }
        }
        
        # Election monitoring thresholds
        self.integrity_thresholds = {
            'manipulation_detection': 0.7,
            'misinformation_campaign': 0.8,
            'coordinated_behavior': 0.6,
            'voting_anomaly': 0.75,
            'transparency_violation': 0.65
        }
        
        # Democratic process patterns
        self.democratic_patterns = {
            'normal_voting_patterns': {},
            'legitimate_campaigns': {},
            'healthy_debate_indicators': {},
            'suspicious_activities': {}
        }
        
        # Election integrity metrics
        self.integrity_metrics = {
            'total_elections_monitored': 0,
            'manipulation_attempts_detected': 0,
            'misinformation_campaigns_stopped': 0,
            'voting_anomalies_flagged': 0,
            'transparency_violations_reported': 0,
            'democratic_processes_protected': 0
        }
        
        logger.info(f"Election Integrity Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content with focus on election integrity and democratic process protection.
        
        The Election Integrity Agent evaluates:
        - Election manipulation attempts
        - Voting system integrity
        - Democratic process fairness
        - Misinformation campaigns
        - Coordinated inauthentic behavior
        - Transparency violations
        - Electoral fraud indicators
        - Democratic participation quality
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Analyze election manipulation attempts
            manipulation_analysis = await self._analyze_election_manipulation(content, context)
            
            # Detect voting system integrity issues
            voting_integrity = await self._assess_voting_integrity(content, context)
            
            # Evaluate democratic process fairness
            process_fairness = await self._evaluate_process_fairness(content, context)
            
            # Identify misinformation campaigns
            misinformation_campaigns = await self._identify_misinformation_campaigns(content, context)
            
            # Detect coordinated inauthentic behavior
            coordinated_behavior = await self._detect_coordinated_behavior(content, context)
            
            # Check transparency violations
            transparency_violations = await self._check_transparency_violations(content, context)
            
            # Analyze electoral fraud indicators
            fraud_indicators = await self._analyze_fraud_indicators(content, context)
            
            # Get AI provider analysis for election integrity
            ai_analysis = await self._get_ai_integrity_analysis(content, trust_score, context)
            
            # Make election integrity decision
            decision = await self._make_integrity_decision(
                content=content,
                trust_score=trust_score,
                manipulation_analysis=manipulation_analysis,
                voting_integrity=voting_integrity,
                process_fairness=process_fairness,
                misinformation_campaigns=misinformation_campaigns,
                coordinated_behavior=coordinated_behavior,
                transparency_violations=transparency_violations,
                fraud_indicators=fraud_indicators,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Update integrity metrics
            await self._update_integrity_metrics(content, decision, context)
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Election integrity analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Election integrity analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'election_integrity', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Election Integrity Agent."""
        return [
            'election_manipulation_detection',
            'voting_integrity_monitoring',
            'democratic_process_protection',
            'misinformation_campaign_identification',
            'coordinated_behavior_detection',
            'transparency_enforcement',
            'electoral_fraud_prevention',
            'fair_participation_ensuring',
            'vote_buying_detection',
            'voter_intimidation_prevention'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Election Integrity Agent."""
        return (
            "Specialized agent for protecting democratic processes and election integrity. "
            "Monitors for manipulation attempts, ensures voting system fairness, detects "
            "misinformation campaigns, and maintains transparency in democratic participation."
        )
    
    # Private analysis methods
    
    async def _analyze_election_manipulation(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for election manipulation attempts."""
        try:
            manipulation_analysis = {
                'manipulation_risk_score': 0.0,
                'manipulation_types': [],
                'manipulation_indicators': [],
                'severity_level': 'low',
                'immediate_threats': []
            }
            
            content_text = content.get('content', '')
            author_id = content.get('author_id', '')
            
            # Check for vote buying indicators
            vote_buying_indicators = [
                'pay for vote', 'money for vote', 'reward for voting',
                'payment if you vote', 'cash for ballot', 'buy your vote'
            ]
            
            vote_buying_score = sum(1 for indicator in vote_buying_indicators 
                                  if indicator in content_text.lower())
            
            if vote_buying_score > 0:
                manipulation_analysis['manipulation_types'].append('vote_buying')
                manipulation_analysis['manipulation_indicators'].append('vote_buying_language')
                manipulation_analysis['manipulation_risk_score'] += 0.4
                manipulation_analysis['immediate_threats'].append('vote_buying_attempt')
            
            # Check for voter intimidation
            intimidation_indicators = [
                'vote or else', 'consequences if you don\'t vote', 'we\'ll know how you voted',
                'punishment for voting', 'retaliation', 'threat', 'intimidate'
            ]
            
            intimidation_score = sum(1 for indicator in intimidation_indicators 
                                   if indicator in content_text.lower())
            
            if intimidation_score > 0:
                manipulation_analysis['manipulation_types'].append('voter_intimidation')
                manipulation_analysis['manipulation_indicators'].append('intimidation_language')
                manipulation_analysis['manipulation_risk_score'] += 0.5
                manipulation_analysis['immediate_threats'].append('voter_intimidation')
            
            # Check for ballot stuffing coordination
            ballot_stuffing_indicators = [
                'multiple votes', 'vote multiple times', 'extra ballots',
                'duplicate voting', 'vote again', 'second vote'
            ]
            
            ballot_stuffing_score = sum(1 for indicator in ballot_stuffing_indicators 
                                      if indicator in content_text.lower())
            
            if ballot_stuffing_score > 0:
                manipulation_analysis['manipulation_types'].append('ballot_stuffing')
                manipulation_analysis['manipulation_indicators'].append('ballot_stuffing_coordination')
                manipulation_analysis['manipulation_risk_score'] += 0.6
                manipulation_analysis['immediate_threats'].append('ballot_stuffing_attempt')
            
            # Check for astroturfing indicators
            astroturfing_indicators = [
                'grassroots campaign', 'organic support', 'natural movement',
                'spontaneous support', 'real people', 'authentic voices'
            ]
            
            # Paradoxically, explicit claims of authenticity can indicate astroturfing
            astroturfing_score = sum(1 for indicator in astroturfing_indicators 
                                   if indicator in content_text.lower())
            
            # Check for coordinated messaging patterns
            if await self._detect_coordinated_messaging(content, context):
                manipulation_analysis['manipulation_types'].append('astroturfing')
                manipulation_analysis['manipulation_indicators'].append('coordinated_messaging')
                manipulation_analysis['manipulation_risk_score'] += 0.3
            
            # Check for sock puppet indicators
            sock_puppet_risk = await self._assess_sock_puppet_risk(content, context)
            if sock_puppet_risk > 0.5:
                manipulation_analysis['manipulation_types'].append('sock_puppeting')
                manipulation_analysis['manipulation_indicators'].append('sock_puppet_behavior')
                manipulation_analysis['manipulation_risk_score'] += sock_puppet_risk * 0.4
            
            # Determine severity level
            if manipulation_analysis['manipulation_risk_score'] >= self.integrity_config['threat_levels']['critical']:
                manipulation_analysis['severity_level'] = 'critical'
            elif manipulation_analysis['manipulation_risk_score'] >= self.integrity_config['threat_levels']['high']:
                manipulation_analysis['severity_level'] = 'high'
            elif manipulation_analysis['manipulation_risk_score'] >= self.integrity_config['threat_levels']['medium']:
                manipulation_analysis['severity_level'] = 'medium'
            
            return manipulation_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze election manipulation: {str(e)}")
            return {'manipulation_risk_score': 0.5, 'error': str(e)}
    
    async def _assess_voting_integrity(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess voting system integrity and fairness."""
        try:
            integrity_assessment = {
                'integrity_score': 1.0,  # Start with perfect integrity
                'integrity_violations': [],
                'voting_anomalies': [],
                'system_vulnerabilities': [],
                'transparency_issues': []
            }
            
            content_text = content.get('content', '')
            
            # Check for voting system manipulation
            system_manipulation_indicators = [
                'hack the vote', 'manipulate results', 'change votes',
                'alter ballots', 'system vulnerability', 'exploit voting'
            ]
            
            system_manipulation_count = sum(1 for indicator in system_manipulation_indicators 
                                          if indicator in content_text.lower())
            
            if system_manipulation_count > 0:
                integrity_assessment['integrity_violations'].append('system_manipulation_discussion')
                integrity_assessment['integrity_score'] -= 0.3
            
            # Check for vote secrecy violations
            secrecy_violations = [
                'show your ballot', 'prove how you voted', 'take photo of vote',
                'verify your choice', 'demonstrate vote', 'ballot selfie'
            ]
            
            secrecy_violation_count = sum(1 for violation in secrecy_violations 
                                        if violation in content_text.lower())
            
            if secrecy_violation_count > 0:
                integrity_assessment['integrity_violations'].append('vote_secrecy_violation')
                integrity_assessment['integrity_score'] -= 0.4
            
            # Check for voting process interference
            interference_indicators = [
                'disrupt voting', 'prevent voting', 'block access',
                'interfere with election', 'stop the vote', 'election interference'
            ]
            
            interference_count = sum(1 for indicator in interference_indicators 
                                   if indicator in content_text.lower())
            
            if interference_count > 0:
                integrity_assessment['integrity_violations'].append('voting_process_interference')
                integrity_assessment['integrity_score'] -= 0.5
            
            # Check for unusual voting patterns discussion
            if await self._detect_voting_anomaly_discussion(content, context):
                integrity_assessment['voting_anomalies'].append('anomaly_discussion_detected')
                integrity_assessment['integrity_score'] -= 0.2
            
            # Check for transparency issues
            transparency_problems = [
                'hidden votes', 'secret counting', 'private results',
                'no audit trail', 'unverifiable', 'opaque process'
            ]
            
            transparency_issue_count = sum(1 for problem in transparency_problems 
                                         if problem in content_text.lower())
            
            if transparency_issue_count > 0:
                integrity_assessment['transparency_issues'].append('transparency_concerns')
                integrity_assessment['integrity_score'] -= 0.3
            
            # Ensure score doesn't go below 0
            integrity_assessment['integrity_score'] = max(0.0, integrity_assessment['integrity_score'])
            
            return integrity_assessment
            
        except Exception as e:
            logger.error(f"Failed to assess voting integrity: {str(e)}")
            return {'integrity_score': 0.5, 'error': str(e)}
    
    async def _evaluate_process_fairness(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate the fairness of democratic processes."""
        try:
            fairness_evaluation = {
                'fairness_score': 0.8,  # Start with good fairness assumption
                'fairness_violations': [],
                'bias_indicators': [],
                'access_issues': [],
                'representation_problems': []
            }
            
            content_text = content.get('content', '')
            
            # Check for unfair advantage attempts
            unfair_advantage_indicators = [
                'special access', 'exclusive information', 'insider knowledge',
                'privileged position', 'unfair advantage', 'rigged system'
            ]
            
            unfair_advantage_count = sum(1 for indicator in unfair_advantage_indicators 
                                       if indicator in content_text.lower())
            
            if unfair_advantage_count > 0:
                fairness_evaluation['fairness_violations'].append('unfair_advantage_seeking')
                fairness_evaluation['fairness_score'] -= 0.3
            
            # Check for discriminatory practices
            discrimination_indicators = [
                'exclude voters', 'prevent participation', 'discriminate against',
                'block access', 'unfair requirements', 'biased rules'
            ]
            
            discrimination_count = sum(1 for indicator in discrimination_indicators 
                                     if indicator in content_text.lower())
            
            if discrimination_count > 0:
                fairness_evaluation['fairness_violations'].append('discriminatory_practices')
                fairness_evaluation['fairness_score'] -= 0.4
            
            # Check for access barriers
            access_barrier_indicators = [
                'difficult to vote', 'hard to participate', 'complex process',
                'barriers to entry', 'restricted access', 'limited availability'
            ]
            
            access_barrier_count = sum(1 for indicator in access_barrier_indicators 
                                     if indicator in content_text.lower())
            
            if access_barrier_count > 0:
                fairness_evaluation['access_issues'].append('participation_barriers')
                fairness_evaluation['fairness_score'] -= 0.2
            
            # Check for representation issues
            representation_indicators = [
                'underrepresented', 'lack of diversity', 'biased selection',
                'unequal representation', 'skewed demographics', 'missing voices'
            ]
            
            representation_count = sum(1 for indicator in representation_indicators 
                                     if indicator in content_text.lower())
            
            if representation_count > 0:
                fairness_evaluation['representation_problems'].append('representation_concerns')
                fairness_evaluation['fairness_score'] -= 0.25
            
            # Check for positive fairness indicators
            positive_fairness_indicators = [
                'equal opportunity', 'fair process', 'transparent system',
                'inclusive participation', 'equal access', 'unbiased'
            ]
            
            positive_fairness_count = sum(1 for indicator in positive_fairness_indicators 
                                        if indicator in content_text.lower())
            
            if positive_fairness_count > 0:
                fairness_evaluation['fairness_score'] += 0.1
            
            # Ensure score stays within bounds
            fairness_evaluation['fairness_score'] = max(0.0, min(1.0, fairness_evaluation['fairness_score']))
            
            return fairness_evaluation
            
        except Exception as e:
            logger.error(f"Failed to evaluate process fairness: {str(e)}")
            return {'fairness_score': 0.5, 'error': str(e)}
    
    async def _identify_misinformation_campaigns(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify coordinated misinformation campaigns."""
        try:
            campaign_analysis = {
                'campaign_risk_score': 0.0,
                'campaign_indicators': [],
                'misinformation_types': [],
                'coordination_evidence': [],
                'target_analysis': {}
            }
            
            content_text = content.get('content', '')
            
            # Check for election-specific misinformation
            election_misinfo_indicators = [
                'voting machines rigged', 'fake ballots', 'dead people voting',
                'election stolen', 'fraudulent votes', 'illegal voting'
            ]
            
            election_misinfo_count = sum(1 for indicator in election_misinfo_indicators 
                                       if indicator in content_text.lower())
            
            if election_misinfo_count > 0:
                campaign_analysis['misinformation_types'].append('election_fraud_claims')
                campaign_analysis['campaign_risk_score'] += 0.4
            
            # Check for voter suppression misinformation
            suppression_misinfo_indicators = [
                'wrong voting date', 'fake polling location', 'false requirements',
                'incorrect voting method', 'misleading instructions', 'vote by text'
            ]
            
            suppression_misinfo_count = sum(1 for indicator in suppression_misinfo_indicators 
                                          if indicator in content_text.lower())
            
            if suppression_misinfo_count > 0:
                campaign_analysis['misinformation_types'].append('voter_suppression')
                campaign_analysis['campaign_risk_score'] += 0.5
            
            # Check for candidate misinformation
            candidate_misinfo_indicators = [
                'false claims about', 'fabricated scandal', 'fake news about',
                'misleading information', 'doctored evidence', 'false accusations'
            ]
            
            candidate_misinfo_count = sum(1 for indicator in candidate_misinfo_indicators 
                                        if indicator in content_text.lower())
            
            if candidate_misinfo_count > 0:
                campaign_analysis['misinformation_types'].append('candidate_defamation')
                campaign_analysis['campaign_risk_score'] += 0.3
            
            # Check for coordinated messaging patterns
            if await self._detect_coordinated_messaging(content, context):
                campaign_analysis['coordination_evidence'].append('coordinated_messaging_detected')
                campaign_analysis['campaign_risk_score'] += 0.3
            
            # Check for bot-like behavior
            bot_indicators = await self._assess_bot_behavior(content, context)
            if bot_indicators['bot_likelihood'] > 0.7:
                campaign_analysis['coordination_evidence'].append('bot_behavior_detected')
                campaign_analysis['campaign_risk_score'] += 0.4
            
            # Analyze targeting patterns
            campaign_analysis['target_analysis'] = await self._analyze_targeting_patterns(content, context)
            
            return campaign_analysis
            
        except Exception as e:
            logger.error(f"Failed to identify misinformation campaigns: {str(e)}")
            return {'campaign_risk_score': 0.5, 'error': str(e)}
    
    async def _detect_coordinated_behavior(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect coordinated inauthentic behavior."""
        try:
            coordination_analysis = {
                'coordination_score': 0.0,
                'coordination_indicators': [],
                'behavior_patterns': [],
                'network_analysis': {},
                'authenticity_score': 1.0
            }
            
            # Check for coordinated timing
            timing_coordination = await self._analyze_timing_coordination(content, context)
            if timing_coordination['is_coordinated']:
                coordination_analysis['coordination_indicators'].append('coordinated_timing')
                coordination_analysis['coordination_score'] += 0.3
            
            # Check for identical or near-identical messaging
            message_similarity = await self._analyze_message_similarity(content, context)
            if message_similarity['similarity_score'] > 0.8:
                coordination_analysis['coordination_indicators'].append('identical_messaging')
                coordination_analysis['coordination_score'] += 0.4
            
            # Check for coordinated account behavior
            account_coordination = await self._analyze_account_coordination(content, context)
            coordination_analysis['network_analysis'] = account_coordination
            
            if account_coordination.get('coordination_likelihood', 0.0) > 0.6:
                coordination_analysis['coordination_indicators'].append('coordinated_accounts')
                coordination_analysis['coordination_score'] += 0.5
            
            # Check for artificial amplification
            amplification_patterns = await self._detect_artificial_amplification(content, context)
            if amplification_patterns['is_artificial']:
                coordination_analysis['coordination_indicators'].append('artificial_amplification')
                coordination_analysis['coordination_score'] += 0.3
            
            # Calculate authenticity score
            coordination_analysis['authenticity_score'] = max(0.0, 1.0 - coordination_analysis['coordination_score'])
            
            return coordination_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect coordinated behavior: {str(e)}")
            return {'coordination_score': 0.5, 'error': str(e)}
    
    async def _check_transparency_violations(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for transparency violations in democratic processes."""
        try:
            transparency_analysis = {
                'transparency_score': 1.0,
                'violations': [],
                'opacity_indicators': [],
                'disclosure_issues': []
            }
            
            content_text = content.get('content', '')
            
            # Check for hidden funding/sponsorship
            hidden_funding_indicators = [
                'anonymous donation', 'undisclosed funding', 'secret sponsor',
                'hidden backer', 'mysterious funding', 'unknown source'
            ]
            
            hidden_funding_count = sum(1 for indicator in hidden_funding_indicators 
                                     if indicator in content_text.lower())
            
            if hidden_funding_count > 0:
                transparency_analysis['violations'].append('hidden_funding')
                transparency_analysis['transparency_score'] -= 0.4
            
            # Check for lack of disclosure
            disclosure_issues = [
                'no disclosure', 'undisclosed interest', 'hidden agenda',
                'secret purpose', 'concealed motive', 'undeclared bias'
            ]
            
            disclosure_issue_count = sum(1 for issue in disclosure_issues 
                                       if issue in content_text.lower())
            
            if disclosure_issue_count > 0:
                transparency_analysis['disclosure_issues'].append('lack_of_disclosure')
                transparency_analysis['transparency_score'] -= 0.3
            
            # Check for opacity in processes
            opacity_indicators = [
                'closed process', 'private meeting', 'secret decision',
                'behind closed doors', 'no public access', 'confidential voting'
            ]
            
            opacity_count = sum(1 for indicator in opacity_indicators 
                              if indicator in content_text.lower())
            
            if opacity_count > 0:
                transparency_analysis['opacity_indicators'].append('process_opacity')
                transparency_analysis['transparency_score'] -= 0.35
            
            # Check for positive transparency indicators
            positive_transparency = [
                'full disclosure', 'transparent process', 'open voting',
                'public record', 'clear documentation', 'audit trail'
            ]
            
            positive_transparency_count = sum(1 for indicator in positive_transparency 
                                            if indicator in content_text.lower())
            
            if positive_transparency_count > 0:
                transparency_analysis['transparency_score'] += 0.1
            
            # Ensure score stays within bounds
            transparency_analysis['transparency_score'] = max(0.0, min(1.0, transparency_analysis['transparency_score']))
            
            return transparency_analysis
            
        except Exception as e:
            logger.error(f"Failed to check transparency violations: {str(e)}")
            return {'transparency_score': 0.5, 'error': str(e)}
    
    async def _analyze_fraud_indicators(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze indicators of electoral fraud."""
        try:
            fraud_analysis = {
                'fraud_risk_score': 0.0,
                'fraud_types': [],
                'evidence_indicators': [],
                'statistical_anomalies': [],
                'procedural_violations': []
            }
            
            content_text = content.get('content', '')
            
            # Check for registration fraud
            registration_fraud_indicators = [
                'fake registration', 'false identity', 'duplicate registration',
                'ineligible voter', 'fraudulent signup', 'identity theft'
            ]
            
            registration_fraud_count = sum(1 for indicator in registration_fraud_indicators 
                                         if indicator in content_text.lower())
            
            if registration_fraud_count > 0:
                fraud_analysis['fraud_types'].append('registration_fraud')
                fraud_analysis['fraud_risk_score'] += 0.4
            
            # Check for counting fraud
            counting_fraud_indicators = [
                'miscounted votes', 'altered results', 'fake tallies',
                'manipulated count', 'fraudulent counting', 'changed numbers'
            ]
            
            counting_fraud_count = sum(1 for indicator in counting_fraud_indicators 
                                     if indicator in content_text.lower())
            
            if counting_fraud_count > 0:
                fraud_analysis['fraud_types'].append('counting_fraud')
                fraud_analysis['fraud_risk_score'] += 0.5
            
            # Check for procedural violations
            procedural_violations = [
                'violated procedure', 'ignored rules', 'bypassed protocol',
                'unauthorized access', 'improper handling', 'rule violation'
            ]
            
            procedural_violation_count = sum(1 for violation in procedural_violations 
                                           if violation in content_text.lower())
            
            if procedural_violation_count > 0:
                fraud_analysis['procedural_violations'].append('protocol_violations')
                fraud_analysis['fraud_risk_score'] += 0.3
            
            # Check for statistical anomaly discussions
            statistical_anomalies = [
                'impossible numbers', 'statistical impossibility', 'anomalous results',
                'suspicious patterns', 'unlikely outcome', 'mathematical impossibility'
            ]
            
            statistical_anomaly_count = sum(1 for anomaly in statistical_anomalies 
                                          if anomaly in content_text.lower())
            
            if statistical_anomaly_count > 0:
                fraud_analysis['statistical_anomalies'].append('anomaly_discussion')
                fraud_analysis['fraud_risk_score'] += 0.35
            
            return fraud_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze fraud indicators: {str(e)}")
            return {'fraud_risk_score': 0.5, 'error': str(e)}
    
    async def _get_ai_integrity_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on election integrity."""
        try:
            prompt = self._create_integrity_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (Claude for election integrity analysis)
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
                'reasoning': 'No AI providers available for election integrity analysis'
            }
            
        except Exception as e:
            logger.error(f"AI election integrity analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_integrity_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create an election integrity focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='election integrity, democratic processes, and voting system protection'
        )
        
        integrity_specific = f"""
ELECTION INTEGRITY ANALYSIS

You are a specialized Election Integrity Agent focused on protecting democratic
processes, ensuring voting system integrity, and preventing electoral manipulation.

User Trust Context:
- Author Trust Score: {trust_score}

Election Integrity Framework:
1. Manipulation Detection: Identify attempts to manipulate elections or voting
2. Voting System Protection: Ensure integrity of voting processes and systems
3. Democratic Process Fairness: Maintain fair and equal democratic participation
4. Misinformation Prevention: Stop false information about elections and voting
5. Transparency Enforcement: Ensure open and transparent democratic processes
6. Fraud Prevention: Detect and prevent electoral fraud and irregularities

Critical Threats to Monitor:
- Vote buying and voter intimidation
- Ballot stuffing and duplicate voting
- Misinformation campaigns about voting
- Coordinated inauthentic behavior
- Voting system manipulation attempts
- Transparency violations and hidden agendas
- Electoral fraud and procedural violations
- Voter suppression tactics

Decision Guidelines:
- BLOCK: Direct threats to election integrity (vote buying, intimidation, fraud)
- FLAG: Suspicious activities requiring investigation (coordinated behavior, anomalies)
- MONITOR: Potential concerns needing ongoing observation (misinformation, bias)
- APPROVE: Legitimate democratic discourse and participation

Protection Priorities:
- Maintain voting system integrity and security
- Ensure fair and equal access to democratic processes
- Protect voter privacy and ballot secrecy
- Prevent manipulation and coercion
- Promote transparency and accountability
- Support legitimate democratic participation

CRITICAL: Any content that directly threatens election integrity, promotes voter
manipulation, or undermines democratic processes must be immediately flagged or blocked.
"""
        
        return base_prompt + integrity_specific
    
    # Helper methods for election integrity analysis
    
    async def _detect_coordinated_messaging(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> bool:
        """Detect coordinated messaging patterns."""
        # Simplified coordinated messaging detection
        # In practice, this would analyze message similarity across multiple accounts
        content_text = content.get('content', '')
        
        # Check for template-like language
        template_indicators = [
            'copy and paste', 'share this message', 'spread the word',
            'repost this', 'forward this', 'identical message'
        ]
        
        template_count = sum(1 for indicator in template_indicators 
                           if indicator in content_text.lower())
        
        return template_count > 0
    
    async def _assess_sock_puppet_risk(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """Assess the risk of sock puppet behavior."""
        # Simplified sock puppet risk assessment
        # In practice, this would analyze account patterns, behavior, and network connections
        
        risk_score = 0.0
        author_id = content.get('author_id', '')
        
        # Check for new account with strong political opinions
        account_age = context.get('author_account_age_days', 365)
        if account_age < 30:
            risk_score += 0.3
        
        # Check for limited posting history
        post_count = context.get('author_post_count', 100)
        if post_count < 10:
            risk_score += 0.2
        
        # Check for single-issue focus
        if context.get('author_topic_diversity', 1.0) < 0.3:
            risk_score += 0.3
        
        return min(1.0, risk_score)
    
    async def _detect_voting_anomaly_discussion(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> bool:
        """Detect discussion of voting anomalies."""
        content_text = content.get('content', '')
        
        anomaly_indicators = [
            'voting anomaly', 'unusual pattern', 'suspicious results',
            'irregular voting', 'abnormal turnout', 'statistical impossibility'
        ]
        
        anomaly_count = sum(1 for indicator in anomaly_indicators 
                          if indicator in content_text.lower())
        
        return anomaly_count > 0
    
    async def _assess_bot_behavior(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess likelihood of bot behavior."""
        bot_analysis = {
            'bot_likelihood': 0.0,
            'bot_indicators': []
        }
        
        # Check posting frequency
        posts_per_hour = context.get('author_posts_per_hour', 1.0)
        if posts_per_hour > 10:
            bot_analysis['bot_indicators'].append('high_posting_frequency')
            bot_analysis['bot_likelihood'] += 0.3
        
        # Check for repetitive content
        content_similarity = context.get('author_content_similarity', 0.0)
        if content_similarity > 0.8:
            bot_analysis['bot_indicators'].append('repetitive_content')
            bot_analysis['bot_likelihood'] += 0.4
        
        # Check for automated timing patterns
        if context.get('author_has_automated_timing', False):
            bot_analysis['bot_indicators'].append('automated_timing')
            bot_analysis['bot_likelihood'] += 0.3
        
        return bot_analysis
    
    async def _analyze_targeting_patterns(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze targeting patterns in content."""
        targeting_analysis = {
            'is_targeted': False,
            'target_demographics': [],
            'targeting_methods': []
        }
        
        content_text = content.get('content', '')
        
        # Check for demographic targeting
        demographic_targets = [
            'young voters', 'elderly voters', 'minority voters',
            'rural voters', 'urban voters', 'suburban voters'
        ]
        
        for target in demographic_targets:
            if target in content_text.lower():
                targeting_analysis['target_demographics'].append(target)
                targeting_analysis['is_targeted'] = True
        
        # Check for geographic targeting
        geographic_indicators = [
            'voters in', 'residents of', 'people from',
            'citizens of', 'locals in', 'community in'
        ]
        
        geographic_count = sum(1 for indicator in geographic_indicators 
                             if indicator in content_text.lower())
        
        if geographic_count > 0:
            targeting_analysis['targeting_methods'].append('geographic_targeting')
            targeting_analysis['is_targeted'] = True
        
        return targeting_analysis
    
    async def _analyze_timing_coordination(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze timing coordination patterns."""
        # Simplified timing coordination analysis
        # In practice, this would analyze posting times across multiple accounts
        
        coordination_analysis = {
            'is_coordinated': False,
            'coordination_indicators': []
        }
        
        # Check for suspicious timing patterns
        if context.get('simultaneous_posts_detected', False):
            coordination_analysis['is_coordinated'] = True
            coordination_analysis['coordination_indicators'].append('simultaneous_posting')
        
        return coordination_analysis
    
    async def _analyze_message_similarity(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze message similarity for coordination detection."""
        # Simplified message similarity analysis
        # In practice, this would use advanced text similarity algorithms
        
        similarity_analysis = {
            'similarity_score': 0.0,
            'similar_messages_found': False
        }
        
        # Check for identical phrases in recent content
        if context.get('identical_phrases_detected', False):
            similarity_analysis['similarity_score'] = 0.9
            similarity_analysis['similar_messages_found'] = True
        
        return similarity_analysis
    
    async def _analyze_account_coordination(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze account coordination patterns."""
        # Simplified account coordination analysis
        # In practice, this would analyze network connections and behavior patterns
        
        coordination_analysis = {
            'coordination_likelihood': 0.0,
            'coordination_indicators': []
        }
        
        # Check for coordinated account creation
        if context.get('coordinated_account_creation', False):
            coordination_analysis['coordination_likelihood'] += 0.4
            coordination_analysis['coordination_indicators'].append('coordinated_creation')
        
        # Check for similar posting patterns
        if context.get('similar_posting_patterns', False):
            coordination_analysis['coordination_likelihood'] += 0.3
            coordination_analysis['coordination_indicators'].append('similar_patterns')
        
        return coordination_analysis
    
    async def _detect_artificial_amplification(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect artificial amplification patterns."""
        amplification_analysis = {
            'is_artificial': False,
            'amplification_indicators': []
        }
        
        # Check for suspicious engagement patterns
        if context.get('suspicious_engagement_spike', False):
            amplification_analysis['is_artificial'] = True
            amplification_analysis['amplification_indicators'].append('engagement_spike')
        
        # Check for bot amplification
        if context.get('bot_amplification_detected', False):
            amplification_analysis['is_artificial'] = True
            amplification_analysis['amplification_indicators'].append('bot_amplification')
        
        return amplification_analysis
    
    async def _make_integrity_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        manipulation_analysis: Dict[str, Any],
        voting_integrity: Dict[str, Any],
        process_fairness: Dict[str, Any],
        misinformation_campaigns: Dict[str, Any],
        coordinated_behavior: Dict[str, Any],
        transparency_violations: Dict[str, Any],
        fraud_indicators: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make election integrity focused moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Calculate overall integrity threat score
            threat_scores = [
                manipulation_analysis.get('manipulation_risk_score', 0.0),
                1.0 - voting_integrity.get('integrity_score', 1.0),
                1.0 - process_fairness.get('fairness_score', 0.8),
                misinformation_campaigns.get('campaign_risk_score', 0.0),
                coordinated_behavior.get('coordination_score', 0.0),
                1.0 - transparency_violations.get('transparency_score', 1.0),
                fraud_indicators.get('fraud_risk_score', 0.0)
            ]
            
            overall_threat_score = max(threat_scores)  # Use highest threat
            
            # Make decision based on threat level
            if overall_threat_score >= self.integrity_config['threat_levels']['critical']:
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'Critical threat to election integrity detected'
                base_decision['priority'] = 'critical'
                
            elif overall_threat_score >= self.integrity_config['threat_levels']['high']:
                if base_decision['action'] == 'approve':
                    base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'High risk to election integrity - requires investigation'
                base_decision['priority'] = 'high'
                
            elif overall_threat_score >= self.integrity_config['threat_levels']['medium']:
                base_decision['monitoring_required'] = True
                base_decision['priority'] = 'medium'
                
            # Handle specific immediate threats
            immediate_threats = manipulation_analysis.get('immediate_threats', [])
            if immediate_threats:
                base_decision['action'] = 'block'
                base_decision['reasoning'] = f'Immediate election integrity threats: {", ".join(immediate_threats)}'
                base_decision['immediate_action_required'] = True
            
            # Add integrity-specific metadata
            base_decision['metadata'] = base_decision.get('metadata', {})
            base_decision['metadata'].update({
                'agent': 'election_integrity',
                'overall_threat_score': round(overall_threat_score, 3),
                'manipulation_risk': round(manipulation_analysis.get('manipulation_risk_score', 0.0), 3),
                'voting_integrity': round(voting_integrity.get('integrity_score', 1.0), 3),
                'process_fairness': round(process_fairness.get('fairness_score', 0.8), 3),
                'misinformation_risk': round(misinformation_campaigns.get('campaign_risk_score', 0.0), 3),
                'coordination_detected': coordinated_behavior.get('coordination_score', 0.0) > 0.5,
                'transparency_score': round(transparency_violations.get('transparency_score', 1.0), 3),
                'fraud_risk': round(fraud_indicators.get('fraud_risk_score', 0.0), 3)
            })
            
            # Add detailed evidence
            base_decision['evidence'] = base_decision.get('evidence', {})
            base_decision['evidence'].update({
                'manipulation_analysis': manipulation_analysis,
                'voting_integrity': voting_integrity,
                'process_fairness': process_fairness,
                'misinformation_campaigns': misinformation_campaigns,
                'coordinated_behavior': coordinated_behavior,
                'transparency_violations': transparency_violations,
                'fraud_indicators': fraud_indicators
            })
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make election integrity decision: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Election integrity decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'election_integrity', 'error': True}
            }
    
    async def _update_integrity_metrics(
        self, 
        content: Dict[str, Any], 
        decision: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> None:
        """Update election integrity metrics for performance tracking."""
        try:
            self.integrity_metrics['total_elections_monitored'] += 1
            
            # Track manipulation attempts
            if decision.get('metadata', {}).get('manipulation_risk', 0.0) > 0.5:
                self.integrity_metrics['manipulation_attempts_detected'] += 1
            
            # Track misinformation campaigns
            if decision.get('metadata', {}).get('misinformation_risk', 0.0) > 0.5:
                self.integrity_metrics['misinformation_campaigns_stopped'] += 1
            
            # Track voting anomalies
            if decision.get('metadata', {}).get('voting_integrity', 1.0) < 0.5:
                self.integrity_metrics['voting_anomalies_flagged'] += 1
            
            # Track transparency violations
            if decision.get('metadata', {}).get('transparency_score', 1.0) < 0.5:
                self.integrity_metrics['transparency_violations_reported'] += 1
            
            # Track protected processes
            if decision.get('action') in ['approve', 'promote']:
                self.integrity_metrics['democratic_processes_protected'] += 1
            
        except Exception as e:
            logger.error(f"Failed to update integrity metrics: {str(e)}")