# Legal Compliance Monitor Agent for TrustStream v4.4
# Specialized agent for legal compliance and regulatory adherence

import logging
import json
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class LegalComplianceMonitorAgent(BaseAIAgent):
    """
    Legal Compliance Monitor Agent - Specialized Legal and Regulatory Compliance
    
    This agent ensures content and community activities comply with applicable
    laws, regulations, and platform policies across multiple jurisdictions.
    
    Key Responsibilities:
    - Legal compliance monitoring and enforcement
    - Regulatory adherence verification (GDPR, CCPA, COPPA, etc.)
    - Platform policy enforcement
    - Terms of service violation detection
    - Intellectual property protection
    - Content liability assessment
    - Jurisdictional compliance analysis
    - Legal risk mitigation
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Legal compliance configuration
        self.legal_compliance_config = {
            'jurisdictions': ['US', 'EU', 'UK', 'CA', 'AU', 'global'],
            'regulations': {
                'data_protection': ['GDPR', 'CCPA', 'PIPEDA', 'Privacy_Act'],
                'child_protection': ['COPPA', 'CIPA', 'UK_Age_Appropriate_Design'],
                'content_regulation': ['DMCA', 'DSA', 'NetzDG', 'Online_Safety_Bill'],
                'accessibility': ['ADA', 'WCAG', 'EN_301_549', 'AODA'],
                'financial': ['PCI_DSS', 'SOX', 'PSD2', 'Open_Banking'],
                'healthcare': ['HIPAA', 'HITECH', 'FDA_regulations'],
                'employment': ['EEOC', 'NLRA', 'GDPR_employment']
            },
            'compliance_areas': [
                'data_protection', 'content_moderation', 'user_rights',
                'intellectual_property', 'platform_liability', 'accessibility',
                'financial_compliance', 'healthcare_compliance', 'employment_law'
            ],
            'risk_levels': ['critical', 'high', 'medium', 'low', 'minimal']
        }
        
        # Legal violation patterns
        self.legal_violation_patterns = {
            'copyright_infringement': [
                r'copyrighted.*material',
                r'pirated.*content',
                r'unauthorized.*distribution',
                r'copyright.*violation',
                r'dmca.*takedown',
                r'intellectual.*property.*theft'
            ],
            'trademark_violation': [
                r'trademark.*infringement',
                r'unauthorized.*use.*trademark',
                r'brand.*impersonation',
                r'counterfeit.*goods',
                r'trademark.*dilution'
            ],
            'defamation': [
                r'false.*statements.*harm',
                r'libel',
                r'slander',
                r'defamatory.*content',
                r'reputation.*damage',
                r'malicious.*falsehoods'
            ],
            'harassment_legal': [
                r'stalking',
                r'cyberstalking',
                r'criminal.*harassment',
                r'threatening.*behavior',
                r'intimidation',
                r'persistent.*unwanted.*contact'
            ],
            'fraud': [
                r'fraudulent.*activity',
                r'scam',
                r'deceptive.*practices',
                r'false.*advertising',
                r'pyramid.*scheme',
                r'ponzi.*scheme'
            ],
            'illegal_content': [
                r'illegal.*drugs',
                r'controlled.*substances',
                r'illegal.*weapons',
                r'child.*exploitation',
                r'human.*trafficking',
                r'terrorism.*content'
            ],
            'financial_crimes': [
                r'money.*laundering',
                r'tax.*evasion',
                r'securities.*fraud',
                r'insider.*trading',
                r'financial.*fraud',
                r'cryptocurrency.*scam'
            ]
        }
        
        # GDPR compliance patterns
        self.gdpr_patterns = {
            'data_processing_violations': [
                r'processing.*without.*consent',
                r'unlawful.*data.*processing',
                r'excessive.*data.*collection',
                r'purpose.*limitation.*violation',
                r'data.*minimization.*violation'
            ],
            'consent_violations': [
                r'forced.*consent',
                r'bundled.*consent',
                r'unclear.*consent',
                r'consent.*withdrawal.*blocked',
                r'pre-ticked.*boxes'
            ],
            'data_subject_rights_violations': [
                r'access.*request.*denied',
                r'rectification.*denied',
                r'erasure.*request.*ignored',
                r'portability.*denied',
                r'objection.*ignored'
            ],
            'data_breach_indicators': [
                r'personal.*data.*breach',
                r'unauthorized.*access.*data',
                r'data.*leak',
                r'security.*incident.*personal.*data',
                r'accidental.*disclosure'
            ]
        }
        
        # COPPA compliance patterns
        self.coppa_patterns = {
            'child_data_collection': [
                r'collecting.*data.*children.*under.*13',
                r'personal.*information.*minors',
                r'child.*data.*without.*consent',
                r'tracking.*children.*online',
                r'behavioral.*advertising.*children'
            ],
            'parental_consent_violations': [
                r'no.*parental.*consent',
                r'inadequate.*consent.*mechanism',
                r'consent.*verification.*failure',
                r'parental.*notification.*missing'
            ]
        }
        
        # Platform policy violations
        self.platform_policy_patterns = {
            'terms_of_service_violations': [
                r'tos.*violation',
                r'terms.*breach',
                r'service.*agreement.*violation',
                r'user.*agreement.*breach',
                r'community.*guidelines.*violation'
            ],
            'spam_violations': [
                r'unsolicited.*messages',
                r'bulk.*messaging',
                r'automated.*posting',
                r'repetitive.*content',
                r'commercial.*spam'
            ],
            'impersonation': [
                r'identity.*theft',
                r'account.*impersonation',
                r'false.*identity',
                r'misleading.*profile',
                r'catfishing'
            ],
            'manipulation': [
                r'vote.*manipulation',
                r'artificial.*engagement',
                r'bot.*networks',
                r'sock.*puppet.*accounts',
                r'coordinated.*inauthentic.*behavior'
            ]
        }
        
        # Intellectual property indicators
        self.ip_indicators = {
            'copyright_claims': [
                'original work', 'creative commons', 'fair use', 'copyright notice',
                'all rights reserved', 'unauthorized reproduction', 'dmca'
            ],
            'trademark_usage': [
                'registered trademark', 'trademark symbol', 'brand name',
                'commercial use', 'trademark owner', 'authorized dealer'
            ],
            'patent_references': [
                'patented technology', 'patent pending', 'intellectual property',
                'proprietary technology', 'patent infringement', 'prior art'
            ]
        }
        
        # Legal compliance thresholds
        self.legal_compliance_thresholds = {
            'critical_violation': 0.9,
            'high_risk_violation': 0.7,
            'moderate_risk_violation': 0.5,
            'low_risk_violation': 0.3,
            'compliance_review_needed': 0.4
        }
        
        # Legal compliance metrics
        self.legal_compliance_metrics = {
            'total_content_analyzed': 0,
            'legal_violations_detected': 0,
            'gdpr_violations_prevented': 0,
            'coppa_violations_prevented': 0,
            'copyright_violations_detected': 0,
            'platform_policy_violations': 0,
            'legal_reviews_triggered': 0,
            'compliance_interventions': 0
        }
        
        logger.info(f"Legal Compliance Monitor Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content for legal compliance and regulatory adherence.
        
        The Legal Compliance Monitor Agent evaluates:
        - Legal violation detection and prevention
        - Regulatory compliance verification (GDPR, COPPA, etc.)
        - Platform policy enforcement
        - Intellectual property protection
        - Terms of service compliance
        - Content liability assessment
        - Jurisdictional compliance requirements
        - Legal risk mitigation strategies
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Detect legal violations
            legal_violations_analysis = await self._detect_legal_violations(content, context)
            
            # Check GDPR compliance
            gdpr_compliance_analysis = await self._check_gdpr_compliance(content, context)
            
            # Check COPPA compliance
            coppa_compliance_analysis = await self._check_coppa_compliance(content, context)
            
            # Analyze platform policy compliance
            platform_policy_analysis = await self._analyze_platform_policy_compliance(content, context)
            
            # Check intellectual property compliance
            ip_compliance_analysis = await self._check_ip_compliance(content, context)
            
            # Assess content liability
            liability_analysis = await self._assess_content_liability(content, context)
            
            # Check jurisdictional compliance
            jurisdictional_analysis = await self._check_jurisdictional_compliance(content, context)
            
            # Get AI provider analysis for legal compliance
            ai_analysis = await self._get_ai_legal_compliance_analysis(content, trust_score, context)
            
            # Make legal compliance decision
            decision = await self._make_legal_compliance_decision(
                content=content,
                trust_score=trust_score,
                legal_violations_analysis=legal_violations_analysis,
                gdpr_compliance_analysis=gdpr_compliance_analysis,
                coppa_compliance_analysis=coppa_compliance_analysis,
                platform_policy_analysis=platform_policy_analysis,
                ip_compliance_analysis=ip_compliance_analysis,
                liability_analysis=liability_analysis,
                jurisdictional_analysis=jurisdictional_analysis,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Update legal compliance metrics
            await self._update_legal_compliance_metrics(content, decision, context)
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Legal compliance analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Legal compliance analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'legal_compliance_monitor', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Legal Compliance Monitor Agent."""
        return [
            'legal_violation_detection',
            'gdpr_compliance_monitoring',
            'coppa_compliance_verification',
            'platform_policy_enforcement',
            'intellectual_property_protection',
            'content_liability_assessment',
            'jurisdictional_compliance_analysis',
            'regulatory_adherence_verification',
            'terms_of_service_enforcement',
            'legal_risk_mitigation'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Legal Compliance Monitor Agent."""
        return (
            "Specialized agent for legal compliance and regulatory adherence. "
            "Monitors legal violations, ensures regulatory compliance (GDPR, COPPA), "
            "enforces platform policies, and protects intellectual property rights."
        )
    
    # Private analysis methods
    
    async def _detect_legal_violations(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect potential legal violations in content."""
        try:
            legal_analysis = {
                'violations_detected': [],
                'violation_score': 0.0,
                'violation_types': [],
                'legal_risk_level': 'low',
                'immediate_action_required': False
            }
            
            content_text = content.get('content', '').lower()
            
            violation_score = 0.0
            
            # Check for copyright infringement
            copyright_score = 0.0
            for pattern in self.legal_violation_patterns['copyright_infringement']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    legal_analysis['violations_detected'].append('copyright_infringement')
                    legal_analysis['violation_types'].append('intellectual_property')
                    copyright_score += len(matches) * 0.4
            
            if copyright_score > 0:
                violation_score += copyright_score
            
            # Check for trademark violations
            trademark_score = 0.0
            for pattern in self.legal_violation_patterns['trademark_violation']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    legal_analysis['violations_detected'].append('trademark_violation')
                    legal_analysis['violation_types'].append('intellectual_property')
                    trademark_score += len(matches) * 0.35
            
            if trademark_score > 0:
                violation_score += trademark_score
            
            # Check for defamation
            defamation_score = 0.0
            for pattern in self.legal_violation_patterns['defamation']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    legal_analysis['violations_detected'].append('defamation')
                    legal_analysis['violation_types'].append('content_liability')
                    defamation_score += len(matches) * 0.5
            
            if defamation_score > 0:
                violation_score += defamation_score
            
            # Check for legal harassment
            harassment_score = 0.0
            for pattern in self.legal_violation_patterns['harassment_legal']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    legal_analysis['violations_detected'].append('legal_harassment')
                    legal_analysis['violation_types'].append('criminal_behavior')
                    harassment_score += len(matches) * 0.6
            
            if harassment_score > 0:
                violation_score += harassment_score
            
            # Check for fraud
            fraud_score = 0.0
            for pattern in self.legal_violation_patterns['fraud']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    legal_analysis['violations_detected'].append('fraud')
                    legal_analysis['violation_types'].append('financial_crime')
                    fraud_score += len(matches) * 0.7
            
            if fraud_score > 0:
                violation_score += fraud_score
            
            # Check for illegal content
            illegal_content_score = 0.0
            for pattern in self.legal_violation_patterns['illegal_content']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    legal_analysis['violations_detected'].append('illegal_content')
                    legal_analysis['violation_types'].append('criminal_content')
                    illegal_content_score += len(matches) * 0.8
            
            if illegal_content_score > 0:
                violation_score += illegal_content_score
                legal_analysis['immediate_action_required'] = True
            
            # Check for financial crimes
            financial_crime_score = 0.0
            for pattern in self.legal_violation_patterns['financial_crimes']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    legal_analysis['violations_detected'].append('financial_crimes')
                    legal_analysis['violation_types'].append('financial_crime')
                    financial_crime_score += len(matches) * 0.75
            
            if financial_crime_score > 0:
                violation_score += financial_crime_score
                legal_analysis['immediate_action_required'] = True
            
            legal_analysis['violation_score'] = min(1.0, violation_score)
            
            # Determine legal risk level
            if legal_analysis['violation_score'] >= self.legal_compliance_thresholds['critical_violation']:
                legal_analysis['legal_risk_level'] = 'critical'
                legal_analysis['immediate_action_required'] = True
            elif legal_analysis['violation_score'] >= self.legal_compliance_thresholds['high_risk_violation']:
                legal_analysis['legal_risk_level'] = 'high'
            elif legal_analysis['violation_score'] >= self.legal_compliance_thresholds['moderate_risk_violation']:
                legal_analysis['legal_risk_level'] = 'moderate'
            elif legal_analysis['violation_score'] >= self.legal_compliance_thresholds['low_risk_violation']:
                legal_analysis['legal_risk_level'] = 'low'
            
            return legal_analysis
            
        except Exception as e:
            logger.error(f"Failed to detect legal violations: {str(e)}")
            return {'violation_score': 0.0, 'error': str(e)}
    
    async def _check_gdpr_compliance(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check GDPR compliance requirements."""
        try:
            gdpr_analysis = {
                'gdpr_violations': [],
                'compliance_score': 1.0,
                'data_processing_issues': [],
                'consent_issues': [],
                'data_subject_rights_issues': [],
                'breach_indicators': []
            }
            
            content_text = content.get('content', '').lower()
            user_location = context.get('user_location', '')
            
            compliance_violations = 0.0
            
            # Check for data processing violations
            for pattern in self.gdpr_patterns['data_processing_violations']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    gdpr_analysis['gdpr_violations'].append('data_processing_violation')
                    gdpr_analysis['data_processing_issues'].append(pattern)
                    compliance_violations += len(matches) * 0.3
            
            # Check for consent violations
            for pattern in self.gdpr_patterns['consent_violations']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    gdpr_analysis['gdpr_violations'].append('consent_violation')
                    gdpr_analysis['consent_issues'].append(pattern)
                    compliance_violations += len(matches) * 0.35
            
            # Check for data subject rights violations
            for pattern in self.gdpr_patterns['data_subject_rights_violations']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    gdpr_analysis['gdpr_violations'].append('data_subject_rights_violation')
                    gdpr_analysis['data_subject_rights_issues'].append(pattern)
                    compliance_violations += len(matches) * 0.4
            
            # Check for data breach indicators
            for pattern in self.gdpr_patterns['data_breach_indicators']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    gdpr_analysis['gdpr_violations'].append('data_breach')
                    gdpr_analysis['breach_indicators'].append(pattern)
                    compliance_violations += len(matches) * 0.5
            
            # Check if GDPR applies (EU users or EU data processing)
            eu_jurisdictions = ['EU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'SE', 'DK', 'FI']
            if user_location in eu_jurisdictions or 'eu' in content_text:
                # GDPR applies - stricter compliance required
                if compliance_violations > 0:
                    compliance_violations += 0.2  # Increase severity for EU users
            
            gdpr_analysis['compliance_score'] = max(0.0, 1.0 - compliance_violations)
            
            return gdpr_analysis
            
        except Exception as e:
            logger.error(f"Failed to check GDPR compliance: {str(e)}")
            return {'compliance_score': 1.0, 'error': str(e)}
    
    async def _check_coppa_compliance(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check COPPA compliance for child protection."""
        try:
            coppa_analysis = {
                'coppa_violations': [],
                'compliance_score': 1.0,
                'child_data_issues': [],
                'parental_consent_issues': [],
                'applies_to_content': False
            }
            
            content_text = content.get('content', '').lower()
            author_age = context.get('author', {}).get('age', 0)
            
            compliance_violations = 0.0
            
            # Check if COPPA applies (children under 13 or child-directed content)
            if author_age < 13 or any(indicator in content_text for indicator in ['children', 'kids', 'under 13', 'minors']):
                coppa_analysis['applies_to_content'] = True
                
                # Check for child data collection violations
                for pattern in self.coppa_patterns['child_data_collection']:
                    matches = re.findall(pattern, content_text, re.IGNORECASE)
                    if matches:
                        coppa_analysis['coppa_violations'].append('child_data_collection')
                        coppa_analysis['child_data_issues'].append(pattern)
                        compliance_violations += len(matches) * 0.5
                
                # Check for parental consent violations
                for pattern in self.coppa_patterns['parental_consent_violations']:
                    matches = re.findall(pattern, content_text, re.IGNORECASE)
                    if matches:
                        coppa_analysis['coppa_violations'].append('parental_consent_violation')
                        coppa_analysis['parental_consent_issues'].append(pattern)
                        compliance_violations += len(matches) * 0.6
                
                # Additional checks for child-directed content
                if author_age < 13:
                    # Stricter requirements for content from children
                    personal_info_indicators = [
                        'my name is', 'i live at', 'my phone number',
                        'my school is', 'my address', 'my email'
                    ]
                    
                    personal_info_count = sum(1 for indicator in personal_info_indicators 
                                            if indicator in content_text)
                    
                    if personal_info_count > 0:
                        coppa_analysis['coppa_violations'].append('child_personal_info_sharing')
                        compliance_violations += personal_info_count * 0.4
            
            coppa_analysis['compliance_score'] = max(0.0, 1.0 - compliance_violations)
            
            return coppa_analysis
            
        except Exception as e:
            logger.error(f"Failed to check COPPA compliance: {str(e)}")
            return {'compliance_score': 1.0, 'error': str(e)}
    
    async def _analyze_platform_policy_compliance(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze compliance with platform policies."""
        try:
            policy_analysis = {
                'policy_violations': [],
                'compliance_score': 1.0,
                'tos_violations': [],
                'spam_indicators': [],
                'impersonation_indicators': [],
                'manipulation_indicators': []
            }
            
            content_text = content.get('content', '').lower()
            
            policy_violations = 0.0
            
            # Check for Terms of Service violations
            for pattern in self.platform_policy_patterns['terms_of_service_violations']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    policy_analysis['policy_violations'].append('tos_violation')
                    policy_analysis['tos_violations'].append(pattern)
                    policy_violations += len(matches) * 0.3
            
            # Check for spam violations
            for pattern in self.platform_policy_patterns['spam_violations']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    policy_analysis['policy_violations'].append('spam_violation')
                    policy_analysis['spam_indicators'].append(pattern)
                    policy_violations += len(matches) * 0.25
            
            # Check for impersonation
            for pattern in self.platform_policy_patterns['impersonation']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    policy_analysis['policy_violations'].append('impersonation')
                    policy_analysis['impersonation_indicators'].append(pattern)
                    policy_violations += len(matches) * 0.4
            
            # Check for manipulation
            for pattern in self.platform_policy_patterns['manipulation']:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    policy_analysis['policy_violations'].append('manipulation')
                    policy_analysis['manipulation_indicators'].append(pattern)
                    policy_violations += len(matches) * 0.35
            
            policy_analysis['compliance_score'] = max(0.0, 1.0 - policy_violations)
            
            return policy_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze platform policy compliance: {str(e)}")
            return {'compliance_score': 1.0, 'error': str(e)}
    
    async def _check_ip_compliance(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check intellectual property compliance."""
        try:
            ip_analysis = {
                'ip_issues': [],
                'compliance_score': 1.0,
                'copyright_indicators': [],
                'trademark_indicators': [],
                'patent_indicators': [],
                'fair_use_assessment': 'unknown'
            }
            
            content_text = content.get('content', '').lower()
            
            ip_violations = 0.0
            
            # Check for copyright indicators
            copyright_count = 0
            for indicator in self.ip_indicators['copyright_claims']:
                if indicator in content_text:
                    ip_analysis['copyright_indicators'].append(indicator)
                    copyright_count += 1
            
            if copyright_count > 0:
                # Assess if it's a violation or legitimate use
                fair_use_indicators = ['fair use', 'educational purpose', 'criticism', 'commentary', 'parody']
                fair_use_count = sum(1 for indicator in fair_use_indicators if indicator in content_text)
                
                if fair_use_count > 0:
                    ip_analysis['fair_use_assessment'] = 'likely_fair_use'
                else:
                    ip_analysis['ip_issues'].append('potential_copyright_infringement')
                    ip_violations += copyright_count * 0.2
            
            # Check for trademark indicators
            trademark_count = 0
            for indicator in self.ip_indicators['trademark_usage']:
                if indicator in content_text:
                    ip_analysis['trademark_indicators'].append(indicator)
                    trademark_count += 1
            
            if trademark_count > 0:
                # Check for unauthorized commercial use
                commercial_indicators = ['selling', 'commercial use', 'business', 'profit']
                commercial_use = sum(1 for indicator in commercial_indicators if indicator in content_text)
                
                if commercial_use > 0:
                    ip_analysis['ip_issues'].append('potential_trademark_infringement')
                    ip_violations += trademark_count * 0.25
            
            # Check for patent indicators
            patent_count = 0
            for indicator in self.ip_indicators['patent_references']:
                if indicator in content_text:
                    ip_analysis['patent_indicators'].append(indicator)
                    patent_count += 1
            
            if patent_count > 0:
                # Patent issues are less common in content but still relevant
                infringement_indicators = ['patent infringement', 'unauthorized use', 'violation']
                infringement_count = sum(1 for indicator in infringement_indicators if indicator in content_text)
                
                if infringement_count > 0:
                    ip_analysis['ip_issues'].append('potential_patent_infringement')
                    ip_violations += patent_count * 0.15
            
            ip_analysis['compliance_score'] = max(0.0, 1.0 - ip_violations)
            
            return ip_analysis
            
        except Exception as e:
            logger.error(f"Failed to check IP compliance: {str(e)}")
            return {'compliance_score': 1.0, 'error': str(e)}
    
    async def _assess_content_liability(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess potential content liability issues."""
        try:
            liability_analysis = {
                'liability_risks': [],
                'risk_score': 0.0,
                'liability_types': [],
                'mitigation_needed': False,
                'legal_review_recommended': False
            }
            
            content_text = content.get('content', '').lower()
            content_type = content.get('type', 'text')
            
            risk_score = 0.0
            
            # Check for defamation liability
            defamation_indicators = [
                'false statement', 'reputation damage', 'malicious intent',
                'public figure', 'private individual', 'harm to reputation'
            ]
            
            defamation_count = sum(1 for indicator in defamation_indicators 
                                 if indicator in content_text)
            
            if defamation_count > 0:
                liability_analysis['liability_risks'].append('defamation_liability')
                liability_analysis['liability_types'].append('tort_liability')
                risk_score += defamation_count * 0.3
            
            # Check for privacy liability
            privacy_indicators = [
                'private information', 'invasion of privacy', 'personal details',
                'confidential information', 'unauthorized disclosure'
            ]
            
            privacy_count = sum(1 for indicator in privacy_indicators 
                              if indicator in content_text)
            
            if privacy_count > 0:
                liability_analysis['liability_risks'].append('privacy_liability')
                liability_analysis['liability_types'].append('privacy_tort')
                risk_score += privacy_count * 0.25
            
            # Check for negligence liability
            negligence_indicators = [
                'duty of care', 'breach of duty', 'harm caused',
                'negligent advice', 'professional negligence'
            ]
            
            negligence_count = sum(1 for indicator in negligence_indicators 
                                 if indicator in content_text)
            
            if negligence_count > 0:
                liability_analysis['liability_risks'].append('negligence_liability')
                liability_analysis['liability_types'].append('professional_liability')
                risk_score += negligence_count * 0.2
            
            # Check for product liability (if applicable)
            if content_type in ['product_review', 'recommendation', 'advertisement']:
                product_liability_indicators = [
                    'defective product', 'product harm', 'safety issue',
                    'product recall', 'manufacturing defect'
                ]
                
                product_liability_count = sum(1 for indicator in product_liability_indicators 
                                            if indicator in content_text)
                
                if product_liability_count > 0:
                    liability_analysis['liability_risks'].append('product_liability')
                    liability_analysis['liability_types'].append('product_liability')
                    risk_score += product_liability_count * 0.35
            
            liability_analysis['risk_score'] = min(1.0, risk_score)
            
            # Determine mitigation needs
            if liability_analysis['risk_score'] >= self.legal_compliance_thresholds['high_risk_violation']:
                liability_analysis['mitigation_needed'] = True
                liability_analysis['legal_review_recommended'] = True
            elif liability_analysis['risk_score'] >= self.legal_compliance_thresholds['compliance_review_needed']:
                liability_analysis['legal_review_recommended'] = True
            
            return liability_analysis
            
        except Exception as e:
            logger.error(f"Failed to assess content liability: {str(e)}")
            return {'risk_score': 0.0, 'error': str(e)}
    
    async def _check_jurisdictional_compliance(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check compliance across different jurisdictions."""
        try:
            jurisdictional_analysis = {
                'applicable_jurisdictions': [],
                'compliance_by_jurisdiction': {},
                'conflicts_detected': [],
                'highest_risk_jurisdiction': 'unknown',
                'global_compliance_score': 1.0
            }
            
            content_text = content.get('content', '').lower()
            user_location = context.get('user_location', '')
            community_location = context.get('community_location', '')
            
            # Determine applicable jurisdictions
            jurisdictions = set()
            
            if user_location:
                jurisdictions.add(user_location)
            
            if community_location:
                jurisdictions.add(community_location)
            
            # Check for jurisdiction-specific content
            jurisdiction_indicators = {
                'US': ['united states', 'usa', 'american', 'federal law', 'state law'],
                'EU': ['european union', 'gdpr', 'eu law', 'european'],
                'UK': ['united kingdom', 'british', 'uk law', 'england'],
                'CA': ['canada', 'canadian', 'pipeda', 'quebec'],
                'AU': ['australia', 'australian', 'privacy act']
            }
            
            for jurisdiction, indicators in jurisdiction_indicators.items():
                if any(indicator in content_text for indicator in indicators):
                    jurisdictions.add(jurisdiction)
            
            jurisdictional_analysis['applicable_jurisdictions'] = list(jurisdictions)
            
            # Assess compliance for each jurisdiction
            total_compliance_score = 0.0
            jurisdiction_count = len(jurisdictions) if jurisdictions else 1
            
            for jurisdiction in jurisdictions:
                compliance_score = await self._assess_jurisdiction_specific_compliance(
                    content, context, jurisdiction
                )
                jurisdictional_analysis['compliance_by_jurisdiction'][jurisdiction] = compliance_score
                total_compliance_score += compliance_score
            
            # Calculate global compliance score
            jurisdictional_analysis['global_compliance_score'] = total_compliance_score / jurisdiction_count
            
            # Identify highest risk jurisdiction
            if jurisdictional_analysis['compliance_by_jurisdiction']:
                lowest_compliance = min(jurisdictional_analysis['compliance_by_jurisdiction'].values())
                for jurisdiction, score in jurisdictional_analysis['compliance_by_jurisdiction'].items():
                    if score == lowest_compliance:
                        jurisdictional_analysis['highest_risk_jurisdiction'] = jurisdiction
                        break
            
            # Check for jurisdictional conflicts
            if len(jurisdictions) > 1:
                compliance_scores = list(jurisdictional_analysis['compliance_by_jurisdiction'].values())
                if max(compliance_scores) - min(compliance_scores) > 0.3:
                    jurisdictional_analysis['conflicts_detected'].append('significant_compliance_variance')
            
            return jurisdictional_analysis
            
        except Exception as e:
            logger.error(f"Failed to check jurisdictional compliance: {str(e)}")
            return {'global_compliance_score': 1.0, 'error': str(e)}
    
    async def _assess_jurisdiction_specific_compliance(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any], 
        jurisdiction: str
    ) -> float:
        """Assess compliance for a specific jurisdiction."""
        try:
            compliance_score = 1.0
            
            content_text = content.get('content', '').lower()
            
            # Jurisdiction-specific compliance checks
            if jurisdiction == 'EU':
                # GDPR compliance is critical for EU
                gdpr_violations = ['data processing without consent', 'unlawful processing', 'data breach']
                violation_count = sum(1 for violation in gdpr_violations if violation in content_text)
                compliance_score -= violation_count * 0.4
                
            elif jurisdiction == 'US':
                # COPPA, DMCA, and other US-specific laws
                us_violations = ['coppa violation', 'dmca infringement', 'section 230']
                violation_count = sum(1 for violation in us_violations if violation in content_text)
                compliance_score -= violation_count * 0.3
                
            elif jurisdiction == 'UK':
                # UK-specific regulations
                uk_violations = ['online safety bill', 'age appropriate design', 'uk gdpr']
                violation_count = sum(1 for violation in uk_violations if violation in content_text)
                compliance_score -= violation_count * 0.35
                
            elif jurisdiction == 'CA':
                # Canadian privacy laws
                ca_violations = ['pipeda violation', 'privacy breach', 'canadian privacy']
                violation_count = sum(1 for violation in ca_violations if violation in content_text)
                compliance_score -= violation_count * 0.3
                
            elif jurisdiction == 'AU':
                # Australian privacy and safety laws
                au_violations = ['privacy act violation', 'online safety act', 'australian privacy']
                violation_count = sum(1 for violation in au_violations if violation in content_text)
                compliance_score -= violation_count * 0.3
            
            return max(0.0, compliance_score)
            
        except Exception as e:
            logger.error(f"Failed to assess jurisdiction-specific compliance: {str(e)}")
            return 1.0
    
    async def _get_ai_legal_compliance_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on legal compliance."""
        try:
            prompt = self._create_legal_compliance_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (Claude for legal analysis)
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
                'reasoning': 'No AI providers available for legal compliance analysis'
            }
            
        except Exception as e:
            logger.error(f"AI legal compliance analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_legal_compliance_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a legal compliance-focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='legal compliance, regulatory adherence, and risk mitigation'
        )
        
        legal_compliance_specific = f"""
LEGAL COMPLIANCE ANALYSIS

You are a specialized Legal Compliance Monitor Agent focused on ensuring
content and community activities comply with applicable laws, regulations,
and platform policies across multiple jurisdictions.

User Trust Context:
- Author Trust Score: {trust_score}

Legal Compliance Framework:
1. Legal Violations: Detect copyright, trademark, defamation, harassment, fraud
2. Regulatory Compliance: Ensure GDPR, COPPA, CCPA, and other regulatory adherence
3. Platform Policies: Enforce terms of service and community guidelines
4. Intellectual Property: Protect copyrights, trademarks, and patents
5. Content Liability: Assess potential legal liability and risk
6. Jurisdictional Compliance: Ensure compliance across applicable jurisdictions
7. Data Protection: Verify privacy and data protection compliance
8. Risk Mitigation: Identify and mitigate legal risks

Critical Legal Violations:
- Copyright and trademark infringement
- Defamation and libel
- Criminal harassment and stalking
- Fraud and deceptive practices
- Illegal content (drugs, weapons, exploitation)
- Financial crimes and money laundering
- GDPR and privacy law violations
- COPPA violations affecting children
- Platform policy violations
- Terms of service breaches

Decision Guidelines:
- BLOCK: Serious legal violations, criminal content, immediate legal risk
- FLAG: Potential violations, compliance issues, legal review needed
- MONITOR: Minor policy violations, compliance concerns, risk assessment
- APPROVE: Compliant content, no legal issues detected

Regulatory Priorities:
- GDPR compliance for EU users and data processing
- COPPA compliance for children under 13
- CCPA compliance for California residents
- Platform-specific terms of service enforcement
- Intellectual property protection and fair use
- Content liability assessment and mitigation
- Cross-jurisdictional compliance verification
- Data protection and privacy rights

CRITICAL: Any content that violates laws, infringes intellectual property,
poses legal liability, or fails regulatory compliance must be flagged for
legal review and appropriate action.

Jurisdiction Considerations:
- EU: Strict GDPR compliance, Digital Services Act, right to be forgotten
- US: COPPA, DMCA, Section 230, state privacy laws
- UK: UK GDPR, Online Safety Bill, Age Appropriate Design Code
- Canada: PIPEDA, Bill C-11, provincial privacy laws
- Australia: Privacy Act, Online Safety Act, consumer protection laws
"""
        
        return base_prompt + legal_compliance_specific
    
    async def _make_legal_compliance_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        legal_violations_analysis: Dict[str, Any],
        gdpr_compliance_analysis: Dict[str, Any],
        coppa_compliance_analysis: Dict[str, Any],
        platform_policy_analysis: Dict[str, Any],
        ip_compliance_analysis: Dict[str, Any],
        liability_analysis: Dict[str, Any],
        jurisdictional_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make legal compliance-focused moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Handle critical legal violations
            if legal_violations_analysis.get('immediate_action_required', False):
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'Critical legal violation detected - immediate action required'
                base_decision['priority'] = 'critical'
                base_decision['legal_violation_detected'] = True
                
            # Handle severe GDPR violations
            elif gdpr_compliance_analysis.get('compliance_score', 1.0) < 0.3:
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'Severe GDPR compliance violation'
                base_decision['priority'] = 'high'
                base_decision['gdpr_violation'] = True
                
            # Handle COPPA violations
            elif (coppa_compliance_analysis.get('applies_to_content', False) and 
                  coppa_compliance_analysis.get('compliance_score', 1.0) < 0.5):
                base_decision['action'] = 'block'
                base_decision['reasoning'] = 'COPPA compliance violation affecting children'
                base_decision['priority'] = 'high'
                base_decision['coppa_violation'] = True
                
            # Handle high legal risk
            elif legal_violations_analysis.get('legal_risk_level') in ['critical', 'high']:
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'High legal risk detected - review required'
                base_decision['priority'] = 'high'
                base_decision['legal_review_needed'] = True
                
            # Handle content liability issues
            elif liability_analysis.get('legal_review_recommended', False):
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Content liability concerns - legal review recommended'
                base_decision['priority'] = 'medium'
                base_decision['liability_review_needed'] = True
                
            # Handle platform policy violations
            elif platform_policy_analysis.get('compliance_score', 1.0) < 0.5:
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Platform policy violations detected'
                base_decision['priority'] = 'medium'
                base_decision['policy_violation'] = True
                
            # Handle IP compliance issues
            elif ip_compliance_analysis.get('compliance_score', 1.0) < 0.7:
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Intellectual property compliance concerns'
                base_decision['priority'] = 'medium'
                base_decision['ip_review_needed'] = True
                
            # Handle jurisdictional compliance issues
            elif jurisdictional_analysis.get('global_compliance_score', 1.0) < 0.6:
                base_decision['action'] = 'flag'
                base_decision['reasoning'] = 'Jurisdictional compliance concerns'
                base_decision['priority'] = 'medium'
                base_decision['jurisdictional_review_needed'] = True
            
            # Add legal compliance-specific metadata
            base_decision['metadata'] = base_decision.get('metadata', {})
            base_decision['metadata'].update({
                'agent': 'legal_compliance_monitor',
                'legal_risk_level': legal_violations_analysis.get('legal_risk_level', 'low'),
                'violation_score': round(legal_violations_analysis.get('violation_score', 0.0), 3),
                'gdpr_compliance_score': round(gdpr_compliance_analysis.get('compliance_score', 1.0), 3),
                'coppa_compliance_score': round(coppa_compliance_analysis.get('compliance_score', 1.0), 3),
                'platform_policy_score': round(platform_policy_analysis.get('compliance_score', 1.0), 3),
                'ip_compliance_score': round(ip_compliance_analysis.get('compliance_score', 1.0), 3),
                'liability_risk_score': round(liability_analysis.get('risk_score', 0.0), 3),
                'global_compliance_score': round(jurisdictional_analysis.get('global_compliance_score', 1.0), 3)
            })
            
            # Add detailed evidence
            base_decision['evidence'] = base_decision.get('evidence', {})
            base_decision['evidence'].update({
                'legal_violations_analysis': legal_violations_analysis,
                'gdpr_compliance_analysis': gdpr_compliance_analysis,
                'coppa_compliance_analysis': coppa_compliance_analysis,
                'platform_policy_analysis': platform_policy_analysis,
                'ip_compliance_analysis': ip_compliance_analysis,
                'liability_analysis': liability_analysis,
                'jurisdictional_analysis': jurisdictional_analysis
            })
            
            # Add legal compliance recommendations
            if base_decision['action'] in ['block', 'flag']:
                recommendations = []
                
                if legal_violations_analysis.get('violations_detected'):
                    recommendations.extend([f"Address legal violation: {violation}" for violation in legal_violations_analysis['violations_detected']])
                
                if gdpr_compliance_analysis.get('gdpr_violations'):
                    recommendations.extend([f"GDPR compliance: {violation}" for violation in gdpr_compliance_analysis['gdpr_violations']])
                
                if coppa_compliance_analysis.get('coppa_violations'):
                    recommendations.extend([f"COPPA compliance: {violation}" for violation in coppa_compliance_analysis['coppa_violations']])
                
                if platform_policy_analysis.get('policy_violations'):
                    recommendations.extend([f"Policy compliance: {violation}" for violation in platform_policy_analysis['policy_violations']])
                
                if ip_compliance_analysis.get('ip_issues'):
                    recommendations.extend([f"IP compliance: {issue}" for issue in ip_compliance_analysis['ip_issues']])
                
                base_decision['legal_compliance_recommendations'] = recommendations
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make legal compliance decision: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'Legal compliance decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'legal_compliance_monitor', 'error': True}
            }
    
    async def _update_legal_compliance_metrics(
        self, 
        content: Dict[str, Any], 
        decision: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> None:
        """Update legal compliance metrics for performance tracking."""
        try:
            self.legal_compliance_metrics['total_content_analyzed'] += 1
            
            # Track legal violations
            if decision.get('legal_violation_detected', False):
                self.legal_compliance_metrics['legal_violations_detected'] += 1
            
            # Track GDPR violations
            if decision.get('gdpr_violation', False):
                self.legal_compliance_metrics['gdpr_violations_prevented'] += 1
            
            # Track COPPA violations
            if decision.get('coppa_violation', False):
                self.legal_compliance_metrics['coppa_violations_prevented'] += 1
            
            # Track copyright violations
            if 'copyright_infringement' in decision.get('evidence', {}).get('legal_violations_analysis', {}).get('violations_detected', []):
                self.legal_compliance_metrics['copyright_violations_detected'] += 1
            
            # Track platform policy violations
            if decision.get('policy_violation', False):
                self.legal_compliance_metrics['platform_policy_violations'] += 1
            
            # Track legal reviews
            if decision.get('legal_review_needed', False):
                self.legal_compliance_metrics['legal_reviews_triggered'] += 1
            
            # Track overall compliance interventions
            if decision['action'] in ['block', 'flag']:
                self.legal_compliance_metrics['compliance_interventions'] += 1
            
        except Exception as e:
            logger.error(f"Failed to update legal compliance metrics: {str(e)}")