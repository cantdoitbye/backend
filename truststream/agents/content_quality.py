# Content Quality Agent for TrustStream v4.4
# Specialized agent for analyzing content quality, relevance, and community value

import logging
import json
import re
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class ContentQualityAgent(BaseAIAgent):
    """
    Content Quality Agent - Specialized Quality Assessment
    
    This agent focuses on evaluating content quality, relevance, and value
    to the community. It helps maintain high standards of discourse and
    filters out low-quality or spam content.
    
    Key Responsibilities:
    - Content quality assessment
    - Relevance to community topics
    - Educational and informational value
    - Spam and low-effort content detection
    - Constructive contribution evaluation
    - Content depth and substance analysis
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        super().__init__(config, community_id, community_analysis)
        
        # Content Quality specific configuration
        self.quality_thresholds = {
            'minimum_word_count': 10,
            'maximum_repetition_ratio': 0.3,
            'minimum_readability_score': 0.4,
            'spam_keyword_threshold': 3
        }
        
        # Quality indicators
        self.positive_indicators = [
            'question', 'explain', 'understand', 'learn', 'help', 'share',
            'experience', 'insight', 'analysis', 'discussion', 'feedback',
            'suggestion', 'improvement', 'solution', 'research', 'study'
        ]
        
        self.negative_indicators = [
            'spam', 'click here', 'buy now', 'limited time', 'act fast',
            'guaranteed', 'free money', 'get rich', 'lose weight fast',
            'miracle cure', 'secret method', 'exclusive offer'
        ]
        
        logger.info(f"Content Quality Agent initialized for community {community_id}")
    
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content quality and provide quality-focused moderation decision.
        
        The Content Quality Agent evaluates:
        - Writing quality and coherence
        - Relevance to community
        - Educational or informational value
        - Spam and low-effort detection
        - Constructive contribution potential
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract content features
            content_features = self._extract_content_features(content)
            
            # Perform quality analysis
            quality_metrics = await self._analyze_content_quality(content, content_features)
            
            # Check for spam indicators
            spam_analysis = await self._analyze_spam_indicators(content, content_features)
            
            # Assess educational value
            educational_value = await self._assess_educational_value(content, content_features)
            
            # Analyze relevance to community
            relevance_score = await self._analyze_community_relevance(content, context)
            
            # Get AI provider analysis
            ai_analysis = await self._get_ai_quality_analysis(content, trust_score, context)
            
            # Make final quality decision
            decision = await self._make_quality_decision(
                content=content,
                trust_score=trust_score,
                quality_metrics=quality_metrics,
                spam_analysis=spam_analysis,
                educational_value=educational_value,
                relevance_score=relevance_score,
                ai_analysis=ai_analysis
            )
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.log_decision(content, decision, processing_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"Content Quality analysis failed: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.4,
                'reasoning': f'Quality analysis failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'content_quality', 'error': True}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of the Content Quality Agent."""
        return [
            'content_quality_assessment',
            'spam_detection',
            'educational_value_analysis',
            'community_relevance_scoring',
            'readability_analysis',
            'constructive_contribution_evaluation',
            'low_effort_content_detection',
            'content_depth_analysis',
            'writing_quality_assessment',
            'topic_relevance_matching'
        ]
    
    def get_description(self) -> str:
        """Return a description of the Content Quality Agent."""
        return (
            "Specialized agent for analyzing content quality, relevance, and community value. "
            "Evaluates writing quality, educational value, spam indicators, and constructive "
            "contribution potential to maintain high community discourse standards."
        )
    
    # Private analysis methods
    
    async def _analyze_content_quality(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze overall content quality metrics."""
        try:
            text_content = content.get('content', '')
            quality_metrics = {
                'word_count_score': 0.5,
                'readability_score': 0.5,
                'coherence_score': 0.5,
                'grammar_score': 0.5,
                'overall_quality': 0.5
            }
            
            # Word count analysis
            word_count = content_features.get('word_count', 0)
            if word_count < self.quality_thresholds['minimum_word_count']:
                quality_metrics['word_count_score'] = 0.2
            elif word_count > 50:
                quality_metrics['word_count_score'] = min(1.0, word_count / 200)
            else:
                quality_metrics['word_count_score'] = word_count / 50
            
            # Readability analysis
            quality_metrics['readability_score'] = self._calculate_readability_score(text_content)
            
            # Coherence analysis
            quality_metrics['coherence_score'] = self._analyze_coherence(text_content)
            
            # Grammar and spelling analysis
            quality_metrics['grammar_score'] = self._analyze_grammar_quality(text_content)
            
            # Calculate overall quality
            quality_metrics['overall_quality'] = (
                quality_metrics['word_count_score'] * 0.2 +
                quality_metrics['readability_score'] * 0.3 +
                quality_metrics['coherence_score'] * 0.3 +
                quality_metrics['grammar_score'] * 0.2
            )
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze content quality: {str(e)}")
            return {'overall_quality': 0.5, 'error': str(e)}
    
    async def _analyze_spam_indicators(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content for spam indicators."""
        try:
            text_content = content.get('content', '').lower()
            spam_analysis = {
                'spam_keywords_count': 0,
                'repetition_ratio': 0.0,
                'link_density': 0.0,
                'caps_ratio': 0.0,
                'spam_probability': 0.0
            }
            
            # Count spam keywords
            spam_keywords_found = [keyword for keyword in self.negative_indicators if keyword in text_content]
            spam_analysis['spam_keywords_count'] = len(spam_keywords_found)
            
            # Calculate repetition ratio
            words = text_content.split()
            if words:
                unique_words = set(words)
                spam_analysis['repetition_ratio'] = 1 - (len(unique_words) / len(words))
            
            # Calculate link density
            link_count = text_content.count('http') + text_content.count('www.')
            if content_features.get('word_count', 0) > 0:
                spam_analysis['link_density'] = link_count / content_features['word_count']
            
            # Calculate caps ratio
            original_content = content.get('content', '')
            if original_content:
                caps_count = sum(1 for c in original_content if c.isupper())
                spam_analysis['caps_ratio'] = caps_count / len(original_content)
            
            # Calculate overall spam probability
            spam_score = 0
            if spam_analysis['spam_keywords_count'] > self.quality_thresholds['spam_keyword_threshold']:
                spam_score += 0.4
            if spam_analysis['repetition_ratio'] > self.quality_thresholds['maximum_repetition_ratio']:
                spam_score += 0.3
            if spam_analysis['link_density'] > 0.1:
                spam_score += 0.2
            if spam_analysis['caps_ratio'] > 0.3:
                spam_score += 0.1
            
            spam_analysis['spam_probability'] = min(1.0, spam_score)
            spam_analysis['spam_keywords_found'] = spam_keywords_found
            
            return spam_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze spam indicators: {str(e)}")
            return {'spam_probability': 0.3, 'error': str(e)}
    
    async def _assess_educational_value(
        self, 
        content: Dict[str, Any], 
        content_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the educational and informational value of content."""
        try:
            text_content = content.get('content', '').lower()
            educational_analysis = {
                'educational_keywords_count': 0,
                'question_indicators': 0,
                'knowledge_sharing_indicators': 0,
                'educational_value_score': 0.0
            }
            
            # Count educational keywords
            educational_keywords_found = [keyword for keyword in self.positive_indicators if keyword in text_content]
            educational_analysis['educational_keywords_count'] = len(educational_keywords_found)
            
            # Count question indicators
            question_patterns = ['?', 'how', 'what', 'why', 'when', 'where', 'which', 'who']
            educational_analysis['question_indicators'] = sum(
                text_content.count(pattern) for pattern in question_patterns
            )
            
            # Count knowledge sharing indicators
            sharing_patterns = ['share', 'explain', 'teach', 'show', 'demonstrate', 'example']
            educational_analysis['knowledge_sharing_indicators'] = sum(
                1 for pattern in sharing_patterns if pattern in text_content
            )
            
            # Calculate educational value score
            score = 0
            if educational_analysis['educational_keywords_count'] > 0:
                score += min(0.4, educational_analysis['educational_keywords_count'] * 0.1)
            if educational_analysis['question_indicators'] > 0:
                score += min(0.3, educational_analysis['question_indicators'] * 0.1)
            if educational_analysis['knowledge_sharing_indicators'] > 0:
                score += min(0.3, educational_analysis['knowledge_sharing_indicators'] * 0.15)
            
            educational_analysis['educational_value_score'] = min(1.0, score)
            educational_analysis['educational_keywords_found'] = educational_keywords_found
            
            return educational_analysis
            
        except Exception as e:
            logger.error(f"Failed to assess educational value: {str(e)}")
            return {'educational_value_score': 0.3, 'error': str(e)}
    
    async def _analyze_community_relevance(
        self, 
        content: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """Analyze how relevant the content is to the community."""
        try:
            # This would analyze content against community topics and interests
            # For now, return a basic relevance score based on content characteristics
            
            text_content = content.get('content', '').lower()
            community_topics = self.community_analysis.get('primary_topics', [])
            
            relevance_score = 0.5  # Default neutral relevance
            
            # Check for topic alignment
            if community_topics:
                topic_matches = sum(1 for topic in community_topics if topic.lower() in text_content)
                relevance_score += min(0.3, topic_matches * 0.1)
            
            # Check for community-specific language
            community_language = self.community_analysis.get('primary_language', 'en')
            content_language = content.get('language', 'en')
            if community_language == content_language:
                relevance_score += 0.1
            
            # Check for constructive discussion indicators
            discussion_indicators = ['discuss', 'opinion', 'thoughts', 'feedback', 'community']
            if any(indicator in text_content for indicator in discussion_indicators):
                relevance_score += 0.1
            
            return min(1.0, relevance_score)
            
        except Exception as e:
            logger.error(f"Failed to analyze community relevance: {str(e)}")
            return 0.5
    
    async def _get_ai_quality_analysis(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI provider analysis focused on content quality."""
        try:
            prompt = self._create_quality_prompt(content, trust_score, context)
            content_text = content.get('content', '')
            
            # Try primary AI provider (OpenAI for quality analysis)
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
                'confidence': 0.3,
                'reasoning': 'No AI providers available for quality analysis'
            }
            
        except Exception as e:
            logger.error(f"AI quality analysis failed: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.3,
                'reasoning': f'AI analysis failed: {str(e)}'
            }
    
    def _create_quality_prompt(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> str:
        """Create a quality-focused analysis prompt."""
        base_prompt = self._create_base_prompt(
            content_type=content.get('type', 'text'),
            analysis_focus='content quality and community value'
        )
        
        quality_specific = f"""
CONTENT QUALITY ANALYSIS

You are a specialized Content Quality Agent focused on evaluating content quality,
relevance, and value to the community.

User Trust Context:
- Author Trust Score: {trust_score}

Quality Assessment Criteria:
1. Writing Quality: Grammar, spelling, coherence, readability
2. Content Depth: Substance, thoughtfulness, effort invested
3. Educational Value: Learning potential, knowledge sharing
4. Community Relevance: Alignment with community topics and interests
5. Constructive Contribution: Potential to generate meaningful discussion
6. Spam Detection: Commercial intent, repetitive content, low-effort posts

Decision Guidelines:
- APPROVE: High-quality, relevant, constructive content
- FLAG: Questionable quality that needs human review
- WARN: Low quality but not harmful, user education opportunity
- REMOVE: Spam, extremely low quality, or completely irrelevant

Quality Thresholds:
- Minimum word count for substantial posts: {self.quality_thresholds['minimum_word_count']}
- Maximum acceptable repetition ratio: {self.quality_thresholds['maximum_repetition_ratio']}
- Spam keyword threshold: {self.quality_thresholds['spam_keyword_threshold']}

Focus on maintaining high discourse standards while being fair to users
with different writing abilities and backgrounds.
"""
        
        return base_prompt + quality_specific
    
    async def _make_quality_decision(
        self,
        content: Dict[str, Any],
        trust_score: float,
        quality_metrics: Dict[str, Any],
        spam_analysis: Dict[str, Any],
        educational_value: Dict[str, Any],
        relevance_score: float,
        ai_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make final quality-based moderation decision."""
        try:
            # Start with AI analysis if available
            if ai_analysis and 'action' in ai_analysis:
                base_decision = ai_analysis.copy()
            else:
                base_decision = {'action': 'approve', 'confidence': 0.5, 'reasoning': 'Default approval'}
            
            # Adjust based on quality metrics
            overall_quality = quality_metrics.get('overall_quality', 0.5)
            spam_probability = spam_analysis.get('spam_probability', 0.0)
            educational_score = educational_value.get('educational_value_score', 0.0)
            
            # Quality-based adjustments
            if spam_probability > 0.7:
                base_decision['action'] = 'remove'
                base_decision['confidence'] = 0.9
                base_decision['reasoning'] = 'High spam probability detected'
            elif spam_probability > 0.4:
                base_decision['action'] = 'flag'
                base_decision['confidence'] = 0.7
                base_decision['reasoning'] = 'Potential spam content requires review'
            elif overall_quality < 0.3:
                if trust_score > 0.7:
                    base_decision['action'] = 'warn'
                    base_decision['reasoning'] = 'Low quality content from trusted user - education opportunity'
                else:
                    base_decision['action'] = 'flag'
                    base_decision['reasoning'] = 'Low quality content requires review'
            elif overall_quality > 0.8 and educational_score > 0.6:
                base_decision['action'] = 'approve'
                base_decision['confidence'] = min(1.0, base_decision.get('confidence', 0.5) + 0.2)
                base_decision['reasoning'] = 'High quality educational content'
            
            # Relevance adjustments
            if relevance_score < 0.3:
                if base_decision['action'] == 'approve':
                    base_decision['action'] = 'flag'
                    base_decision['reasoning'] += ' (Low community relevance)'
            
            # Add quality-specific metadata
            base_decision['metadata'] = {
                'agent': 'content_quality',
                'quality_score': round(overall_quality, 3),
                'spam_probability': round(spam_probability, 3),
                'educational_value': round(educational_score, 3),
                'relevance_score': round(relevance_score, 3),
                'trust_score': trust_score
            }
            
            # Add detailed evidence
            base_decision['evidence'] = {
                'quality_metrics': quality_metrics,
                'spam_analysis': spam_analysis,
                'educational_value': educational_value,
                'relevance_score': relevance_score,
                'ai_analysis': ai_analysis
            }
            
            return base_decision
            
        except Exception as e:
            logger.error(f"Failed to make quality decision: {str(e)}")
            return {
                'action': 'flag',
                'confidence': 0.4,
                'reasoning': f'Quality decision making failed: {str(e)}',
                'evidence': {'error': str(e)},
                'metadata': {'agent': 'content_quality', 'error': True}
            }
    
    # Helper methods for quality analysis
    
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate a simple readability score."""
        if not text:
            return 0.0
        
        try:
            sentences = len(re.split(r'[.!?]+', text))
            words = len(text.split())
            
            if sentences == 0 or words == 0:
                return 0.0
            
            # Simple readability metric (lower is better, normalize to 0-1)
            avg_sentence_length = words / sentences
            
            # Optimal sentence length is around 15-20 words
            if 10 <= avg_sentence_length <= 25:
                return 0.8
            elif 5 <= avg_sentence_length <= 35:
                return 0.6
            else:
                return 0.4
                
        except Exception:
            return 0.5
    
    def _analyze_coherence(self, text: str) -> float:
        """Analyze text coherence and flow."""
        if not text:
            return 0.0
        
        try:
            # Simple coherence indicators
            coherence_score = 0.5
            
            # Check for transition words
            transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'additionally', 
                             'consequently', 'meanwhile', 'similarly', 'in contrast', 'for example']
            
            text_lower = text.lower()
            transition_count = sum(1 for word in transition_words if word in text_lower)
            
            if transition_count > 0:
                coherence_score += min(0.3, transition_count * 0.1)
            
            # Check for logical structure (paragraphs, lists)
            if '\n' in text or text.count('.') > 2:
                coherence_score += 0.2
            
            return min(1.0, coherence_score)
            
        except Exception:
            return 0.5
    
    def _analyze_grammar_quality(self, text: str) -> float:
        """Analyze grammar and spelling quality."""
        if not text:
            return 0.0
        
        try:
            # Simple grammar quality indicators
            grammar_score = 0.7  # Start with decent score
            
            # Check for basic punctuation
            if not any(punct in text for punct in '.!?'):
                grammar_score -= 0.2
            
            # Check for excessive punctuation
            punct_ratio = sum(1 for c in text if c in '!?.,;:') / len(text) if text else 0
            if punct_ratio > 0.1:
                grammar_score -= 0.1
            
            # Check for proper capitalization
            sentences = re.split(r'[.!?]+', text)
            capitalized_sentences = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
            if sentences and capitalized_sentences / len(sentences) < 0.5:
                grammar_score -= 0.2
            
            return max(0.0, min(1.0, grammar_score))
            
        except Exception:
            return 0.5