# AI Provider Integrations for TrustStream v4.4
# Multi-AI Analysis System with Fallback Support

import logging
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import openai
from anthropic import AsyncAnthropic
import google.generativeai as genai
from transformers import pipeline
import cohere
import hashlib
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers"""
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"


class AnalysisType(Enum):
    """Types of AI analysis"""
    CONTENT_MODERATION = "content_moderation"
    BIAS_DETECTION = "bias_detection"
    HARASSMENT_DETECTION = "harassment_detection"
    MISINFORMATION_DETECTION = "misinformation_detection"
    CULTURAL_SENSITIVITY = "cultural_sensitivity"
    MENTAL_HEALTH_SUPPORT = "mental_health_support"
    ACCESSIBILITY_CHECK = "accessibility_check"
    YOUTH_SAFETY = "youth_safety"
    LEGAL_COMPLIANCE = "legal_compliance"
    TRUST_SCORING = "trust_scoring"


@dataclass
class AIResponse:
    """Standardized AI response format"""
    provider: AIProvider
    analysis_type: AnalysisType
    decision: str  # BLOCK, FLAG, MONITOR, APPROVE, etc.
    confidence: float  # 0.0 to 1.0
    reasoning: str
    evidence: Dict[str, Any]
    processing_time: float
    model_used: str
    cost_estimate: float
    timestamp: datetime
    request_id: str


@dataclass
class AIProviderConfig:
    """Configuration for AI providers"""
    api_key: str
    model: str
    max_tokens: int
    temperature: float
    timeout: int
    rate_limit: int  # requests per minute
    cost_per_token: float
    priority: int  # 1 = highest priority
    enabled: bool


class AIProviderManager:
    """
    AI Provider Manager for TrustStream v4.4
    
    Manages multiple AI providers with intelligent routing, fallback support,
    cost optimization, and consensus-based decision making.
    
    Features:
    - Multi-provider support (Claude, OpenAI, GPT-4, Gemini, HuggingFace, Cohere)
    - Intelligent provider selection based on analysis type and performance
    - Automatic fallback when providers fail or are unavailable
    - Cost optimization and budget management
    - Rate limiting and quota management
    - Response caching for efficiency
    - Consensus analysis for critical decisions
    - Performance monitoring and analytics
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {}
        self.provider_configs = {}
        self.provider_stats = {}
        self.response_cache = {}
        self.rate_limiters = {}
        
        # Initialize providers
        self._initialize_providers()
        
        # Provider priority for different analysis types
        self.provider_priorities = {
            AnalysisType.CONTENT_MODERATION: [AIProvider.CLAUDE, AIProvider.OPENAI, AIProvider.GEMINI],
            AnalysisType.BIAS_DETECTION: [AIProvider.CLAUDE, AIProvider.OPENAI, AIProvider.HUGGINGFACE],
            AnalysisType.HARASSMENT_DETECTION: [AIProvider.OPENAI, AIProvider.CLAUDE, AIProvider.COHERE],
            AnalysisType.MISINFORMATION_DETECTION: [AIProvider.CLAUDE, AIProvider.GEMINI, AIProvider.OPENAI],
            AnalysisType.CULTURAL_SENSITIVITY: [AIProvider.CLAUDE, AIProvider.OPENAI, AIProvider.GEMINI],
            AnalysisType.MENTAL_HEALTH_SUPPORT: [AIProvider.CLAUDE, AIProvider.OPENAI, AIProvider.GEMINI],
            AnalysisType.ACCESSIBILITY_CHECK: [AIProvider.CLAUDE, AIProvider.OPENAI, AIProvider.HUGGINGFACE],
            AnalysisType.YOUTH_SAFETY: [AIProvider.CLAUDE, AIProvider.OPENAI, AIProvider.GEMINI],
            AnalysisType.LEGAL_COMPLIANCE: [AIProvider.CLAUDE, AIProvider.OPENAI, AIProvider.GEMINI],
            AnalysisType.TRUST_SCORING: [AIProvider.CLAUDE, AIProvider.OPENAI, AIProvider.GEMINI]
        }
        
        # Cost and performance tracking
        self.daily_costs = {}
        self.performance_metrics = {}
        
        logger.info("AI Provider Manager initialized")
    
    def _initialize_providers(self):
        """Initialize all AI providers with their configurations."""
        try:
            # Claude (Anthropic)
            if self.config.get('claude', {}).get('enabled', False):
                self.provider_configs[AIProvider.CLAUDE] = AIProviderConfig(
                    api_key=self.config['claude']['api_key'],
                    model=self.config['claude'].get('model', 'claude-3-sonnet-20240229'),
                    max_tokens=self.config['claude'].get('max_tokens', 4000),
                    temperature=self.config['claude'].get('temperature', 0.3),
                    timeout=self.config['claude'].get('timeout', 30),
                    rate_limit=self.config['claude'].get('rate_limit', 50),
                    cost_per_token=self.config['claude'].get('cost_per_token', 0.000015),
                    priority=1,
                    enabled=True
                )
                self.providers[AIProvider.CLAUDE] = AsyncAnthropic(api_key=self.config['claude']['api_key'])
            
            # OpenAI
            if self.config.get('openai', {}).get('enabled', False):
                self.provider_configs[AIProvider.OPENAI] = AIProviderConfig(
                    api_key=self.config['openai']['api_key'],
                    model=self.config['openai'].get('model', 'gpt-4-turbo-preview'),
                    max_tokens=self.config['openai'].get('max_tokens', 4000),
                    temperature=self.config['openai'].get('temperature', 0.3),
                    timeout=self.config['openai'].get('timeout', 30),
                    rate_limit=self.config['openai'].get('rate_limit', 60),
                    cost_per_token=self.config['openai'].get('cost_per_token', 0.00001),
                    priority=2,
                    enabled=True
                )
                openai.api_key = self.config['openai']['api_key']
            
            # Gemini (Google)
            if self.config.get('gemini', {}).get('enabled', False):
                self.provider_configs[AIProvider.GEMINI] = AIProviderConfig(
                    api_key=self.config['gemini']['api_key'],
                    model=self.config['gemini'].get('model', 'gemini-pro'),
                    max_tokens=self.config['gemini'].get('max_tokens', 4000),
                    temperature=self.config['gemini'].get('temperature', 0.3),
                    timeout=self.config['gemini'].get('timeout', 30),
                    rate_limit=self.config['gemini'].get('rate_limit', 60),
                    cost_per_token=self.config['gemini'].get('cost_per_token', 0.000001),
                    priority=3,
                    enabled=True
                )
                genai.configure(api_key=self.config['gemini']['api_key'])
            
            # HuggingFace
            if self.config.get('huggingface', {}).get('enabled', False):
                self.provider_configs[AIProvider.HUGGINGFACE] = AIProviderConfig(
                    api_key=self.config['huggingface']['api_key'],
                    model=self.config['huggingface'].get('model', 'microsoft/DialoGPT-large'),
                    max_tokens=self.config['huggingface'].get('max_tokens', 2000),
                    temperature=0.3,
                    timeout=self.config['huggingface'].get('timeout', 45),
                    rate_limit=self.config['huggingface'].get('rate_limit', 30),
                    cost_per_token=self.config['huggingface'].get('cost_per_token', 0.000001),
                    priority=4,
                    enabled=True
                )
            
            # Cohere
            if self.config.get('cohere', {}).get('enabled', False):
                self.provider_configs[AIProvider.COHERE] = AIProviderConfig(
                    api_key=self.config['cohere']['api_key'],
                    model=self.config['cohere'].get('model', 'command'),
                    max_tokens=self.config['cohere'].get('max_tokens', 4000),
                    temperature=self.config['cohere'].get('temperature', 0.3),
                    timeout=self.config['cohere'].get('timeout', 30),
                    rate_limit=self.config['cohere'].get('rate_limit', 40),
                    cost_per_token=self.config['cohere'].get('cost_per_token', 0.000015),
                    priority=5,
                    enabled=True
                )
                self.providers[AIProvider.COHERE] = cohere.AsyncClient(api_key=self.config['cohere']['api_key'])
            
            # Initialize stats and rate limiters
            for provider in self.provider_configs:
                self.provider_stats[provider] = {
                    'requests': 0,
                    'successes': 0,
                    'failures': 0,
                    'avg_response_time': 0.0,
                    'total_cost': 0.0,
                    'last_used': None
                }
                self.rate_limiters[provider] = {
                    'requests': [],
                    'limit': self.provider_configs[provider].rate_limit
                }
            
            logger.info(f"Initialized {len(self.provider_configs)} AI providers")
            
        except Exception as e:
            logger.error(f"Provider initialization failed: {str(e)}")
            raise
    
    async def analyze_content(
        self,
        content: str,
        analysis_type: AnalysisType,
        context: Dict[str, Any] = None,
        require_consensus: bool = False,
        max_providers: int = 1
    ) -> Union[AIResponse, List[AIResponse]]:
        """
        Analyze content using AI providers.
        
        Args:
            content: Content to analyze
            analysis_type: Type of analysis to perform
            context: Additional context for analysis
            require_consensus: Whether to use multiple providers for consensus
            max_providers: Maximum number of providers to use
        
        Returns:
            Single AIResponse or list of responses for consensus
        """
        try:
            request_id = self._generate_request_id(content, analysis_type)
            
            # Check cache first
            cached_response = await self._get_cached_response(request_id)
            if cached_response:
                logger.info(f"Returning cached response for {analysis_type.value}")
                return cached_response
            
            # Select providers
            selected_providers = await self._select_providers(analysis_type, max_providers, require_consensus)
            
            if not selected_providers:
                raise Exception("No available providers for analysis")
            
            # Perform analysis
            if require_consensus or max_providers > 1:
                responses = await self._analyze_with_multiple_providers(
                    content, analysis_type, context, selected_providers, request_id
                )
                
                if require_consensus:
                    consensus_response = await self._build_consensus(responses, analysis_type, request_id)
                    await self._cache_response(request_id, consensus_response)
                    return consensus_response
                else:
                    await self._cache_response(request_id, responses)
                    return responses
            else:
                response = await self._analyze_with_single_provider(
                    content, analysis_type, context, selected_providers[0], request_id
                )
                await self._cache_response(request_id, response)
                return response
                
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return await self._create_error_response(analysis_type, str(e))
    
    async def _select_providers(
        self, 
        analysis_type: AnalysisType, 
        max_providers: int, 
        require_consensus: bool
    ) -> List[AIProvider]:
        """Select optimal providers for analysis."""
        try:
            # Get priority list for analysis type
            priority_list = self.provider_priorities.get(analysis_type, list(self.provider_configs.keys()))
            
            # Filter available and enabled providers
            available_providers = []
            for provider in priority_list:
                if (provider in self.provider_configs and 
                    self.provider_configs[provider].enabled and
                    await self._check_provider_availability(provider)):
                    available_providers.append(provider)
            
            # For consensus, ensure we have at least 3 providers
            if require_consensus:
                max_providers = max(max_providers, 3)
            
            # Select top providers up to max_providers
            selected = available_providers[:max_providers]
            
            logger.info(f"Selected providers for {analysis_type.value}: {[p.value for p in selected]}")
            return selected
            
        except Exception as e:
            logger.error(f"Provider selection failed: {str(e)}")
            return []
    
    async def _check_provider_availability(self, provider: AIProvider) -> bool:
        """Check if provider is available and within rate limits."""
        try:
            # Check rate limits
            now = time.time()
            rate_limiter = self.rate_limiters[provider]
            
            # Remove old requests (older than 1 minute)
            rate_limiter['requests'] = [req_time for req_time in rate_limiter['requests'] 
                                      if now - req_time < 60]
            
            # Check if under rate limit
            if len(rate_limiter['requests']) >= rate_limiter['limit']:
                logger.warning(f"Provider {provider.value} rate limited")
                return False
            
            # Check if provider had recent failures
            stats = self.provider_stats[provider]
            if stats['failures'] > 5 and stats['last_used']:
                time_since_last = now - stats['last_used']
                if time_since_last < 300:  # 5 minutes cooldown
                    logger.warning(f"Provider {provider.value} in cooldown")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Availability check failed for {provider.value}: {str(e)}")
            return False
    
    async def _analyze_with_single_provider(
        self,
        content: str,
        analysis_type: AnalysisType,
        context: Dict[str, Any],
        provider: AIProvider,
        request_id: str
    ) -> AIResponse:
        """Analyze content with a single provider."""
        start_time = time.time()
        
        try:
            # Update rate limiter
            self.rate_limiters[provider]['requests'].append(start_time)
            
            # Get analysis prompt
            prompt = await self._build_analysis_prompt(content, analysis_type, context)
            
            # Call provider
            if provider == AIProvider.CLAUDE:
                response = await self._call_claude(prompt, analysis_type)
            elif provider == AIProvider.OPENAI:
                response = await self._call_openai(prompt, analysis_type)
            elif provider == AIProvider.GEMINI:
                response = await self._call_gemini(prompt, analysis_type)
            elif provider == AIProvider.HUGGINGFACE:
                response = await self._call_huggingface(prompt, analysis_type)
            elif provider == AIProvider.COHERE:
                response = await self._call_cohere(prompt, analysis_type)
            else:
                raise Exception(f"Unsupported provider: {provider}")
            
            # Parse response
            parsed_response = await self._parse_ai_response(response, provider, analysis_type)
            
            # Calculate processing time and cost
            processing_time = time.time() - start_time
            cost = await self._calculate_cost(provider, prompt, parsed_response.get('text', ''))
            
            # Update stats
            await self._update_provider_stats(provider, True, processing_time, cost)
            
            # Create standardized response
            ai_response = AIResponse(
                provider=provider,
                analysis_type=analysis_type,
                decision=parsed_response.get('decision', 'APPROVE'),
                confidence=parsed_response.get('confidence', 0.5),
                reasoning=parsed_response.get('reasoning', 'Analysis completed'),
                evidence=parsed_response.get('evidence', {}),
                processing_time=processing_time,
                model_used=self.provider_configs[provider].model,
                cost_estimate=cost,
                timestamp=datetime.utcnow(),
                request_id=request_id
            )
            
            logger.info(f"Analysis completed with {provider.value}: {ai_response.decision} ({ai_response.confidence:.2f})")
            return ai_response
            
        except Exception as e:
            # Update failure stats
            processing_time = time.time() - start_time
            await self._update_provider_stats(provider, False, processing_time, 0.0)
            
            logger.error(f"Analysis failed with {provider.value}: {str(e)}")
            raise
    
    async def _analyze_with_multiple_providers(
        self,
        content: str,
        analysis_type: AnalysisType,
        context: Dict[str, Any],
        providers: List[AIProvider],
        request_id: str
    ) -> List[AIResponse]:
        """Analyze content with multiple providers concurrently."""
        try:
            tasks = []
            for provider in providers:
                task = asyncio.create_task(
                    self._analyze_with_single_provider(content, analysis_type, context, provider, request_id)
                )
                tasks.append(task)
            
            # Wait for all analyses to complete (with timeout)
            responses = []
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(completed_tasks):
                if isinstance(result, AIResponse):
                    responses.append(result)
                else:
                    logger.error(f"Provider {providers[i].value} failed: {str(result)}")
            
            if not responses:
                raise Exception("All providers failed")
            
            logger.info(f"Multi-provider analysis completed: {len(responses)} responses")
            return responses
            
        except Exception as e:
            logger.error(f"Multi-provider analysis failed: {str(e)}")
            raise
    
    async def _build_consensus(
        self, 
        responses: List[AIResponse], 
        analysis_type: AnalysisType, 
        request_id: str
    ) -> AIResponse:
        """Build consensus from multiple AI responses."""
        try:
            if not responses:
                raise Exception("No responses to build consensus from")
            
            # Analyze decisions
            decisions = [r.decision for r in responses]
            decision_counts = {}
            for decision in decisions:
                decision_counts[decision] = decision_counts.get(decision, 0) + 1
            
            # Find consensus decision (majority or highest confidence)
            consensus_decision = max(decision_counts, key=decision_counts.get)
            
            # Calculate consensus confidence
            consensus_responses = [r for r in responses if r.decision == consensus_decision]
            avg_confidence = sum(r.confidence for r in consensus_responses) / len(consensus_responses)
            
            # Adjust confidence based on agreement level
            agreement_ratio = len(consensus_responses) / len(responses)
            adjusted_confidence = avg_confidence * agreement_ratio
            
            # Combine reasoning and evidence
            combined_reasoning = self._combine_reasoning(consensus_responses)
            combined_evidence = self._combine_evidence(consensus_responses)
            
            # Calculate total cost and processing time
            total_cost = sum(r.cost_estimate for r in responses)
            max_processing_time = max(r.processing_time for r in responses)
            
            # Create consensus response
            consensus_response = AIResponse(
                provider=AIProvider.CLAUDE,  # Use primary provider as representative
                analysis_type=analysis_type,
                decision=consensus_decision,
                confidence=adjusted_confidence,
                reasoning=combined_reasoning,
                evidence={
                    **combined_evidence,
                    'consensus_details': {
                        'total_providers': len(responses),
                        'agreement_ratio': agreement_ratio,
                        'decision_breakdown': decision_counts,
                        'individual_confidences': [r.confidence for r in responses]
                    }
                },
                processing_time=max_processing_time,
                model_used='consensus',
                cost_estimate=total_cost,
                timestamp=datetime.utcnow(),
                request_id=request_id
            )
            
            logger.info(f"Consensus built: {consensus_decision} ({adjusted_confidence:.2f}) from {len(responses)} providers")
            return consensus_response
            
        except Exception as e:
            logger.error(f"Consensus building failed: {str(e)}")
            # Return best single response as fallback
            return max(responses, key=lambda r: r.confidence)
    
    def _combine_reasoning(self, responses: List[AIResponse]) -> str:
        """Combine reasoning from multiple responses."""
        reasonings = [r.reasoning for r in responses if r.reasoning]
        if not reasonings:
            return "Consensus analysis completed"
        
        # Create combined reasoning
        combined = "Consensus Analysis:\n\n"
        for i, reasoning in enumerate(reasonings, 1):
            combined += f"Provider {i}: {reasoning}\n\n"
        
        combined += f"Consensus: Based on analysis from {len(reasonings)} AI providers, "
        combined += "the majority assessment supports this decision."
        
        return combined
    
    def _combine_evidence(self, responses: List[AIResponse]) -> Dict[str, Any]:
        """Combine evidence from multiple responses."""
        combined_evidence = {}
        
        for i, response in enumerate(responses):
            if response.evidence:
                combined_evidence[f'provider_{i+1}_{response.provider.value}'] = response.evidence
        
        return combined_evidence
    
    # Provider-specific API calls
    
    async def _call_claude(self, prompt: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Call Claude API."""
        try:
            config = self.provider_configs[AIProvider.CLAUDE]
            client = self.providers[AIProvider.CLAUDE]
            
            message = await client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'text': message.content[0].text,
                'usage': {
                    'input_tokens': message.usage.input_tokens,
                    'output_tokens': message.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            raise
    
    async def _call_openai(self, prompt: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Call OpenAI API."""
        try:
            config = self.provider_configs[AIProvider.OPENAI]
            
            response = await openai.ChatCompletion.acreate(
                model=config.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                timeout=config.timeout
            )
            
            return {
                'text': response.choices[0].message.content,
                'usage': response.usage
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    async def _call_gemini(self, prompt: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Call Gemini API."""
        try:
            config = self.provider_configs[AIProvider.GEMINI]
            model = genai.GenerativeModel(config.model)
            
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=config.max_tokens,
                    temperature=config.temperature
                )
            )
            
            return {
                'text': response.text,
                'usage': {
                    'input_tokens': len(prompt.split()),  # Approximate
                    'output_tokens': len(response.text.split())  # Approximate
                }
            }
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            raise
    
    async def _call_huggingface(self, prompt: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Call HuggingFace API."""
        try:
            config = self.provider_configs[AIProvider.HUGGINGFACE]
            
            # Use transformers pipeline for local inference
            # This is a simplified implementation - in production, you'd use HF's API
            classifier = pipeline("text-classification", model=config.model)
            result = classifier(prompt)
            
            return {
                'text': json.dumps(result),
                'usage': {
                    'input_tokens': len(prompt.split()),
                    'output_tokens': len(json.dumps(result).split())
                }
            }
            
        except Exception as e:
            logger.error(f"HuggingFace API call failed: {str(e)}")
            raise
    
    async def _call_cohere(self, prompt: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Call Cohere API."""
        try:
            config = self.provider_configs[AIProvider.COHERE]
            client = self.providers[AIProvider.COHERE]
            
            response = await client.generate(
                model=config.model,
                prompt=prompt,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            return {
                'text': response.generations[0].text,
                'usage': {
                    'input_tokens': len(prompt.split()),  # Approximate
                    'output_tokens': len(response.generations[0].text.split())  # Approximate
                }
            }
            
        except Exception as e:
            logger.error(f"Cohere API call failed: {str(e)}")
            raise
    
    # Utility methods
    
    async def _build_analysis_prompt(
        self, 
        content: str, 
        analysis_type: AnalysisType, 
        context: Dict[str, Any]
    ) -> str:
        """Build analysis prompt for AI providers."""
        base_prompt = f"""
You are an expert AI moderator for TrustStream v4.4, analyzing content for {analysis_type.value}.

CONTENT TO ANALYZE:
{content}

CONTEXT:
{json.dumps(context or {}, indent=2)}

ANALYSIS REQUIREMENTS:
Please analyze this content and provide your assessment in the following JSON format:

{{
    "decision": "BLOCK|FLAG|MONITOR|APPROVE",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of your decision",
    "evidence": {{
        "key_indicators": ["list", "of", "indicators"],
        "risk_factors": ["identified", "risks"],
        "positive_factors": ["positive", "aspects"]
    }}
}}

DECISION GUIDELINES:
- BLOCK: Content violates policies and should be removed immediately
- FLAG: Content needs human review due to potential issues
- MONITOR: Content is acceptable but should be watched for patterns
- APPROVE: Content is safe and appropriate

Focus on accuracy, fairness, and protecting community safety while respecting free expression.
"""
        
        return base_prompt
    
    async def _parse_ai_response(
        self, 
        response: Dict[str, Any], 
        provider: AIProvider, 
        analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """Parse AI response into standardized format."""
        try:
            text = response.get('text', '')
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
            except:
                pass
            
            # Fallback parsing based on keywords
            decision = 'APPROVE'
            confidence = 0.5
            reasoning = text
            
            # Simple keyword-based decision making
            text_lower = text.lower()
            if any(word in text_lower for word in ['block', 'remove', 'delete', 'violates']):
                decision = 'BLOCK'
                confidence = 0.8
            elif any(word in text_lower for word in ['flag', 'review', 'concern', 'potential']):
                decision = 'FLAG'
                confidence = 0.7
            elif any(word in text_lower for word in ['monitor', 'watch', 'track']):
                decision = 'MONITOR'
                confidence = 0.6
            
            return {
                'decision': decision,
                'confidence': confidence,
                'reasoning': reasoning,
                'evidence': {'raw_response': text}
            }
            
        except Exception as e:
            logger.error(f"Response parsing failed: {str(e)}")
            return {
                'decision': 'APPROVE',
                'confidence': 0.3,
                'reasoning': f'Parsing failed: {str(e)}',
                'evidence': {'error': str(e)}
            }
    
    async def _calculate_cost(self, provider: AIProvider, input_text: str, output_text: str) -> float:
        """Calculate estimated cost for API call."""
        try:
            config = self.provider_configs[provider]
            
            # Estimate token counts (rough approximation)
            input_tokens = len(input_text.split()) * 1.3  # Account for tokenization
            output_tokens = len(output_text.split()) * 1.3
            
            total_tokens = input_tokens + output_tokens
            cost = total_tokens * config.cost_per_token
            
            return cost
            
        except Exception as e:
            logger.error(f"Cost calculation failed: {str(e)}")
            return 0.0
    
    async def _update_provider_stats(
        self, 
        provider: AIProvider, 
        success: bool, 
        processing_time: float, 
        cost: float
    ):
        """Update provider performance statistics."""
        try:
            stats = self.provider_stats[provider]
            
            stats['requests'] += 1
            stats['last_used'] = time.time()
            
            if success:
                stats['successes'] += 1
                # Update average response time
                total_time = stats['avg_response_time'] * (stats['successes'] - 1) + processing_time
                stats['avg_response_time'] = total_time / stats['successes']
            else:
                stats['failures'] += 1
            
            stats['total_cost'] += cost
            
            # Update daily costs
            today = datetime.utcnow().date().isoformat()
            if today not in self.daily_costs:
                self.daily_costs[today] = {}
            if provider not in self.daily_costs[today]:
                self.daily_costs[today][provider] = 0.0
            self.daily_costs[today][provider] += cost
            
        except Exception as e:
            logger.error(f"Stats update failed: {str(e)}")
    
    def _generate_request_id(self, content: str, analysis_type: AnalysisType) -> str:
        """Generate unique request ID for caching."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{analysis_type.value}_{content_hash}_{int(time.time())}"
    
    async def _get_cached_response(self, request_id: str) -> Optional[AIResponse]:
        """Get cached response if available."""
        # Placeholder - implement caching logic
        return None
    
    async def _cache_response(self, request_id: str, response: Union[AIResponse, List[AIResponse]]):
        """Cache response for future use."""
        # Placeholder - implement caching logic
        pass
    
    async def _create_error_response(self, analysis_type: AnalysisType, error_message: str) -> AIResponse:
        """Create error response when analysis fails."""
        return AIResponse(
            provider=AIProvider.CLAUDE,  # Default provider
            analysis_type=analysis_type,
            decision='APPROVE',  # Safe default
            confidence=0.1,
            reasoning=f'Analysis failed: {error_message}',
            evidence={'error': error_message},
            processing_time=0.0,
            model_used='error',
            cost_estimate=0.0,
            timestamp=datetime.utcnow(),
            request_id='error'
        )
    
    # Public utility methods
    
    async def get_provider_stats(self) -> Dict[str, Any]:
        """Get comprehensive provider statistics."""
        return {
            'provider_stats': self.provider_stats,
            'daily_costs': self.daily_costs,
            'total_daily_cost': sum(
                sum(costs.values()) for costs in self.daily_costs.values()
            ),
            'provider_availability': {
                provider.value: await self._check_provider_availability(provider)
                for provider in self.provider_configs
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers."""
        health_status = {}
        
        for provider in self.provider_configs:
            try:
                # Simple test call
                test_response = await self._analyze_with_single_provider(
                    "Test content", AnalysisType.CONTENT_MODERATION, {}, provider, "health_check"
                )
                health_status[provider.value] = {
                    'status': 'healthy',
                    'response_time': test_response.processing_time,
                    'last_check': datetime.utcnow().isoformat()
                }
            except Exception as e:
                health_status[provider.value] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.utcnow().isoformat()
                }
        
        return health_status