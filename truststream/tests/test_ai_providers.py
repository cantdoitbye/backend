# truststream/tests/test_ai_providers.py

"""
Unit Tests for TrustStream AI Providers Integration

This module contains comprehensive unit tests for the AI Providers integration,
testing provider management, intelligent routing, fallback mechanisms, 
consensus-based decision making, and performance optimization features.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from datetime import datetime, timedelta

from truststream.ai_providers import (
    TrustStreamAIProviders, AIProvider, ProviderResponse, 
    ConsensusResult, ProviderConfig
)


class TestAIProvider(unittest.TestCase):
    """Test cases for AIProvider data class."""
    
    def test_ai_provider_creation(self):
        """Test AIProvider creation with valid configuration."""
        config = ProviderConfig(
            name="openai",
            api_key="test_key",
            model="gpt-4",
            max_tokens=1000,
            temperature=0.7
        )
        
        provider = AIProvider(
            name="openai",
            config=config,
            is_available=True,
            response_time_avg=0.8,
            success_rate=0.95,
            cost_per_request=0.002
        )
        
        self.assertEqual(provider.name, "openai")
        self.assertEqual(provider.config, config)
        self.assertTrue(provider.is_available)
        self.assertEqual(provider.response_time_avg, 0.8)
        self.assertEqual(provider.success_rate, 0.95)
        self.assertEqual(provider.cost_per_request, 0.002)


class TestProviderResponse(unittest.TestCase):
    """Test cases for ProviderResponse data class."""
    
    def test_provider_response_creation(self):
        """Test ProviderResponse creation with complete data."""
        response = ProviderResponse(
            provider_name="openai",
            decision="approve",
            confidence=0.85,
            reasoning="Content appears to be high-quality and safe",
            analysis_details={
                "toxicity_score": 0.1,
                "quality_score": 4.2,
                "safety_indicators": ["no_harmful_content", "appropriate_language"]
            },
            response_time=0.75,
            cost=0.002,
            model_used="gpt-4",
            timestamp=datetime.now()
        )
        
        self.assertEqual(response.provider_name, "openai")
        self.assertEqual(response.decision, "approve")
        self.assertEqual(response.confidence, 0.85)
        self.assertIn("toxicity_score", response.analysis_details)
        self.assertEqual(response.response_time, 0.75)


class TestConsensusResult(unittest.TestCase):
    """Test cases for ConsensusResult data class."""
    
    def test_consensus_result_creation(self):
        """Test ConsensusResult creation with multiple provider responses."""
        responses = [
            ProviderResponse("openai", "approve", 0.85, "Safe content", {}, 0.8, 0.002, "gpt-4", datetime.now()),
            ProviderResponse("claude", "approve", 0.90, "High quality", {}, 0.6, 0.001, "claude-3", datetime.now()),
            ProviderResponse("gemini", "flag", 0.70, "Potential issue", {}, 0.9, 0.0015, "gemini-pro", datetime.now())
        ]
        
        consensus = ConsensusResult(
            final_decision="approve",
            confidence=0.82,
            agreement_score=0.67,
            provider_responses=responses,
            reasoning="Majority consensus with high confidence",
            metadata={"total_providers": 3, "agreement_threshold": 0.6}
        )
        
        self.assertEqual(consensus.final_decision, "approve")
        self.assertEqual(consensus.confidence, 0.82)
        self.assertEqual(len(consensus.provider_responses), 3)
        self.assertIn("total_providers", consensus.metadata)


class TestTrustStreamAIProviders(unittest.TestCase):
    """Test cases for TrustStreamAIProviders main class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ai_providers = TrustStreamAIProviders()
        
        # Mock content for testing
        self.mock_content = {
            'content_id': 'test_content_123',
            'text': 'This is a test post about technology and innovation.',
            'author_id': 'user_456',
            'content_type': 'post',
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'community': 'tech_discussion'
            }
        }
        
        # Mock provider configurations
        self.mock_configs = {
            'openai': {
                'api_key': 'test_openai_key',
                'model': 'gpt-4',
                'max_tokens': 1000,
                'temperature': 0.3
            },
            'claude': {
                'api_key': 'test_claude_key',
                'model': 'claude-3-sonnet',
                'max_tokens': 1000,
                'temperature': 0.3
            }
        }
    
    def test_providers_initialization(self):
        """Test TrustStreamAIProviders initialization."""
        self.assertIsInstance(self.ai_providers, TrustStreamAIProviders)
        self.assertIsInstance(self.ai_providers.providers, dict)
        self.assertIsInstance(self.ai_providers.provider_stats, dict)
        self.assertIsInstance(self.ai_providers.rate_limiters, dict)
    
    @patch('truststream.ai_providers.TrustStreamAIProviders._load_provider_configs')
    def test_initialize_providers(self, mock_load_configs):
        """Test provider initialization with configurations."""
        mock_load_configs.return_value = self.mock_configs
        
        self.ai_providers.initialize_providers()
        
        # Should have initialized providers
        self.assertGreater(len(self.ai_providers.providers), 0)
        mock_load_configs.assert_called_once()
    
    @patch('openai.ChatCompletion.create')
    async def test_analyze_with_openai(self, mock_openai):
        """Test content analysis with OpenAI provider."""
        # Mock OpenAI response
        mock_openai.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'decision': 'approve',
                        'confidence': 0.85,
                        'reasoning': 'Content is appropriate and high-quality',
                        'analysis': {
                            'toxicity_score': 0.1,
                            'quality_score': 4.2,
                            'safety_indicators': ['appropriate_language']
                        }
                    })
                }
            }],
            'usage': {'total_tokens': 150}
        }
        
        # Initialize provider
        self.ai_providers.providers['openai'] = AIProvider(
            name='openai',
            config=ProviderConfig(**self.mock_configs['openai']),
            is_available=True,
            response_time_avg=0.8,
            success_rate=0.95,
            cost_per_request=0.002
        )
        
        response = await self.ai_providers._analyze_with_openai(self.mock_content)
        
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(response.provider_name, 'openai')
        self.assertEqual(response.decision, 'approve')
        self.assertEqual(response.confidence, 0.85)
    
    @patch('anthropic.Anthropic')
    async def test_analyze_with_claude(self, mock_anthropic):
        """Test content analysis with Claude provider."""
        # Mock Claude response
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text=json.dumps({
                'decision': 'flag',
                'confidence': 0.75,
                'reasoning': 'Content requires human review',
                'analysis': {
                    'toxicity_score': 0.3,
                    'quality_score': 3.5,
                    'safety_indicators': ['needs_review']
                }
            }))]
        )
        
        # Initialize provider
        self.ai_providers.providers['claude'] = AIProvider(
            name='claude',
            config=ProviderConfig(**self.mock_configs['claude']),
            is_available=True,
            response_time_avg=0.6,
            success_rate=0.93,
            cost_per_request=0.001
        )
        
        response = await self.ai_providers._analyze_with_claude(self.mock_content)
        
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(response.provider_name, 'claude')
        self.assertEqual(response.decision, 'flag')
        self.assertEqual(response.confidence, 0.75)
    
    def test_select_optimal_provider(self):
        """Test optimal provider selection algorithm."""
        # Set up mock providers with different characteristics
        self.ai_providers.providers = {
            'openai': AIProvider(
                name='openai',
                config=Mock(),
                is_available=True,
                response_time_avg=0.8,
                success_rate=0.95,
                cost_per_request=0.002
            ),
            'claude': AIProvider(
                name='claude',
                config=Mock(),
                is_available=True,
                response_time_avg=0.6,
                success_rate=0.93,
                cost_per_request=0.001
            ),
            'gemini': AIProvider(
                name='gemini',
                config=Mock(),
                is_available=False,  # Unavailable
                response_time_avg=1.2,
                success_rate=0.88,
                cost_per_request=0.0008
            )
        }
        
        # Test speed-optimized selection
        selected = self.ai_providers._select_optimal_provider(optimization='speed')
        self.assertEqual(selected.name, 'claude')  # Fastest available
        
        # Test cost-optimized selection
        selected = self.ai_providers._select_optimal_provider(optimization='cost')
        self.assertEqual(selected.name, 'claude')  # Cheapest available
        
        # Test reliability-optimized selection
        selected = self.ai_providers._select_optimal_provider(optimization='reliability')
        self.assertEqual(selected.name, 'openai')  # Highest success rate
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        provider_name = 'openai'
        
        # Should allow requests initially
        self.assertTrue(self.ai_providers._check_rate_limit(provider_name))
        
        # Simulate hitting rate limit
        self.ai_providers.rate_limiters[provider_name] = {
            'requests': 100,  # At limit
            'window_start': datetime.now(),
            'limit': 100,
            'window_seconds': 60
        }
        
        self.assertFalse(self.ai_providers._check_rate_limit(provider_name))
    
    def test_response_caching(self):
        """Test response caching mechanism."""
        content_hash = self.ai_providers._generate_content_hash(self.mock_content)
        
        # Mock response
        mock_response = ProviderResponse(
            provider_name='openai',
            decision='approve',
            confidence=0.85,
            reasoning='Test response',
            analysis_details={},
            response_time=0.8,
            cost=0.002,
            model_used='gpt-4',
            timestamp=datetime.now()
        )
        
        # Cache response
        self.ai_providers._cache_response(content_hash, mock_response)
        
        # Retrieve cached response
        cached = self.ai_providers._get_cached_response(content_hash)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.decision, 'approve')
        
        # Test cache expiration
        expired_response = ProviderResponse(
            provider_name='openai',
            decision='approve',
            confidence=0.85,
            reasoning='Expired response',
            analysis_details={},
            response_time=0.8,
            cost=0.002,
            model_used='gpt-4',
            timestamp=datetime.now() - timedelta(hours=25)  # Expired
        )
        
        expired_hash = 'expired_hash'
        self.ai_providers._cache_response(expired_hash, expired_response)
        cached_expired = self.ai_providers._get_cached_response(expired_hash)
        self.assertIsNone(cached_expired)  # Should be None due to expiration
    
    @patch('truststream.ai_providers.TrustStreamAIProviders._analyze_with_openai')
    @patch('truststream.ai_providers.TrustStreamAIProviders._analyze_with_claude')
    async def test_consensus_analysis(self, mock_claude, mock_openai):
        """Test consensus-based analysis with multiple providers."""
        # Mock provider responses
        mock_openai.return_value = ProviderResponse(
            'openai', 'approve', 0.85, 'Safe content', {}, 0.8, 0.002, 'gpt-4', datetime.now()
        )
        mock_claude.return_value = ProviderResponse(
            'claude', 'approve', 0.90, 'High quality', {}, 0.6, 0.001, 'claude-3', datetime.now()
        )
        
        # Set up providers
        self.ai_providers.providers = {
            'openai': AIProvider('openai', Mock(), True, 0.8, 0.95, 0.002),
            'claude': AIProvider('claude', Mock(), True, 0.6, 0.93, 0.001)
        }
        
        consensus = await self.ai_providers.analyze_with_consensus(
            self.mock_content, 
            providers=['openai', 'claude']
        )
        
        self.assertIsInstance(consensus, ConsensusResult)
        self.assertEqual(consensus.final_decision, 'approve')
        self.assertEqual(len(consensus.provider_responses), 2)
        self.assertGreater(consensus.agreement_score, 0.8)  # High agreement
    
    @patch('truststream.ai_providers.TrustStreamAIProviders._analyze_with_openai')
    async def test_fallback_mechanism(self, mock_openai):
        """Test fallback mechanism when primary provider fails."""
        # Mock primary provider failure
        mock_openai.side_effect = Exception("API Error")
        
        # Set up providers with fallback
        self.ai_providers.providers = {
            'openai': AIProvider('openai', Mock(), True, 0.8, 0.95, 0.002),
            'claude': AIProvider('claude', Mock(), True, 0.6, 0.93, 0.001)
        }
        
        with patch('truststream.ai_providers.TrustStreamAIProviders._analyze_with_claude') as mock_claude:
            mock_claude.return_value = ProviderResponse(
                'claude', 'approve', 0.80, 'Fallback analysis', {}, 0.6, 0.001, 'claude-3', datetime.now()
            )
            
            response = await self.ai_providers.analyze_content(
                self.mock_content,
                primary_provider='openai',
                fallback_providers=['claude']
            )
            
            self.assertIsInstance(response, ProviderResponse)
            self.assertEqual(response.provider_name, 'claude')  # Used fallback
    
    def test_provider_health_monitoring(self):
        """Test provider health monitoring and status updates."""
        provider_name = 'openai'
        
        # Initialize provider stats
        self.ai_providers.provider_stats[provider_name] = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'last_success': None,
            'last_failure': None
        }
        
        # Record successful request
        self.ai_providers._update_provider_stats(provider_name, success=True, response_time=0.8)
        
        stats = self.ai_providers.provider_stats[provider_name]
        self.assertEqual(stats['total_requests'], 1)
        self.assertEqual(stats['successful_requests'], 1)
        self.assertEqual(stats['failed_requests'], 0)
        self.assertIsNotNone(stats['last_success'])
        
        # Record failed request
        self.ai_providers._update_provider_stats(provider_name, success=False, response_time=0.0)
        
        self.assertEqual(stats['total_requests'], 2)
        self.assertEqual(stats['successful_requests'], 1)
        self.assertEqual(stats['failed_requests'], 1)
        self.assertIsNotNone(stats['last_failure'])
    
    def test_cost_optimization(self):
        """Test cost optimization features."""
        # Set up providers with different costs
        self.ai_providers.providers = {
            'expensive': AIProvider('expensive', Mock(), True, 0.5, 0.98, 0.005),
            'moderate': AIProvider('moderate', Mock(), True, 0.8, 0.95, 0.002),
            'cheap': AIProvider('cheap', Mock(), True, 1.2, 0.90, 0.0008)
        }
        
        # Test cost-optimized selection
        selected = self.ai_providers._select_optimal_provider(optimization='cost')
        self.assertEqual(selected.name, 'cheap')
        
        # Test cost tracking
        initial_cost = self.ai_providers.total_cost
        self.ai_providers._track_cost('moderate', 0.002)
        self.assertEqual(self.ai_providers.total_cost, initial_cost + 0.002)
    
    def test_batch_analysis(self):
        """Test batch content analysis."""
        content_batch = [
            {'content_id': 'content_1', 'text': 'First test content'},
            {'content_id': 'content_2', 'text': 'Second test content'},
            {'content_id': 'content_3', 'text': 'Third test content'}
        ]
        
        with patch('truststream.ai_providers.TrustStreamAIProviders.analyze_content') as mock_analyze:
            mock_analyze.return_value = ProviderResponse(
                'openai', 'approve', 0.85, 'Test response', {}, 0.8, 0.002, 'gpt-4', datetime.now()
            )
            
            # Run batch analysis
            results = asyncio.run(self.ai_providers.batch_analyze_content(content_batch))
            
            self.assertEqual(len(results), 3)
            self.assertEqual(mock_analyze.call_count, 3)
            
            for result in results:
                self.assertIn('content_id', result)
                self.assertIn('analysis_result', result)
                self.assertIsInstance(result['analysis_result'], ProviderResponse)
    
    def test_provider_configuration_validation(self):
        """Test provider configuration validation."""
        # Valid configuration
        valid_config = {
            'api_key': 'test_key',
            'model': 'gpt-4',
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        self.assertTrue(self.ai_providers._validate_provider_config('openai', valid_config))
        
        # Invalid configuration (missing required fields)
        invalid_config = {
            'model': 'gpt-4',
            'temperature': 0.7
            # Missing api_key
        }
        
        self.assertFalse(self.ai_providers._validate_provider_config('openai', invalid_config))
    
    def test_error_handling(self):
        """Test error handling and recovery mechanisms."""
        # Test handling of invalid content
        invalid_content = None
        
        with self.assertRaises(ValueError):
            asyncio.run(self.ai_providers.analyze_content(invalid_content))
        
        # Test handling of provider unavailability
        self.ai_providers.providers = {}  # No providers available
        
        with self.assertRaises(RuntimeError):
            asyncio.run(self.ai_providers.analyze_content(self.mock_content))
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Initialize metrics
        self.ai_providers._initialize_performance_metrics()
        
        # Record some metrics
        self.ai_providers._record_performance_metric('response_time', 0.8)
        self.ai_providers._record_performance_metric('response_time', 0.6)
        self.ai_providers._record_performance_metric('response_time', 1.0)
        
        metrics = self.ai_providers.get_performance_metrics()
        
        self.assertIn('response_time', metrics)
        self.assertIn('average', metrics['response_time'])
        self.assertIn('min', metrics['response_time'])
        self.assertIn('max', metrics['response_time'])
        
        self.assertAlmostEqual(metrics['response_time']['average'], 0.8, places=1)
        self.assertEqual(metrics['response_time']['min'], 0.6)
        self.assertEqual(metrics['response_time']['max'], 1.0)


class TestAIProvidersIntegration(unittest.TestCase):
    """Integration tests for AI Providers system."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.ai_providers = TrustStreamAIProviders()
    
    @patch('openai.ChatCompletion.create')
    @patch('anthropic.Anthropic')
    async def test_full_analysis_workflow(self, mock_anthropic, mock_openai):
        """Test complete analysis workflow with multiple providers."""
        # Mock responses from different providers
        mock_openai.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'decision': 'approve',
                        'confidence': 0.85,
                        'reasoning': 'Content is safe and appropriate',
                        'analysis': {'toxicity_score': 0.1, 'quality_score': 4.2}
                    })
                }
            }]
        }
        
        mock_claude_client = Mock()
        mock_anthropic.return_value = mock_claude_client
        mock_claude_client.messages.create.return_value = Mock(
            content=[Mock(text=json.dumps({
                'decision': 'approve',
                'confidence': 0.90,
                'reasoning': 'High-quality content',
                'analysis': {'toxicity_score': 0.05, 'quality_score': 4.5}
            }))]
        )
        
        # Initialize providers
        self.ai_providers.providers = {
            'openai': AIProvider('openai', Mock(), True, 0.8, 0.95, 0.002),
            'claude': AIProvider('claude', Mock(), True, 0.6, 0.93, 0.001)
        }
        
        # Run full analysis workflow
        content = {
            'content_id': 'integration_test',
            'text': 'This is a comprehensive integration test for AI providers.',
            'author_id': 'test_user',
            'content_type': 'post'
        }
        
        # Test single provider analysis
        single_result = await self.ai_providers.analyze_content(content, primary_provider='openai')
        self.assertIsInstance(single_result, ProviderResponse)
        self.assertEqual(single_result.decision, 'approve')
        
        # Test consensus analysis
        consensus_result = await self.ai_providers.analyze_with_consensus(
            content, 
            providers=['openai', 'claude']
        )
        self.assertIsInstance(consensus_result, ConsensusResult)
        self.assertEqual(consensus_result.final_decision, 'approve')
        self.assertGreater(consensus_result.agreement_score, 0.8)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)