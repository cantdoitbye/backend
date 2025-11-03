# Base AI Agent for TrustStream v4.4
# This module provides the foundation for all specialized AI moderation agents

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json

from agentic.services.agent_memory_service import AgentMemoryService
from agentic.models import AgentActionLog

logger = logging.getLogger(__name__)


class BaseAIAgent(ABC):
    """
    Base class for all TrustStream AI moderation agents.
    
    This abstract class provides the common interface and functionality
    that all specialized AI agents must implement. It integrates with
    the existing agentic module's memory and logging systems while
    adding TrustStream-specific capabilities.
    
    Key Features:
    - Standardized content analysis interface
    - Integration with existing agent memory system
    - Transparent decision making with explanations
    - Performance monitoring and metrics
    - Multi-AI provider support
    """
    
    def __init__(self, config, community_id: str, community_analysis: Dict[str, Any]):
        """
        Initialize the base AI agent.
        
        Args:
            config: TrustStream configuration object
            community_id: ID of the community this agent serves
            community_analysis: Analysis of community characteristics
        """
        self.config = config
        self.community_id = community_id
        self.community_analysis = community_analysis
        self.agent_memory = AgentMemoryService()
        
        # Agent-specific configuration
        self.agent_type = self.__class__.__name__.replace('Agent', '').lower()
        self.ai_providers = self._initialize_ai_providers()
        
        # Performance tracking
        self.decisions_made = 0
        self.total_processing_time = 0
        self.confidence_scores = []
        
        logger.info(f"Initialized {self.agent_type} agent for community {community_id}")
    
    async def initialize(self):
        """Initialize the agent with any required setup."""
        try:
            # Test AI provider connections
            await self._test_ai_providers()
            
            # Load agent-specific memory/context
            await self._load_agent_context()
            
            logger.info(f"{self.agent_type} agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_type} agent: {str(e)}")
            raise
    
    @abstractmethod
    async def analyze_content(
        self, 
        content: Dict[str, Any], 
        trust_score: float, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content and make a moderation decision.
        
        This is the main method that each specialized agent must implement.
        
        Args:
            content: The content to analyze
            trust_score: Trust score of the content author
            context: Additional context for the decision
            
        Returns:
            Dictionary containing:
            - action: 'approve', 'flag', 'remove', 'warn'
            - confidence: Float between 0 and 1
            - reasoning: Human-readable explanation
            - evidence: Supporting evidence for the decision
            - metadata: Additional agent-specific data
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return a list of capabilities this agent provides.
        
        Returns:
            List of capability strings
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Return a human-readable description of this agent.
        
        Returns:
            Description string
        """
        pass
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this agent.
        
        Returns:
            Dictionary containing performance data
        """
        avg_confidence = (
            sum(self.confidence_scores) / len(self.confidence_scores) 
            if self.confidence_scores else 0
        )
        
        avg_processing_time = (
            self.total_processing_time / self.decisions_made 
            if self.decisions_made > 0 else 0
        )
        
        return {
            'agent_type': self.agent_type,
            'community_id': self.community_id,
            'decisions_made': self.decisions_made,
            'average_confidence': round(avg_confidence, 3),
            'average_processing_time_ms': round(avg_processing_time, 2),
            'confidence_distribution': self._get_confidence_distribution(),
            'last_active': datetime.utcnow().isoformat()
        }
    
    async def log_decision(
        self, 
        content: Dict[str, Any], 
        decision: Dict[str, Any], 
        processing_time: float
    ):
        """
        Log a moderation decision for audit and learning purposes.
        
        Args:
            content: The content that was analyzed
            decision: The decision that was made
            processing_time: Time taken to make the decision
        """
        try:
            # Update performance metrics
            self.decisions_made += 1
            self.total_processing_time += processing_time
            self.confidence_scores.append(decision.get('confidence', 0.5))
            
            # Create action log entry using existing system
            action_data = {
                'action_type': 'CONTENT_MODERATION',
                'action_details': {
                    'agent_type': self.agent_type,
                    'content_id': content.get('id'),
                    'content_type': content.get('type'),
                    'decision': decision['action'],
                    'confidence': decision['confidence'],
                    'reasoning': decision['reasoning'],
                    'processing_time_ms': processing_time
                },
                'community_uid': self.community_id,
                'performed_by_uid': f"truststream_{self.agent_type}",
                'metadata': {
                    'trust_score': content.get('trust_score'),
                    'evidence': decision.get('evidence', {}),
                    'ai_provider': decision.get('ai_provider')
                }
            }
            
            # This would integrate with existing AgentActionLog model
            # For now, we'll log it
            logger.info(f"Decision logged: {json.dumps(action_data, indent=2)}")
            
            # Store in agent memory for learning
            await self._store_decision_in_memory(content, decision)
            
        except Exception as e:
            logger.error(f"Failed to log decision: {str(e)}")
    
    # Protected helper methods for subclasses
    
    async def _call_ai_provider(
        self, 
        provider: str, 
        prompt: str, 
        content: str, 
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Call an AI provider for content analysis.
        
        Args:
            provider: AI provider name ('openai', 'gemini', 'claude', etc.)
            prompt: The analysis prompt
            content: Content to analyze
            additional_context: Additional context for the AI
            
        Returns:
            AI provider response
        """
        try:
            if provider not in self.ai_providers:
                raise ValueError(f"AI provider {provider} not available")
            
            provider_client = self.ai_providers[provider]
            
            # Format the request based on provider
            if provider == 'openai':
                return await self._call_openai(provider_client, prompt, content, additional_context)
            elif provider == 'gemini':
                return await self._call_gemini(provider_client, prompt, content, additional_context)
            elif provider == 'claude':
                return await self._call_claude(provider_client, prompt, content, additional_context)
            elif provider == 'huggingface':
                return await self._call_huggingface(provider_client, prompt, content, additional_context)
            elif provider == 'cohere':
                return await self._call_cohere(provider_client, prompt, content, additional_context)
            else:
                raise ValueError(f"Unsupported AI provider: {provider}")
                
        except Exception as e:
            logger.error(f"AI provider {provider} call failed: {str(e)}")
            raise
    
    def _create_base_prompt(self, content_type: str, analysis_focus: str) -> str:
        """
        Create a base prompt for content analysis.
        
        Args:
            content_type: Type of content being analyzed
            analysis_focus: What to focus the analysis on
            
        Returns:
            Base prompt string
        """
        return f"""
You are a specialized AI moderation agent for TrustStream v4.4, focusing on {analysis_focus}.

Community Context:
- Community ID: {self.community_id}
- Community Size: {self.community_analysis.get('size', 'unknown')}
- Risk Level: {self.community_analysis.get('risk_level', 'medium')}

Content Analysis Task:
- Content Type: {content_type}
- Analysis Focus: {analysis_focus}

Please analyze the provided content and respond with a JSON object containing:
{{
    "action": "approve|flag|remove|warn",
    "confidence": 0.0-1.0,
    "reasoning": "Clear explanation of your decision",
    "evidence": {{
        "key_indicators": ["list", "of", "indicators"],
        "risk_factors": ["identified", "risks"],
        "positive_factors": ["positive", "aspects"]
    }},
    "recommendations": ["suggested", "actions"]
}}

Be thorough, fair, and transparent in your analysis.
"""
    
    def _extract_content_features(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant features from content for analysis.
        
        Args:
            content: Content dictionary
            
        Returns:
            Dictionary of extracted features
        """
        features = {
            'text_length': len(content.get('content', '')),
            'has_links': 'http' in content.get('content', '').lower(),
            'has_mentions': '@' in content.get('content', ''),
            'has_hashtags': '#' in content.get('content', ''),
            'language': content.get('language', 'en'),
            'content_type': content.get('type', 'text'),
            'timestamp': content.get('created_at'),
            'author_id': content.get('author_id'),
            'community_id': content.get('community_id')
        }
        
        # Add text-specific features
        text_content = content.get('content', '')
        if text_content:
            features.update({
                'word_count': len(text_content.split()),
                'sentence_count': text_content.count('.') + text_content.count('!') + text_content.count('?'),
                'uppercase_ratio': sum(1 for c in text_content if c.isupper()) / len(text_content) if text_content else 0,
                'punctuation_density': sum(1 for c in text_content if not c.isalnum() and not c.isspace()) / len(text_content) if text_content else 0
            })
        
        return features
    
    # Private helper methods
    
    def _initialize_ai_providers(self) -> Dict[str, Any]:
        """Initialize available AI providers based on configuration."""
        providers = {}
        
        # Initialize each configured AI provider
        ai_config = self.config.ai_services
        
        if ai_config.openai_api_key:
            providers['openai'] = self._init_openai_client(ai_config)
        
        if ai_config.gemini_api_key:
            providers['gemini'] = self._init_gemini_client(ai_config)
        
        if ai_config.claude_api_key:
            providers['claude'] = self._init_claude_client(ai_config)
        
        if ai_config.huggingface_api_key:
            providers['huggingface'] = self._init_huggingface_client(ai_config)
        
        if ai_config.cohere_api_key:
            providers['cohere'] = self._init_cohere_client(ai_config)
        
        return providers
    
    def _init_openai_client(self, ai_config):
        """Initialize OpenAI client."""
        try:
            import openai
            return openai.AsyncOpenAI(api_key=ai_config.openai_api_key)
        except ImportError:
            logger.warning("OpenAI library not available")
            return None
    
    def _init_gemini_client(self, ai_config):
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=ai_config.gemini_api_key)
            return genai
        except ImportError:
            logger.warning("Google Generative AI library not available")
            return None
    
    def _init_claude_client(self, ai_config):
        """Initialize Claude client."""
        try:
            import anthropic
            return anthropic.AsyncAnthropic(api_key=ai_config.claude_api_key)
        except ImportError:
            logger.warning("Anthropic library not available")
            return None
    
    def _init_huggingface_client(self, ai_config):
        """Initialize Hugging Face client."""
        try:
            from transformers import pipeline
            return {
                'api_key': ai_config.huggingface_api_key,
                'endpoint': ai_config.huggingface_endpoint
            }
        except ImportError:
            logger.warning("Transformers library not available")
            return None
    
    def _init_cohere_client(self, ai_config):
        """Initialize Cohere client."""
        try:
            import cohere
            return cohere.AsyncClient(api_key=ai_config.cohere_api_key)
        except ImportError:
            logger.warning("Cohere library not available")
            return None
    
    async def _test_ai_providers(self):
        """Test connections to all configured AI providers."""
        for provider_name, provider_client in self.ai_providers.items():
            try:
                # Simple test call to verify connectivity
                test_result = await self._call_ai_provider(
                    provider=provider_name,
                    prompt="Test connection. Respond with 'OK'.",
                    content="test",
                    additional_context={}
                )
                logger.info(f"AI provider {provider_name} connection test: OK")
                
            except Exception as e:
                logger.warning(f"AI provider {provider_name} connection test failed: {str(e)}")
    
    async def _load_agent_context(self):
        """Load agent-specific context from memory."""
        try:
            # This would integrate with existing agent memory system
            # For now, we'll just log that we're loading context
            logger.info(f"Loading context for {self.agent_type} agent in community {self.community_id}")
            
        except Exception as e:
            logger.error(f"Failed to load agent context: {str(e)}")
    
    async def _store_decision_in_memory(self, content: Dict[str, Any], decision: Dict[str, Any]):
        """Store decision in agent memory for learning."""
        try:
            memory_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'content_features': self._extract_content_features(content),
                'decision': decision,
                'agent_type': self.agent_type,
                'community_id': self.community_id
            }
            
            # This would integrate with existing agent memory system
            logger.debug(f"Storing decision in memory: {json.dumps(memory_entry, indent=2)}")
            
        except Exception as e:
            logger.error(f"Failed to store decision in memory: {str(e)}")
    
    def _get_confidence_distribution(self) -> Dict[str, int]:
        """Get distribution of confidence scores."""
        if not self.confidence_scores:
            return {}
        
        distribution = {
            'very_low': 0,    # 0.0 - 0.2
            'low': 0,         # 0.2 - 0.4
            'medium': 0,      # 0.4 - 0.6
            'high': 0,        # 0.6 - 0.8
            'very_high': 0    # 0.8 - 1.0
        }
        
        for score in self.confidence_scores:
            if score < 0.2:
                distribution['very_low'] += 1
            elif score < 0.4:
                distribution['low'] += 1
            elif score < 0.6:
                distribution['medium'] += 1
            elif score < 0.8:
                distribution['high'] += 1
            else:
                distribution['very_high'] += 1
        
        return distribution
    
    # AI Provider-specific methods (to be implemented based on actual APIs)
    
    async def _call_openai(self, client, prompt: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenAI API."""
        try:
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Content to analyze: {content}"}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return {
                'response': response.choices[0].message.content,
                'provider': 'openai',
                'model': 'gpt-4',
                'usage': response.usage.dict() if response.usage else {}
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    async def _call_gemini(self, client, prompt: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Gemini API."""
        try:
            model = client.GenerativeModel('gemini-pro')
            full_prompt = f"{prompt}\n\nContent to analyze: {content}"
            
            response = await model.generate_content_async(full_prompt)
            
            return {
                'response': response.text,
                'provider': 'gemini',
                'model': 'gemini-pro'
            }
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            raise
    
    async def _call_claude(self, client, prompt: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Claude API."""
        try:
            response = await client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nContent to analyze: {content}"}
                ]
            )
            
            return {
                'response': response.content[0].text,
                'provider': 'claude',
                'model': 'claude-3-sonnet-20240229',
                'usage': response.usage.dict() if hasattr(response, 'usage') else {}
            }
            
        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            raise
    
    async def _call_huggingface(self, client, prompt: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Hugging Face API."""
        try:
            # This would use Hugging Face Inference API
            # For now, return a placeholder
            return {
                'response': '{"action": "approve", "confidence": 0.7, "reasoning": "Hugging Face analysis"}',
                'provider': 'huggingface',
                'model': 'text-classification'
            }
            
        except Exception as e:
            logger.error(f"Hugging Face API call failed: {str(e)}")
            raise
    
    async def _call_cohere(self, client, prompt: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Cohere API."""
        try:
            response = await client.generate(
                model='command',
                prompt=f"{prompt}\n\nContent to analyze: {content}",
                max_tokens=1000,
                temperature=0.3
            )
            
            return {
                'response': response.generations[0].text,
                'provider': 'cohere',
                'model': 'command'
            }
            
        except Exception as e:
            logger.error(f"Cohere API call failed: {str(e)}")
            raise