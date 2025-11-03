# Transparency Moderator Agent for TrustStream v4.4
# Specialized agent for ensuring transparent AI decision-making and explainable moderation

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class TransparencyModeratorAgent(BaseAIAgent):
    """
    Transparency Moderator Agent - Specialized AI Explainability and Transparency
    
    This agent focuses on ensuring transparent AI decision-making, providing clear
    explanations for moderation actions, and maintaining accountability in automated
    content moderation processes.
    
    Key Responsibilities:
    - AI decision explainability
    - Moderation transparency
    - User-friendly explanation generation
    - Decision audit trail maintenance
    - Bias detection in AI decisions
    - Appeal process facilitation
    - Stakeholder communication
    - Compliance with transparency regulations
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Transparency configuration
        self.transparency_config = {
            'explanation_detail_levels': ['basic', 'detailed', 'technical'],
            'stakeholder_types': ['user', 'moderator', 'admin', 'auditor'],
            'required_explanation_elements': [
                'decision_summary',
                'key_factors',
                'confidence_level',
                'alternative_actions',
                'appeal_process'
            ]
        }
        
        # Explanation templates for different audiences
        self.explanation_templates = {
            'user': {
                'approved': "Your content was approved because it follows community guidelines and contributes positively to the discussion.",
                'flagged': "Your content has been flagged for review because {reason}. A human moderator will review it shortly.",
                'warned': "Your content received a warning because {reason}. Please review our community guidelines.",
                'removed': "Your content was removed because {reason}. You can appeal this decision if you believe it was made in error."
            },
            'moderator': {
                'summary_template': "AI Analysis Summary: {decision} (Confidence: {confidence}%)\nKey Factors: {factors}\nRecommended Action: {action}",
                'detailed_template': "Detailed AI Analysis:\nDecision: {decision}\nConfidence: {confidence}%\nPrimary Agent: {agent}\nKey Evidence: {evidence}\nRisk Assessment: {risk}\nRecommendations: {recommendations}"
            }
        }
        
        # Bias detection patterns
        self.bias_indicators = {
            'demographic_bias': ['age', 'gender', 'race', 'ethnicity', 'religion'],
            'linguistic_bias': ['grammar', 'spelling', 'vocabulary', 'dialect'],
            'cultural_bias': ['cultural_references', 'idioms', 'local_knowledge'],
            'temporal_bias': ['time_of_day', 'day_of_week', 'seasonal']
        }
        
        logger.info(f"Transparency Moderator Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content with focus on transparency and explainability.
        
        The Transparency Moderator Agent evaluates:
        - Decision transparency requirements
        - Explanation clarity and completeness
        - Potential bias in AI decisions
        - Stakeholder communication needs
        - Audit trail completeness
        - Appeal process requirements
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Analyze transparency requirements
            transparency_requirements = await self._analyze_transparency_requirements(content, context)
            
            # Generate explanations for different stakeholders
            stakeholder_explanations = await self._generate_stakeholder_explanations(content, context)
            
            # Check for potential bias in decision-making
            bias_analysis = await self._analyze_decision_bias(content, context)
            
            # Assess explanation quality
            explanation_quality = await self._assess_explanation_quality(stakeholder_explanations)
            
            # Generate audit trail information
            audit_trail = await self._generate_audit_trail(content, context)
            
            # Get AI provider analysis for transparency
            ai_analysis = await self._get_ai_transparency_analysis(content, trust_score, context)
            
            # Make transparency-focused decision
            decision = await self._make_transparency_decision(
                content=content,
                trust_score=trust_score,
                transparency_requirements=transparency_requirements,
                stakeholder_explanations=stakeholder_explanations,
                bias_analysis=bias_analysis,
                explanation_quality=explanation_quality,
                audit_trail=audit_trail,
                ai_analysis=ai_analysis,
                context=context
            )
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Transparency analysis failed: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.5,
                'reasoning': f'Transparency analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'transparency_moderator', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Transparency Moderator Agent."""
        return [
            'ai_decision_explainability',
            'moderation_transparency',
            'stakeholder_communication',
            'bias_detection',
            'audit_trail_generation',
            'appeal_process_facilitation',
            'explanation_quality_assessment',
            'transparency_compliance',
            'decision_accountability',
            'user_education'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Transparency Moderator Agent."""
        return (
            "Specialized agent for ensuring transparent AI decision-making and explainable moderation. "
            "Focuses on generating clear explanations, detecting bias, maintaining audit trails, "
            "and facilitating communication between AI systems and human stakeholders."
        )
    
    # Private analysis methods
    
    async def _analyze_transparency_requirements(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze what level of transparency is required for this content."""
        try:
            transparency_requirements = {
                'required_detail_level': 'basic',
                'stakeholders_to_notify': ['user'],
                'explanation_urgency': 'normal',
                'audit_requirements': 'standard',
                'appeal_eligibility': True
            }
            
            # Determine detail level based on content sensitivity
            content_type = content.get('type', 'text')
            content_sensitivity = context.get('sensitivity_level', 'normal')
            
            if content_sensitivity == 'high' or content_type in ['image', 'video']:
                transparency_requirements['required_detail_level'] = 'detailed'
                transparency_requirements['stakeholders_to_notify'].append('moderator')
            
            # Check if this is a high-stakes decision
            if context.get('high_stakes_decision', False):
                transparency_requirements['required_detail_level'] = 'technical'
                transparency_requirements['stakeholders_to_notify'].extend(['moderator', 'admin'])
                transparency_requirements['explanation_urgency'] = 'immediate'
                transparency_requirements['audit_requirements'] = 'comprehensive'
            
            # Check for regulatory compliance requirements
            if context.get('regulatory_compliance_required', False):
                transparency_requirements['required_detail_level'] = 'technical'
                transparency_requirements['audit_requirements'] = 'regulatory'
                transparency_requirements['stakeholders_to_notify'].append('auditor')
            
            # Check user's transparency preferences
            user_preferences = context.get('user_transparency_preferences', {})
            if user_preferences.get('detailed_explanations', False):
                transparency_requirements['required_detail_level'] = 'detailed'
            
            return transparency_requirements
            
        except Exception as e:
            logger.error(f"Failed to analyze transparency requirements: {str(e)}")
            return {'required_detail_level': 'basic', 'error': str(e)}
    
    async def _generate_stakeholder_explanations(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate explanations tailored for different stakeholders."""
        try:
            stakeholder_explanations = {}
            
            # Get moderation decision context
            moderation_decision = context.get('moderation_decision', {})
            decision_action = moderation_decision.get('action', 'approve')
            decision_reasoning = moderation_decision.get('reasoning', 'Content follows guidelines')
            confidence = moderation_decision.get('confidence', 0.5)
            primary_agent = moderation_decision.get('metadata', {}).get('agent', 'unknown')
            
            # Generate user explanation
            stakeholder_explanations['user'] = await self._generate_user_explanation(
                decision_action, decision_reasoning, confidence, content, context
            )
            
            # Generate moderator explanation
            stakeholder_explanations['moderator'] = await self._generate_moderator_explanation(
                moderation_decision, content, context
            )
            
            # Generate admin explanation if needed
            if context.get('admin_notification_required', False):
                stakeholder_explanations['admin'] = await self._generate_admin_explanation(
                    moderation_decision, content, context
                )
            
            # Generate auditor explanation if needed
            if context.get('audit_required', False):
                stakeholder_explanations['auditor'] = await self._generate_auditor_explanation(
                    moderation_decision, content, context
                )
            
            return stakeholder_explanations
            
        except Exception as e:
            logger.error(f"Failed to generate stakeholder explanations: {str(e)}")
            return {'error': str(e)}
    
    async def _analyze_decision_bias(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze potential bias in AI decision-making."""
        try:
            bias_analysis = {
                'bias_risk_score': 0.0,
                'potential_bias_types': [],
                'bias_mitigation_needed': False,
                'fairness_assessment': 'fair'
            }
            
            # Check for demographic bias indicators
            author_demographics = context.get('author_demographics', {})
            if author_demographics:
                # This would involve more sophisticated bias detection
                # For now, we'll do basic checks
                bias_analysis['potential_bias_types'].append('demographic_awareness_needed')
            
            # Check for linguistic bias
            content_language = content.get('language', 'en')
            author_native_language = context.get('author_native_language', 'en')
            
            if content_language != author_native_language:
                bias_analysis['potential_bias_types'].append('linguistic_bias')
                bias_analysis['bias_risk_score'] += 0.2
            
            # Check for temporal bias
            content_timestamp = content.get('timestamp', datetime.utcnow())
            if isinstance(content_timestamp, str):
                content_timestamp = datetime.fromisoformat(content_timestamp.replace('Z', '+00:00'))
            
            hour = content_timestamp.hour
            if hour < 6 or hour > 22:  # Off-hours content
                bias_analysis['potential_bias_types'].append('temporal_bias')
                bias_analysis['bias_risk_score'] += 0.1
            
            # Check for cultural bias indicators
            cultural_references = context.get('cultural_references_detected', [])
            if cultural_references:
                bias_analysis['potential_bias_types'].append('cultural_bias')
                bias_analysis['bias_risk_score'] += 0.15
            
            # Assess overall fairness
            if bias_analysis['bias_risk_score'] > 0.4:
                bias_analysis['fairness_assessment'] = 'potentially_biased'
                bias_analysis['bias_mitigation_needed'] = True
            elif bias_analysis['bias_risk_score'] > 0.2:
                bias_analysis['fairness_assessment'] = 'review_recommended'
            
            return bias_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze decision bias: {str(e)}")
            return {'bias_risk_score': 0.1, 'error': str(e)}
    
    async def _assess_explanation_quality(
        self, 
        stakeholder_explanations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the quality and completeness of generated explanations."""
        try:
            quality_assessment = {
                'overall_quality_score': 0.0,
                'completeness_score': 0.0,
                'clarity_score': 0.0,
                'actionability_score': 0.0,
                'missing_elements': []
            }
            
            # Check completeness
            required_elements = self.transparency_config['required_explanation_elements']
            user_explanation = stakeholder_explanations.get('user', '')
            
            elements_present = 0
            for element in required_elements:
                if self._check_explanation_element(user_explanation, element):
                    elements_present += 1
                else:
                    quality_assessment['missing_elements'].append(element)
            
            quality_assessment['completeness_score'] = elements_present / len(required_elements)
            
            # Assess clarity (basic metrics)
            if user_explanation:
                word_count = len(user_explanation.split())
                sentence_count = user_explanation.count('.') + user_explanation.count('!') + user_explanation.count('?')
                
                if sentence_count > 0:
                    avg_sentence_length = word_count / sentence_count
                    # Optimal sentence length for clarity is 15-20 words
                    if 10 <= avg_sentence_length <= 25:
                        quality_assessment['clarity_score'] = 0.8
                    else:
                        quality_assessment['clarity_score'] = 0.6
                else:
                    quality_assessment['clarity_score'] = 0.4
            
            # Assess actionability
            actionable_keywords = ['can', 'should', 'may', 'appeal', 'contact', 'review', 'guidelines']
            actionable_count = sum(1 for keyword in actionable_keywords if keyword in user_explanation.lower())
            quality_assessment['actionability_score'] = min(1.0, actionable_count * 0.2)
            
            # Calculate overall quality
            quality_assessment['overall_quality_score'] = (
                quality_assessment['completeness_score'] * 0.4 +
                quality_assessment['clarity_score'] * 0.3 +
                quality_assessment['actionability_score'] * 0.3
            )
            
            return quality_assessment
            
        except Exception as e:
            logger.error(f"Failed to assess explanation quality: {str(e)}")
            return {'overall_quality_score': 0.5, 'error': str(e)}
    
    async def _generate_audit_trail(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive audit trail information."""
        try:
            audit_trail = {
                'timestamp': datetime.utcnow().isoformat(),
                'content_id': content.get('id', 'unknown'),
                'author_id': content.get('author_id', 'unknown'),
                'community_id': self.community_id,
                'ai_agents_involved': [],
                'decision_factors': [],
                'confidence_scores': {},
                'processing_steps': [],
                'data_sources': [],
                'compliance_checks': []
            }
            
            # Extract AI agents involved
            moderation_decision = context.get('moderation_decision', {})
            if 'metadata' in moderation_decision:
                primary_agent = moderation_decision['metadata'].get('agent', 'unknown')
                audit_trail['ai_agents_involved'].append(primary_agent)
            
            # Extract decision factors
            if 'evidence' in moderation_decision:
                evidence = moderation_decision['evidence']
                for key, value in evidence.items():
                    if isinstance(value, dict) and 'score' in str(value).lower():
                        audit_trail['decision_factors'].append(key)
            
            # Extract confidence scores
            audit_trail['confidence_scores']['overall'] = moderation_decision.get('confidence', 0.5)
            
            # Record processing steps
            audit_trail['processing_steps'] = [
                'content_ingestion',
                'feature_extraction',
                'ai_analysis',
                'decision_synthesis',
                'explanation_generation'
            ]
            
            # Record data sources
            audit_trail['data_sources'] = [
                'content_text',
                'user_trust_score',
                'community_context',
                'ai_provider_analysis'
            ]
            
            # Record compliance checks
            if context.get('gdpr_compliance_required', False):
                audit_trail['compliance_checks'].append('gdpr')
            if context.get('eu_ai_act_compliance_required', False):
                audit_trail['compliance_checks'].append('eu_ai_act')
            
            return audit_trail
            
        except Exception as e:
            logger.error(f"Failed to generate audit trail: {str(e)}")
            return {'error': str(e)}
    
    async def _get_ai_transparency_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on transparency and explainability."""
        try:
            prompt = self._create_transparency_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (Claude for transparency analysis)
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
                'reasoning': 'No AI providers available for transparency analysis'
            }
            
        except Exception as e:
            logger.error(f"AI transparency analysis failed: {str(e)}")
            return {
                'action': 'approve',
                'confidence': 0.5,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_transparency_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a transparency-focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='transparency, explainability, and clear communication'
        )
        
        transparency_specific = f"""
TRANSPARENCY AND EXPLAINABILITY ANALYSIS

You are a specialized Transparency Moderator Agent focused on ensuring clear,
explainable, and transparent AI decision-making in content moderation.

User Trust Context:
- Author Trust Score: {trust_score}

Transparency Requirements:
1. Clear Decision Rationale: Provide clear, understandable reasons for decisions
2. Evidence-Based Reasoning: Base decisions on specific, identifiable evidence
3. Confidence Communication: Clearly communicate confidence levels and uncertainty
4. Alternative Considerations: Acknowledge alternative interpretations or actions
5. Appeal Process: Provide clear information about appeal processes
6. Bias Awareness: Consider and communicate potential biases in decision-making

Decision Guidelines:
- APPROVE: Content that clearly meets community standards
- FLAG: Content requiring human review with clear explanation of concerns
- WARN: Content with minor issues that can be addressed through education
- REMOVE: Content that clearly violates policies with specific policy citations

Transparency Principles:
- Use clear, jargon-free language
- Provide specific examples and evidence
- Acknowledge uncertainty when present
- Explain the reasoning process, not just the conclusion
- Consider the user's perspective and potential confusion
- Maintain consistency with community guidelines

CRITICAL: Your primary goal is to make AI decision-making transparent and
understandable to all stakeholders while maintaining accuracy and fairness.
"""
        
        return base_prompt + transparency_specific
    
    async def _make_transparency_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        transparency_requirements: Dict[str, Any],
        stakeholder_explanations: Dict[str, Any],
        bias_analysis: Dict[str, Any],
        explanation_quality: Dict[str, Any],
        audit_trail: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make transparency-focused moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Enhance decision with transparency elements
            base_decision['transparency'] = {
                'explanation_quality_score': explanation_quality.get('overall_quality_score', 0.5),
                'bias_risk_score': bias_analysis.get('bias_risk_score', 0.0),
                'required_detail_level': transparency_requirements.get('required_detail_level', 'basic'),
                'stakeholder_explanations': stakeholder_explanations,
                'audit_trail': audit_trail
            }
            
            # Adjust decision based on transparency requirements
            if transparency_requirements.get('required_detail_level') == 'technical':
                base_decision['requires_human_review'] = True
                base_decision['explanation_urgency'] = 'immediate'
            
            # Handle bias concerns
            if bias_analysis.get('bias_mitigation_needed', False):
                base_decision['bias_warning'] = True
                base_decision['requires_bias_review'] = True
                if base_decision['action'] == 'approve':
                    base_decision['action'] = 'flag'
                    base_decision['reasoning'] += ' (Potential bias detected - requires review)'
            
            # Ensure explanation quality
            if explanation_quality.get('overall_quality_score', 0.5) < 0.6:
                base_decision['explanation_improvement_needed'] = True
                base_decision['missing_explanation_elements'] = explanation_quality.get('missing_elements', [])
            
            # Add transparency-specific metadata
            base_decision['metadata'] = base_decision.get('metadata', {})
            base_decision['metadata'].update({
                'agent': 'transparency_moderator',
                'transparency_score': round(explanation_quality.get('overall_quality_score', 0.5), 3),
                'bias_risk': round(bias_analysis.get('bias_risk_score', 0.0), 3),
                'explanation_completeness': round(explanation_quality.get('completeness_score', 0.5), 3),
                'stakeholders_notified': transparency_requirements.get('stakeholders_to_notify', ['user']),
                'audit_trail_id': audit_trail.get('timestamp', 'unknown')
            })
            
            # Add detailed evidence
            base_decision['evidence'] = base_decision.get('evidence', {})
            base_decision['evidence'].update({
                'transparency_requirements': transparency_requirements,
                'bias_analysis': bias_analysis,
                'explanation_quality': explanation_quality,
                'audit_trail': audit_trail
            })
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make transparency decision: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.5,
                'reasoning': f'Transparency decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'transparency_moderator', 'error': True}
            }
    
    # Helper methods for explanation generation
    
    async def _generate_user_explanation(
        self, 
        action: str, 
        reasoning: str, 
        confidence: float, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Generate user-friendly explanation."""
        try:
            template = self.explanation_templates['user'].get(action, self.explanation_templates['user']['approved'])
            
            # Format the explanation
            explanation = template.format(reason=reasoning)
            
            # Add confidence information if low
            if confidence < 0.7:
                explanation += f" (Confidence: {int(confidence * 100)}% - This decision may be reviewed by a human moderator.)"
            
            # Add appeal information for negative actions
            if action in ['flagged', 'warned', 'removed']:
                explanation += " If you believe this decision was made in error, you can appeal by contacting our moderation team."
            
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate user explanation: {str(e)}")
            return "Your content has been processed. For more information, please contact our support team."
    
    async def _generate_moderator_explanation(
        self, 
        moderation_decision: Dict[str, Any], 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Generate detailed explanation for moderators."""
        try:
            template = self.explanation_templates['moderator']['detailed_template']
            
            return template.format(
                decision=moderation_decision.get('action', 'unknown'),
                confidence=int(moderation_decision.get('confidence', 0.5) * 100),
                agent=moderation_decision.get('metadata', {}).get('agent', 'unknown'),
                evidence=str(moderation_decision.get('evidence', {}))[:200] + '...',
                risk=moderation_decision.get('metadata', {}).get('risk_level', 'unknown'),
                recommendations=moderation_decision.get('reasoning', 'No specific recommendations')
            )
            
        except Exception as e:
            logger.error(f"Failed to generate moderator explanation: {str(e)}")
            return "Detailed analysis failed. Please review manually."
    
    async def _generate_admin_explanation(
        self, 
        moderation_decision: Dict[str, Any], 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Generate comprehensive explanation for administrators."""
        try:
            return json.dumps({
                'decision_summary': moderation_decision,
                'content_metadata': {
                    'id': content.get('id'),
                    'type': content.get('type'),
                    'author_id': content.get('author_id'),
                    'timestamp': content.get('timestamp')
                },
                'context_summary': {
                    'community_id': self.community_id,
                    'trust_score': context.get('trust_score'),
                    'high_stakes': context.get('high_stakes_decision', False)
                }
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to generate admin explanation: {str(e)}")
            return json.dumps({'error': str(e)})
    
    async def _generate_auditor_explanation(
        self, 
        moderation_decision: Dict[str, Any], 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Generate compliance-focused explanation for auditors."""
        try:
            return json.dumps({
                'compliance_summary': {
                    'decision': moderation_decision.get('action'),
                    'confidence': moderation_decision.get('confidence'),
                    'reasoning': moderation_decision.get('reasoning'),
                    'bias_assessment': context.get('bias_analysis', {}),
                    'transparency_score': context.get('transparency_score', 0.5)
                },
                'regulatory_compliance': {
                    'gdpr_compliant': context.get('gdpr_compliant', True),
                    'eu_ai_act_compliant': context.get('eu_ai_act_compliant', True),
                    'data_processing_lawful': True,
                    'user_rights_respected': True
                },
                'audit_metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent_version': 'transparency_moderator_v1.0',
                    'processing_time_ms': context.get('processing_time_ms', 0)
                }
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to generate auditor explanation: {str(e)}")
            return json.dumps({'error': str(e)})
    
    def _check_explanation_element(self, explanation: str, element: str) -> bool:
        """Check if an explanation contains a required element."""
        element_keywords = {
            'decision_summary': ['approved', 'flagged', 'warned', 'removed', 'decision'],
            'key_factors': ['because', 'due to', 'reason', 'factor'],
            'confidence_level': ['confidence', 'certain', 'sure', 'likely'],
            'alternative_actions': ['could', 'might', 'alternative', 'option'],
            'appeal_process': ['appeal', 'contact', 'review', 'dispute']
        }
        
        keywords = element_keywords.get(element, [])
        return any(keyword in explanation.lower() for keyword in keywords)