# Privacy Protection Agent for TrustStream v4.4
# Specialized agent for protecting user privacy and ensuring data protection compliance

import logging
import json
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class PrivacyProtectionAgent(BaseAIAgent):
    """
    Privacy Protection Agent - Specialized Data Privacy and Protection
    
    This agent focuses on protecting user privacy, ensuring compliance with
    data protection regulations (GDPR, CCPA, etc.), and preventing privacy
    violations in community interactions and content.
    
    Key Responsibilities:
    - Personal information detection and protection
    - Data privacy compliance monitoring
    - Privacy violation prevention
    - Consent management oversight
    - Data minimization enforcement
    - Privacy rights protection
    - Anonymization and pseudonymization
    - Cross-border data transfer compliance
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Privacy protection configuration
        self.privacy_config = {
            'personal_data_types': [
                'email_addresses', 'phone_numbers', 'physical_addresses',
                'social_security_numbers', 'credit_card_numbers', 'bank_accounts',
                'government_ids', 'biometric_data', 'health_information',
                'financial_data', 'location_data', 'ip_addresses'
            ],
            'privacy_regulations': [
                'gdpr', 'ccpa', 'pipeda', 'lgpd', 'pdpa',
                'coppa', 'ferpa', 'hipaa', 'glba'
            ],
            'privacy_principles': [
                'data_minimization', 'purpose_limitation', 'storage_limitation',
                'accuracy', 'integrity', 'confidentiality', 'accountability'
            ],
            'risk_levels': {
                'critical': 0.9,  # Severe privacy violation
                'high': 0.7,      # Significant privacy risk
                'medium': 0.5,    # Moderate privacy concern
                'low': 0.3        # Minor privacy issue
            }
        }
        
        # Privacy detection patterns
        self.privacy_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'address': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b',
            'government_id': r'\b[A-Z]{1,2}\d{6,9}\b',
            'bank_account': r'\b\d{8,17}\b'
        }
        
        # Privacy protection thresholds
        self.privacy_thresholds = {
            'personal_data_exposure': 0.8,
            'privacy_violation': 0.7,
            'consent_violation': 0.75,
            'data_misuse': 0.6,
            'regulatory_violation': 0.85
        }
        
        # Privacy protection metrics
        self.privacy_metrics = {
            'total_content_analyzed': 0,
            'personal_data_detected': 0,
            'privacy_violations_prevented': 0,
            'consent_violations_flagged': 0,
            'data_protection_actions': 0,
            'regulatory_compliance_checks': 0
        }
        
        logger.info(f"Privacy Protection Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content with focus on privacy protection and data compliance.
        
        The Privacy Protection Agent evaluates:
        - Personal information exposure
        - Data privacy violations
        - Regulatory compliance issues
        - Consent management problems
        - Data minimization violations
        - Privacy rights infringements
        - Cross-border data transfer issues
        - Anonymization requirements
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Detect personal information exposure
            personal_data_analysis = await self._detect_personal_information(content, context)
            
            # Analyze privacy violations
            privacy_violations = await self._analyze_privacy_violations(content, context)
            
            # Check regulatory compliance
            compliance_analysis = await self._check_regulatory_compliance(content, context)
            
            # Evaluate consent management
            consent_analysis = await self._evaluate_consent_management(content, context)
            
            # Assess data minimization compliance
            data_minimization = await self._assess_data_minimization(content, context)
            
            # Check privacy rights violations
            rights_violations = await self._check_privacy_rights_violations(content, context)
            
            # Analyze cross-border data transfer issues
            cross_border_analysis = await self._analyze_cross_border_transfers(content, context)
            
            # Get AI provider analysis for privacy protection
            ai_analysis = await self._get_ai_privacy_analysis(content, trust_score, context)
            
            # Make privacy protection decision
            decision = await self._make_privacy_decision(
                content=content,
                trust_score=trust_score,
                personal_data_analysis=personal_data_analysis,
                privacy_violations=privacy_violations,
                compliance_analysis=compliance_analysis,
                consent_analysis=consent_analysis,
                data_minimization=data_minimization,
                rights_violations=rights_violations,
                cross_border_analysis=cross_border_analysis,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Update privacy metrics
            await self._update_privacy_metrics(content, decision, context)
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Privacy protection analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Privacy protection analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'privacy_protection', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Privacy Protection Agent."""
        return [
            'personal_information_detection',
            'privacy_violation_prevention',
            'data_protection_compliance',
            'consent_management_oversight',
            'data_minimization_enforcement',
            'privacy_rights_protection',
            'regulatory_compliance_monitoring',
            'anonymization_enforcement',
            'cross_border_transfer_compliance',
            'privacy_impact_assessment'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Privacy Protection Agent."""
        return (
            "Specialized agent for protecting user privacy and ensuring data protection compliance. "
            "Detects personal information exposure, prevents privacy violations, monitors regulatory "
            "compliance, and enforces privacy rights and data protection principles."
        )
    
    # Private analysis methods
    
    async def _detect_personal_information(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect personal information in content."""
        try:
            personal_data_analysis = {
                'personal_data_detected': False,
                'data_types_found': [],
                'exposure_risk_score': 0.0,
                'sensitive_data_count': 0,
                'protection_required': False
            }
            
            content_text = content.get('content', '')
            
            # Check for different types of personal information
            for data_type, pattern in self.privacy_patterns.items():
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                
                if matches:
                    personal_data_analysis['personal_data_detected'] = True
                    personal_data_analysis['data_types_found'].append(data_type)
                    personal_data_analysis['sensitive_data_count'] += len(matches)
                    
                    # Calculate exposure risk based on data type sensitivity
                    if data_type in ['ssn', 'credit_card', 'bank_account']:
                        personal_data_analysis['exposure_risk_score'] += 0.4
                    elif data_type in ['email', 'phone', 'address']:
                        personal_data_analysis['exposure_risk_score'] += 0.2
                    else:
                        personal_data_analysis['exposure_risk_score'] += 0.1
            
            # Check for health information
            health_indicators = [
                'medical record', 'diagnosis', 'prescription', 'health condition',
                'medical history', 'treatment', 'medication', 'doctor visit'
            ]
            
            health_info_count = sum(1 for indicator in health_indicators 
                                  if indicator in content_text.lower())
            
            if health_info_count > 0:
                personal_data_analysis['data_types_found'].append('health_information')
                personal_data_analysis['exposure_risk_score'] += 0.3
                personal_data_analysis['sensitive_data_count'] += health_info_count
            
            # Check for financial information
            financial_indicators = [
                'bank balance', 'income', 'salary', 'financial status',
                'credit score', 'debt', 'investment', 'tax information'
            ]
            
            financial_info_count = sum(1 for indicator in financial_indicators 
                                     if indicator in content_text.lower())
            
            if financial_info_count > 0:
                personal_data_analysis['data_types_found'].append('financial_information')
                personal_data_analysis['exposure_risk_score'] += 0.25
                personal_data_analysis['sensitive_data_count'] += financial_info_count
            
            # Check for biometric data references
            biometric_indicators = [
                'fingerprint', 'facial recognition', 'iris scan', 'voice print',
                'biometric', 'dna', 'genetic information', 'retinal scan'
            ]
            
            biometric_count = sum(1 for indicator in biometric_indicators 
                                if indicator in content_text.lower())
            
            if biometric_count > 0:
                personal_data_analysis['data_types_found'].append('biometric_data')
                personal_data_analysis['exposure_risk_score'] += 0.35
                personal_data_analysis['sensitive_data_count'] += biometric_count
            
            # Determine if protection is required
            if personal_data_analysis['exposure_risk_score'] > 0.3:
                personal_data_analysis['protection_required'] = True
            
            # Cap the risk score
            personal_data_analysis['exposure_risk_score'] = min(1.0, personal_data_analysis['exposure_risk_score'])
            
            return personal_data_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect personal information: {str(e)}")
            return {'exposure_risk_score': 0.5, 'error': str(e)}
    
    async def _analyze_privacy_violations(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for privacy violations."""
        try:
            violation_analysis = {
                'violation_risk_score': 0.0,
                'violation_types': [],
                'violation_indicators': [],
                'severity_level': 'low'
            }
            
            content_text = content.get('content', '')
            
            # Check for unauthorized data sharing
            data_sharing_indicators = [
                'share personal info', 'give out details', 'provide private data',
                'leak information', 'expose data', 'unauthorized sharing'
            ]
            
            data_sharing_count = sum(1 for indicator in data_sharing_indicators 
                                   if indicator in content_text.lower())
            
            if data_sharing_count > 0:
                violation_analysis['violation_types'].append('unauthorized_data_sharing')
                violation_analysis['violation_indicators'].append('data_sharing_language')
                violation_analysis['violation_risk_score'] += 0.4
            
            # Check for privacy invasion attempts
            invasion_indicators = [
                'spy on', 'track without consent', 'monitor secretly',
                'invade privacy', 'unauthorized surveillance', 'secret recording'
            ]
            
            invasion_count = sum(1 for indicator in invasion_indicators 
                               if indicator in content_text.lower())
            
            if invasion_count > 0:
                violation_analysis['violation_types'].append('privacy_invasion')
                violation_analysis['violation_indicators'].append('invasion_language')
                violation_analysis['violation_risk_score'] += 0.5
            
            # Check for data misuse
            misuse_indicators = [
                'misuse data', 'abuse information', 'unauthorized use',
                'exploit personal info', 'inappropriate use', 'data abuse'
            ]
            
            misuse_count = sum(1 for indicator in misuse_indicators 
                             if indicator in content_text.lower())
            
            if misuse_count > 0:
                violation_analysis['violation_types'].append('data_misuse')
                violation_analysis['violation_indicators'].append('misuse_language')
                violation_analysis['violation_risk_score'] += 0.35
            
            # Check for consent violations
            consent_violation_indicators = [
                'without permission', 'no consent', 'unauthorized access',
                'against wishes', 'without approval', 'forced sharing'
            ]
            
            consent_violation_count = sum(1 for indicator in consent_violation_indicators 
                                        if indicator in content_text.lower())
            
            if consent_violation_count > 0:
                violation_analysis['violation_types'].append('consent_violation')
                violation_analysis['violation_indicators'].append('consent_violation_language')
                violation_analysis['violation_risk_score'] += 0.45
            
            # Determine severity level
            if violation_analysis['violation_risk_score'] >= self.privacy_config['risk_levels']['critical']:
                violation_analysis['severity_level'] = 'critical'
            elif violation_analysis['violation_risk_score'] >= self.privacy_config['risk_levels']['high']:
                violation_analysis['severity_level'] = 'high'
            elif violation_analysis['violation_risk_score'] >= self.privacy_config['risk_levels']['medium']:
                violation_analysis['severity_level'] = 'medium'
            
            return violation_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze privacy violations: {str(e)}")
            return {'violation_risk_score': 0.5, 'error': str(e)}
    
    async def _check_regulatory_compliance(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check content for regulatory compliance issues."""
        try:
            compliance_analysis = {
                'compliance_score': 1.0,  # Start with full compliance
                'violations': [],
                'regulatory_concerns': [],
                'jurisdiction_issues': []
            }
            
            content_text = content.get('content', '')
            
            # Check for GDPR violations
            gdpr_violations = [
                'process without consent', 'no legal basis', 'excessive data collection',
                'indefinite storage', 'no data subject rights', 'unlawful processing'
            ]
            
            gdpr_violation_count = sum(1 for violation in gdpr_violations 
                                     if violation in content_text.lower())
            
            if gdpr_violation_count > 0:
                compliance_analysis['violations'].append('gdpr_violation')
                compliance_analysis['compliance_score'] -= 0.3
            
            # Check for CCPA violations
            ccpa_violations = [
                'sell personal info', 'no opt-out', 'discriminate for privacy',
                'no disclosure', 'unauthorized sale', 'privacy discrimination'
            ]
            
            ccpa_violation_count = sum(1 for violation in ccpa_violations 
                                     if violation in content_text.lower())
            
            if ccpa_violation_count > 0:
                compliance_analysis['violations'].append('ccpa_violation')
                compliance_analysis['compliance_score'] -= 0.25
            
            # Check for COPPA violations (children's privacy)
            coppa_violations = [
                'collect from children', 'under 13 data', 'no parental consent',
                'child personal info', 'minor data collection', 'kids privacy'
            ]
            
            coppa_violation_count = sum(1 for violation in coppa_violations 
                                      if violation in content_text.lower())
            
            if coppa_violation_count > 0:
                compliance_analysis['violations'].append('coppa_violation')
                compliance_analysis['compliance_score'] -= 0.4
            
            # Check for HIPAA violations (health information)
            hipaa_violations = [
                'share health records', 'medical info leak', 'unauthorized health data',
                'phi disclosure', 'health privacy violation', 'medical record sharing'
            ]
            
            hipaa_violation_count = sum(1 for violation in hipaa_violations 
                                      if violation in content_text.lower())
            
            if hipaa_violation_count > 0:
                compliance_analysis['violations'].append('hipaa_violation')
                compliance_analysis['compliance_score'] -= 0.35
            
            # Check for cross-border transfer issues
            transfer_issues = [
                'transfer to unsafe country', 'no adequacy decision', 'unsafe transfer',
                'inadequate protection', 'cross-border violation', 'international transfer'
            ]
            
            transfer_issue_count = sum(1 for issue in transfer_issues 
                                     if issue in content_text.lower())
            
            if transfer_issue_count > 0:
                compliance_analysis['jurisdiction_issues'].append('unsafe_transfer')
                compliance_analysis['compliance_score'] -= 0.2
            
            # Ensure score doesn't go below 0
            compliance_analysis['compliance_score'] = max(0.0, compliance_analysis['compliance_score'])
            
            return compliance_analysis
            
        except Exception as e:
            logger.error(f"Failed to check regulatory compliance: {str(e)}")
            return {'compliance_score': 0.5, 'error': str(e)}
    
    async def _evaluate_consent_management(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate consent management practices."""
        try:
            consent_analysis = {
                'consent_score': 0.8,  # Start with good consent assumption
                'consent_issues': [],
                'consent_violations': [],
                'consent_quality': 'adequate'
            }
            
            content_text = content.get('content', '')
            
            # Check for lack of consent
            no_consent_indicators = [
                'no consent needed', 'skip consent', 'ignore permission',
                'without asking', 'assume consent', 'implied consent'
            ]
            
            no_consent_count = sum(1 for indicator in no_consent_indicators 
                                 if indicator in content_text.lower())
            
            if no_consent_count > 0:
                consent_analysis['consent_violations'].append('lack_of_consent')
                consent_analysis['consent_score'] -= 0.4
            
            # Check for coerced consent
            coercion_indicators = [
                'forced consent', 'no choice', 'must agree', 'required consent',
                'coerced agreement', 'mandatory acceptance'
            ]
            
            coercion_count = sum(1 for indicator in coercion_indicators 
                               if indicator in content_text.lower())
            
            if coercion_count > 0:
                consent_analysis['consent_violations'].append('coerced_consent')
                consent_analysis['consent_score'] -= 0.35
            
            # Check for unclear consent
            unclear_consent_indicators = [
                'vague consent', 'unclear terms', 'confusing agreement',
                'ambiguous consent', 'unclear permission', 'confusing terms'
            ]
            
            unclear_consent_count = sum(1 for indicator in unclear_consent_indicators 
                                      if indicator in content_text.lower())
            
            if unclear_consent_count > 0:
                consent_analysis['consent_issues'].append('unclear_consent')
                consent_analysis['consent_score'] -= 0.2
            
            # Check for bundled consent
            bundled_consent_indicators = [
                'all or nothing', 'bundled consent', 'package deal',
                'take it or leave it', 'no granular choice', 'blanket consent'
            ]
            
            bundled_consent_count = sum(1 for indicator in bundled_consent_indicators 
                                      if indicator in content_text.lower())
            
            if bundled_consent_count > 0:
                consent_analysis['consent_issues'].append('bundled_consent')
                consent_analysis['consent_score'] -= 0.25
            
            # Check for positive consent indicators
            positive_consent_indicators = [
                'clear consent', 'informed agreement', 'granular choice',
                'opt-in', 'explicit consent', 'freely given'
            ]
            
            positive_consent_count = sum(1 for indicator in positive_consent_indicators 
                                       if indicator in content_text.lower())
            
            if positive_consent_count > 0:
                consent_analysis['consent_score'] += 0.1
            
            # Determine consent quality
            if consent_analysis['consent_score'] >= 0.8:
                consent_analysis['consent_quality'] = 'excellent'
            elif consent_analysis['consent_score'] >= 0.6:
                consent_analysis['consent_quality'] = 'good'
            elif consent_analysis['consent_score'] >= 0.4:
                consent_analysis['consent_quality'] = 'adequate'
            else:
                consent_analysis['consent_quality'] = 'poor'
            
            # Ensure score stays within bounds
            consent_analysis['consent_score'] = max(0.0, min(1.0, consent_analysis['consent_score']))
            
            return consent_analysis
            
        except Exception as e:
            logger.error(f"Failed to evaluate consent management: {str(e)}")
            return {'consent_score': 0.5, 'error': str(e)}
    
    async def _assess_data_minimization(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess data minimization compliance."""
        try:
            minimization_analysis = {
                'minimization_score': 0.8,
                'minimization_violations': [],
                'excessive_collection_indicators': [],
                'purpose_limitation_issues': []
            }
            
            content_text = content.get('content', '')
            
            # Check for excessive data collection
            excessive_collection_indicators = [
                'collect everything', 'gather all data', 'maximum information',
                'comprehensive data', 'all available info', 'complete profile'
            ]
            
            excessive_collection_count = sum(1 for indicator in excessive_collection_indicators 
                                           if indicator in content_text.lower())
            
            if excessive_collection_count > 0:
                minimization_analysis['excessive_collection_indicators'].append('excessive_collection_language')
                minimization_analysis['minimization_score'] -= 0.3
            
            # Check for purpose creep
            purpose_creep_indicators = [
                'use for other purposes', 'additional uses', 'expand usage',
                'different purpose', 'secondary use', 'repurpose data'
            ]
            
            purpose_creep_count = sum(1 for indicator in purpose_creep_indicators 
                                    if indicator in content_text.lower())
            
            if purpose_creep_count > 0:
                minimization_analysis['purpose_limitation_issues'].append('purpose_creep')
                minimization_analysis['minimization_score'] -= 0.25
            
            # Check for indefinite retention
            indefinite_retention_indicators = [
                'keep forever', 'permanent storage', 'indefinite retention',
                'never delete', 'store permanently', 'unlimited storage'
            ]
            
            indefinite_retention_count = sum(1 for indicator in indefinite_retention_indicators 
                                           if indicator in content_text.lower())
            
            if indefinite_retention_count > 0:
                minimization_analysis['minimization_violations'].append('indefinite_retention')
                minimization_analysis['minimization_score'] -= 0.35
            
            # Check for positive minimization practices
            positive_minimization_indicators = [
                'minimal data', 'necessary only', 'limited collection',
                'purpose-specific', 'data minimization', 'limited retention'
            ]
            
            positive_minimization_count = sum(1 for indicator in positive_minimization_indicators 
                                            if indicator in content_text.lower())
            
            if positive_minimization_count > 0:
                minimization_analysis['minimization_score'] += 0.1
            
            # Ensure score stays within bounds
            minimization_analysis['minimization_score'] = max(0.0, min(1.0, minimization_analysis['minimization_score']))
            
            return minimization_analysis
            
        except Exception as e:
            logger.error(f"Failed to assess data minimization: {str(e)}")
            return {'minimization_score': 0.5, 'error': str(e)}
    
    async def _check_privacy_rights_violations(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for privacy rights violations."""
        try:
            rights_analysis = {
                'rights_protection_score': 1.0,
                'rights_violations': [],
                'denied_rights': [],
                'rights_obstruction': []
            }
            
            content_text = content.get('content', '')
            
            # Check for right to access violations
            access_violations = [
                'deny access', 'no right to see', 'cannot view data',
                'refuse access', 'block data access', 'hide information'
            ]
            
            access_violation_count = sum(1 for violation in access_violations 
                                       if violation in content_text.lower())
            
            if access_violation_count > 0:
                rights_analysis['denied_rights'].append('right_to_access')
                rights_analysis['rights_protection_score'] -= 0.2
            
            # Check for right to rectification violations
            rectification_violations = [
                'cannot correct', 'no updates allowed', 'refuse correction',
                'deny rectification', 'block changes', 'immutable data'
            ]
            
            rectification_violation_count = sum(1 for violation in rectification_violations 
                                              if violation in content_text.lower())
            
            if rectification_violation_count > 0:
                rights_analysis['denied_rights'].append('right_to_rectification')
                rights_analysis['rights_protection_score'] -= 0.2
            
            # Check for right to erasure violations
            erasure_violations = [
                'cannot delete', 'no right to forget', 'refuse deletion',
                'deny erasure', 'permanent record', 'cannot remove'
            ]
            
            erasure_violation_count = sum(1 for violation in erasure_violations 
                                        if violation in content_text.lower())
            
            if erasure_violation_count > 0:
                rights_analysis['denied_rights'].append('right_to_erasure')
                rights_analysis['rights_protection_score'] -= 0.25
            
            # Check for right to portability violations
            portability_violations = [
                'cannot export', 'no data portability', 'refuse export',
                'deny portability', 'locked data', 'cannot transfer'
            ]
            
            portability_violation_count = sum(1 for violation in portability_violations 
                                            if violation in content_text.lower())
            
            if portability_violation_count > 0:
                rights_analysis['denied_rights'].append('right_to_portability')
                rights_analysis['rights_protection_score'] -= 0.15
            
            # Check for right to object violations
            objection_violations = [
                'cannot object', 'no opt-out', 'refuse objection',
                'deny objection', 'forced processing', 'cannot refuse'
            ]
            
            objection_violation_count = sum(1 for violation in objection_violations 
                                          if violation in content_text.lower())
            
            if objection_violation_count > 0:
                rights_analysis['denied_rights'].append('right_to_object')
                rights_analysis['rights_protection_score'] -= 0.2
            
            # Ensure score doesn't go below 0
            rights_analysis['rights_protection_score'] = max(0.0, rights_analysis['rights_protection_score'])
            
            return rights_analysis
            
        except Exception as e:
            logger.error(f"Failed to check privacy rights violations: {str(e)}")
            return {'rights_protection_score': 0.5, 'error': str(e)}
    
    async def _analyze_cross_border_transfers(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cross-border data transfer compliance."""
        try:
            transfer_analysis = {
                'transfer_compliance_score': 1.0,
                'transfer_violations': [],
                'jurisdiction_issues': [],
                'adequacy_concerns': []
            }
            
            content_text = content.get('content', '')
            
            # Check for unsafe country transfers
            unsafe_transfer_indicators = [
                'transfer to unsafe country', 'no adequacy decision', 'inadequate protection',
                'unsafe jurisdiction', 'poor privacy laws', 'weak protection'
            ]
            
            unsafe_transfer_count = sum(1 for indicator in unsafe_transfer_indicators 
                                      if indicator in content_text.lower())
            
            if unsafe_transfer_count > 0:
                transfer_analysis['transfer_violations'].append('unsafe_country_transfer')
                transfer_analysis['transfer_compliance_score'] -= 0.4
            
            # Check for lack of safeguards
            no_safeguards_indicators = [
                'no safeguards', 'unprotected transfer', 'no security measures',
                'unsafe transfer', 'no protection', 'vulnerable transfer'
            ]
            
            no_safeguards_count = sum(1 for indicator in no_safeguards_indicators 
                                    if indicator in content_text.lower())
            
            if no_safeguards_count > 0:
                transfer_analysis['transfer_violations'].append('lack_of_safeguards')
                transfer_analysis['transfer_compliance_score'] -= 0.3
            
            # Check for jurisdiction shopping
            jurisdiction_shopping_indicators = [
                'jurisdiction shopping', 'forum shopping', 'avoid regulations',
                'regulatory arbitrage', 'escape oversight', 'evade laws'
            ]
            
            jurisdiction_shopping_count = sum(1 for indicator in jurisdiction_shopping_indicators 
                                            if indicator in content_text.lower())
            
            if jurisdiction_shopping_count > 0:
                transfer_analysis['jurisdiction_issues'].append('jurisdiction_shopping')
                transfer_analysis['transfer_compliance_score'] -= 0.35
            
            # Ensure score doesn't go below 0
            transfer_analysis['transfer_compliance_score'] = max(0.0, transfer_analysis['transfer_compliance_score'])
            
            return transfer_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze cross-border transfers: {str(e)}")
            return {'transfer_compliance_score': 0.5, 'error': str(e)}
    
    async def _get_ai_privacy_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on privacy protection."""
        try:
            prompt = self._create_privacy_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (Claude for privacy analysis)
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
                'reasoning': 'No AI providers available for privacy analysis'
            }
            
        except Exception as e:
            logger.error(f"AI privacy analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_privacy_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a privacy protection focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='privacy protection, data compliance, and personal information security'
        )
        
        privacy_specific = f"""
PRIVACY PROTECTION ANALYSIS

You are a specialized Privacy Protection Agent focused on safeguarding user privacy,
ensuring data protection compliance, and preventing privacy violations.

User Trust Context:
- Author Trust Score: {trust_score}

Privacy Protection Framework:
1. Personal Information Detection: Identify and protect personal data exposure
2. Privacy Violation Prevention: Stop unauthorized data sharing and misuse
3. Regulatory Compliance: Ensure adherence to GDPR, CCPA, and other regulations
4. Consent Management: Verify proper consent practices and user rights
5. Data Minimization: Enforce collection and retention limitations
6. Privacy Rights Protection: Safeguard user privacy rights and freedoms
7. Cross-Border Compliance: Monitor international data transfer compliance

Critical Privacy Threats:
- Personal information exposure (emails, phones, addresses, SSNs, etc.)
- Unauthorized data sharing and privacy violations
- Regulatory compliance violations (GDPR, CCPA, HIPAA, COPPA)
- Consent violations and coerced agreements
- Data minimization failures and excessive collection
- Privacy rights denials and obstruction
- Unsafe cross-border data transfers
- Health, financial, and biometric data exposure

Decision Guidelines:
- BLOCK: Direct privacy violations and personal data exposure
- FLAG: Regulatory compliance issues and consent violations
- MONITOR: Potential privacy risks and data minimization concerns
- APPROVE: Privacy-compliant content and proper data handling

Protection Priorities:
- Prevent personal information exposure and identity theft
- Ensure regulatory compliance and avoid legal violations
- Protect user consent and privacy rights
- Enforce data minimization and purpose limitation
- Safeguard sensitive data (health, financial, biometric)
- Maintain cross-border transfer compliance
- Support privacy-by-design principles

CRITICAL: Any content that exposes personal information, violates privacy regulations,
or undermines user privacy rights must be immediately flagged or blocked.
"""
        
        return base_prompt + privacy_specific
    
    async def _make_privacy_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        personal_data_analysis: Dict[str, Any],
        privacy_violations: Dict[str, Any],
        compliance_analysis: Dict[str, Any],
        consent_analysis: Dict[str, Any],
        data_minimization: Dict[str, Any],
        rights_violations: Dict[str, Any],
        cross_border_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make privacy protection focused moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Calculate overall privacy risk score
            risk_scores = [
                personal_data_analysis.get('exposure_risk_score', 0.0),
                privacy_violations.get('violation_risk_score', 0.0),
                1.0 - compliance_analysis.get('compliance_score', 1.0),
                1.0 - consent_analysis.get('consent_score', 0.8),
                1.0 - data_minimization.get('minimization_score', 0.8),
                1.0 - rights_violations.get('rights_protection_score', 1.0),
                1.0 - cross_border_analysis.get('transfer_compliance_score', 1.0)
            ]
            
            overall_privacy_risk = max(risk_scores)  # Use highest risk
            
            # Make decision based on privacy risk level
            if overall_privacy_risk >= self.privacy_config['risk_levels']['critical']:
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'Critical privacy violation detected'
                base_decision['priority'] = 'critical'
                
            elif overall_privacy_risk >= self.privacy_config['risk_levels']['high']:
                if base_decision['action'] == 'approve':
                    base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'High privacy risk - requires review'
                base_decision['priority'] = 'high'
                
            elif overall_privacy_risk >= self.privacy_config['risk_levels']['medium']:
                base_decision['monitoring_required'] = True
                base_decision['priority'] = 'medium'
            
            # Handle personal data exposure
            if personal_data_analysis.get('protection_required', False):
                if base_decision['action'] == 'approve':
                    base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Personal information exposure detected'
                base_decision['data_protection_required'] = True
            
            # Handle regulatory violations
            compliance_violations = compliance_analysis.get('violations', [])
            if compliance_violations:
                base_decision['action'] = 'block'
                base_decision['reasoning'] = f'Regulatory compliance violations: {", ".join(compliance_violations)}'
                base_decision['compliance_violation'] = True
            
            # Add privacy-specific metadata
            base_decision['metadata'] = base_decision.get('metadata', {})
            base_decision['metadata'].update({
                'agent': 'privacy_protection',
                'overall_privacy_risk': round(overall_privacy_risk, 3),
                'personal_data_detected': personal_data_analysis.get('personal_data_detected', False),
                'data_types_found': personal_data_analysis.get('data_types_found', []),
                'exposure_risk': round(personal_data_analysis.get('exposure_risk_score', 0.0), 3),
                'privacy_violations': privacy_violations.get('violation_types', []),
                'compliance_score': round(compliance_analysis.get('compliance_score', 1.0), 3),
                'consent_quality': consent_analysis.get('consent_quality', 'adequate'),
                'rights_protected': round(rights_violations.get('rights_protection_score', 1.0), 3)
            })
            
            # Add detailed evidence
            base_decision['evidence'] = base_decision.get('evidence', {})
            base_decision['evidence'].update({
                'personal_data_analysis': personal_data_analysis,
                'privacy_violations': privacy_violations,
                'compliance_analysis': compliance_analysis,
                'consent_analysis': consent_analysis,
                'data_minimization': data_minimization,
                'rights_violations': rights_violations,
                'cross_border_analysis': cross_border_analysis
            })
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make privacy decision: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Privacy decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'privacy_protection', 'error': True}
            }
    
    async def _update_privacy_metrics(
        self, 
        content: Dict[str, Any], 
        decision: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> None:
        """Update privacy protection metrics for performance tracking."""
        try:
            self.privacy_metrics['total_content_analyzed'] += 1
            
            # Track personal data detection
            if decision.get('metadata', {}).get('personal_data_detected', False):
                self.privacy_metrics['personal_data_detected'] += 1
            
            # Track privacy violations prevented
            if decision.get('action') in ['block', 'flag'] and 'privacy' in decision.get('reasoning', '').lower():
                self.privacy_metrics['privacy_violations_prevented'] += 1
            
            # Track consent violations
            if decision.get('metadata', {}).get('consent_quality') == 'poor':
                self.privacy_metrics['consent_violations_flagged'] += 1
            
            # Track data protection actions
            if decision.get('data_protection_required', False):
                self.privacy_metrics['data_protection_actions'] += 1
            
            # Track regulatory compliance checks
            if decision.get('compliance_violation', False):
                self.privacy_metrics['regulatory_compliance_checks'] += 1
            
        except Exception as e:
            logger.error(f"Failed to update privacy metrics: {str(e)}")