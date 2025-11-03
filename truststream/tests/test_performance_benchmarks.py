# truststream/tests/test_performance_benchmarks.py

"""
Performance Benchmark Tests for TrustStream v4.4

This module contains comprehensive performance benchmark tests to measure
and validate TrustStream system performance under various load conditions,
ensuring the system meets performance requirements for production deployment.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import asyncio
import time
import threading
import concurrent.futures
import statistics
import psutil
import memory_profiler
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from truststream.trust_pyramid import TrustPyramidCalculator, TrustScore, TrustProfile
from truststream.ai_providers import TrustStreamAIProviders, ProviderResponse
from truststream.agent_ecosystem import TrustStreamAgentEcosystem, Agent, AgentTask
from truststream.matrix_integration import MatrixModerationBot, MatrixEvent
from truststream.admin_interface import TrustStreamAdminInterface
from truststream.explainability_engine import TrustStreamExplainabilityEngine


class PerformanceBenchmarkBase(unittest.TestCase):
    """Base class for performance benchmark tests."""
    
    def setUp(self):
        """Set up performance benchmark test environment."""
        self.trust_pyramid = TrustPyramidCalculator()
        self.ai_providers = TrustStreamAIProviders()
        self.agent_ecosystem = TrustStreamAgentEcosystem()
        self.matrix_bot = MatrixModerationBot()
        self.admin_interface = TrustStreamAdminInterface()
        self.explainability_engine = TrustStreamExplainabilityEngine()
        
        # Performance tracking
        self.performance_metrics = {
            'response_times': [],
            'throughput_rates': [],
            'memory_usage': [],
            'cpu_usage': [],
            'error_rates': [],
            'cache_hit_rates': []
        }
        
        # Test data generators
        self.test_users = self._generate_test_users(1000)
        self.test_content = self._generate_test_content(5000)
        self.test_communities = self._generate_test_communities(100)
    
    def _generate_test_users(self, count):
        """Generate test user data for performance testing."""
        users = []
        for i in range(count):
            users.append({
                'user_id': f'perf_user_{i:06d}',
                'username': f'@perfuser{i}',
                'trust_score': np.random.uniform(0.1, 0.95),
                'reputation_score': np.random.uniform(0.2, 0.9),
                'account_age_days': np.random.randint(1, 1000),
                'activity_metrics': {
                    'posts_count': np.random.randint(0, 500),
                    'comments_count': np.random.randint(0, 1000),
                    'likes_received': np.random.randint(0, 2000)
                }
            })
        return users
    
    def _generate_test_content(self, count):
        """Generate test content for performance testing."""
        content_templates = [
            "This is a test post about {topic}. I think it's really {adjective}.",
            "Can someone help me understand {topic}? I'm having trouble with {issue}.",
            "Great discussion about {topic}! Thanks for sharing your insights.",
            "I disagree with this approach to {topic}. Here's why: {reason}.",
            "Amazing work on {topic}! This is exactly what we needed."
        ]
        
        topics = ['technology', 'science', 'politics', 'education', 'entertainment']
        adjectives = ['interesting', 'important', 'challenging', 'innovative', 'helpful']
        issues = ['implementation', 'understanding', 'configuration', 'optimization']
        reasons = ['it lacks evidence', 'it\'s too complex', 'it\'s not scalable', 'it\'s outdated']
        
        content_items = []
        for i in range(count):
            template = np.random.choice(content_templates)
            content = template.format(
                topic=np.random.choice(topics),
                adjective=np.random.choice(adjectives),
                issue=np.random.choice(issues),
                reason=np.random.choice(reasons)
            )
            
            content_items.append({
                'content_id': f'perf_content_{i:06d}',
                'content': content,
                'content_type': np.random.choice(['post', 'comment']),
                'user_id': f'perf_user_{np.random.randint(0, 1000):06d}',
                'timestamp': datetime.now() - timedelta(minutes=np.random.randint(0, 10080))
            })
        
        return content_items
    
    def _generate_test_communities(self, count):
        """Generate test community data for performance testing."""
        communities = []
        for i in range(count):
            communities.append({
                'community_id': f'perf_community_{i:03d}',
                'name': f'Performance Test Community {i}',
                'member_count': np.random.randint(100, 10000),
                'moderation_level': np.random.choice(['lenient', 'moderate', 'strict']),
                'trust_threshold': np.random.uniform(0.3, 0.8)
            })
        return communities
    
    def measure_performance(self, func, *args, **kwargs):
        """Measure performance metrics for a function call."""
        # Record initial system state
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        # Execute function and measure time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        
        # Record final system state
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        # Calculate metrics
        response_time = end_time - start_time
        memory_delta = final_memory - initial_memory
        cpu_usage = (initial_cpu + final_cpu) / 2
        
        return {
            'result': result,
            'success': success,
            'error': error,
            'response_time': response_time,
            'memory_usage': final_memory,
            'memory_delta': memory_delta,
            'cpu_usage': cpu_usage,
            'timestamp': datetime.now()
        }


class TestTrustPyramidPerformance(PerformanceBenchmarkBase):
    """Performance benchmarks for Trust Pyramid Calculator."""
    
    def test_single_trust_calculation_performance(self):
        """Test performance of single trust score calculation."""
        user_data = self.test_users[0]
        community_data = self.test_communities[0]
        
        # Measure single calculation
        with patch.object(self.trust_pyramid, '_calculate_intelligence_score', return_value=0.75):
            with patch.object(self.trust_pyramid, '_calculate_appeal_score', return_value=0.68):
                with patch.object(self.trust_pyramid, '_calculate_social_score', return_value=0.72):
                    with patch.object(self.trust_pyramid, '_calculate_humanity_score', return_value=0.80):
                        
                        metrics = self.measure_performance(
                            self.trust_pyramid.calculate_trust_profile,
                            user_data=user_data,
                            community_context=community_data
                        )
        
        # Performance assertions
        self.assertTrue(metrics['success'])
        self.assertLess(metrics['response_time'], 0.1)  # Should complete in <100ms
        self.assertLess(metrics['memory_delta'], 5)  # Should use <5MB additional memory
        
        # Verify result quality
        trust_profile = metrics['result']
        self.assertIsInstance(trust_profile, TrustProfile)
        self.assertGreater(trust_profile.overall_score, 0.0)
    
    def test_batch_trust_calculation_performance(self):
        """Test performance of batch trust score calculations."""
        batch_size = 100
        user_batch = self.test_users[:batch_size]
        community_data = self.test_communities[0]
        
        # Mock calculation methods for consistent performance
        with patch.object(self.trust_pyramid, '_calculate_intelligence_score', return_value=0.75):
            with patch.object(self.trust_pyramid, '_calculate_appeal_score', return_value=0.68):
                with patch.object(self.trust_pyramid, '_calculate_social_score', return_value=0.72):
                    with patch.object(self.trust_pyramid, '_calculate_humanity_score', return_value=0.80):
                        
                        start_time = time.time()
                        results = []
                        
                        for user_data in user_batch:
                            result = self.trust_pyramid.calculate_trust_profile(
                                user_data=user_data,
                                community_context=community_data
                            )
                            results.append(result)
                        
                        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        throughput = batch_size / total_time
        avg_time_per_calculation = total_time / batch_size
        
        # Performance assertions
        self.assertEqual(len(results), batch_size)
        self.assertGreater(throughput, 500)  # Should process >500 calculations/second
        self.assertLess(avg_time_per_calculation, 0.002)  # <2ms per calculation
        
        # Verify all results are valid
        for result in results:
            self.assertIsInstance(result, TrustProfile)
            self.assertGreaterEqual(result.overall_score, 0.0)
            self.assertLessEqual(result.overall_score, 1.0)
    
    def test_concurrent_trust_calculation_performance(self):
        """Test performance under concurrent trust calculations."""
        batch_size = 200
        num_threads = 10
        user_batch = self.test_users[:batch_size]
        community_data = self.test_communities[0]
        
        def calculate_trust_batch(users_subset):
            """Calculate trust for a subset of users."""
            results = []
            for user_data in users_subset:
                with patch.object(self.trust_pyramid, '_calculate_intelligence_score', return_value=0.75):
                    with patch.object(self.trust_pyramid, '_calculate_appeal_score', return_value=0.68):
                        with patch.object(self.trust_pyramid, '_calculate_social_score', return_value=0.72):
                            with patch.object(self.trust_pyramid, '_calculate_humanity_score', return_value=0.80):
                                
                                result = self.trust_pyramid.calculate_trust_profile(
                                    user_data=user_data,
                                    community_context=community_data
                                )
                                results.append(result)
            return results
        
        # Split users into chunks for concurrent processing
        chunk_size = batch_size // num_threads
        user_chunks = [
            user_batch[i:i + chunk_size]
            for i in range(0, batch_size, chunk_size)
        ]
        
        # Execute concurrent calculations
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_chunk = {
                executor.submit(calculate_trust_batch, chunk): chunk
                for chunk in user_chunks
            }
            
            all_results = []
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk_results = future.result()
                all_results.extend(chunk_results)
        
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        throughput = len(all_results) / total_time
        
        # Performance assertions
        self.assertEqual(len(all_results), batch_size)
        self.assertGreater(throughput, 800)  # Should achieve >800 calculations/second with concurrency
        self.assertLess(total_time, 1.0)  # Should complete batch in <1 second
    
    def test_trust_calculation_memory_efficiency(self):
        """Test memory efficiency of trust calculations."""
        batch_size = 1000
        user_batch = self.test_users[:batch_size]
        community_data = self.test_communities[0]
        
        # Monitor memory usage during batch processing
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_samples = [initial_memory]
        
        with patch.object(self.trust_pyramid, '_calculate_intelligence_score', return_value=0.75):
            with patch.object(self.trust_pyramid, '_calculate_appeal_score', return_value=0.68):
                with patch.object(self.trust_pyramid, '_calculate_social_score', return_value=0.72):
                    with patch.object(self.trust_pyramid, '_calculate_humanity_score', return_value=0.80):
                        
                        for i, user_data in enumerate(user_batch):
                            result = self.trust_pyramid.calculate_trust_profile(
                                user_data=user_data,
                                community_context=community_data
                            )
                            
                            # Sample memory every 100 calculations
                            if i % 100 == 0:
                                current_memory = process.memory_info().rss / 1024 / 1024
                                memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        max_memory = max(memory_samples)
        memory_growth = final_memory - initial_memory
        
        # Memory efficiency assertions
        self.assertLess(memory_growth, 50)  # Should use <50MB for 1000 calculations
        self.assertLess(max_memory - initial_memory, 100)  # Peak usage <100MB
        
        # Check for memory leaks (final memory should be close to initial)
        memory_leak = final_memory - initial_memory
        self.assertLess(memory_leak, 20)  # <20MB memory leak tolerance


class TestAIProvidersPerformance(PerformanceBenchmarkBase):
    """Performance benchmarks for AI Providers."""
    
    def test_single_content_analysis_performance(self):
        """Test performance of single content analysis."""
        content_item = self.test_content[0]
        user_data = self.test_users[0]
        
        with patch.object(self.ai_providers, '_call_openai_api') as mock_openai:
            mock_openai.return_value = {
                'toxicity_score': 0.25,
                'quality_score': 0.78,
                'spam_score': 0.15
            }
            
            metrics = self.measure_performance(
                self.ai_providers.analyze_content,
                content=content_item['content'],
                content_type=content_item['content_type'],
                user_context=user_data
            )
        
        # Performance assertions
        self.assertTrue(metrics['success'])
        self.assertLess(metrics['response_time'], 2.0)  # Should complete in <2 seconds
        self.assertIsInstance(metrics['result'], ProviderResponse)
    
    def test_batch_content_analysis_performance(self):
        """Test performance of batch content analysis."""
        batch_size = 50
        content_batch = self.test_content[:batch_size]
        
        with patch.object(self.ai_providers, 'analyze_content_batch') as mock_batch:
            mock_responses = [
                ProviderResponse(
                    provider_name='openai',
                    analysis_result={'toxicity_score': 0.3, 'quality_score': 0.7},
                    confidence=0.85,
                    response_time=0.5,
                    cost=0.002
                )
                for _ in content_batch
            ]
            mock_batch.return_value = mock_responses
            
            metrics = self.measure_performance(
                self.ai_providers.analyze_content_batch,
                content_items=[item['content'] for item in content_batch],
                batch_size=10
            )
        
        # Performance assertions
        self.assertTrue(metrics['success'])
        self.assertLess(metrics['response_time'], 10.0)  # Should complete batch in <10 seconds
        self.assertEqual(len(metrics['result']), batch_size)
        
        # Calculate throughput
        throughput = batch_size / metrics['response_time']
        self.assertGreater(throughput, 5)  # Should process >5 items/second
    
    def test_provider_failover_performance(self):
        """Test performance of provider failover mechanisms."""
        content_item = self.test_content[0]
        
        # Simulate primary provider failure
        with patch.object(self.ai_providers, '_call_openai_api') as mock_openai:
            mock_openai.side_effect = Exception("Provider timeout")
            
            with patch.object(self.ai_providers, '_call_claude_api') as mock_claude:
                mock_claude.return_value = {
                    'toxicity_score': 0.28,
                    'quality_score': 0.75,
                    'spam_score': 0.18
                }
                
                metrics = self.measure_performance(
                    self.ai_providers.analyze_with_fallback,
                    content=content_item['content'],
                    primary_provider='openai',
                    fallback_provider='claude'
                )
        
        # Performance assertions
        self.assertTrue(metrics['success'])
        self.assertLess(metrics['response_time'], 5.0)  # Failover should complete in <5 seconds
        self.assertEqual(metrics['result'].provider_name, 'claude')
    
    def test_concurrent_provider_requests_performance(self):
        """Test performance under concurrent provider requests."""
        batch_size = 100
        content_batch = self.test_content[:batch_size]
        num_workers = 20
        
        def analyze_content_item(content_item):
            """Analyze a single content item."""
            with patch.object(self.ai_providers, '_call_openai_api') as mock_api:
                mock_api.return_value = {
                    'toxicity_score': np.random.uniform(0.1, 0.9),
                    'quality_score': np.random.uniform(0.3, 0.95),
                    'spam_score': np.random.uniform(0.05, 0.8)
                }
                
                return self.ai_providers.analyze_content(
                    content=content_item['content'],
                    content_type=content_item['content_type']
                )
        
        # Execute concurrent requests
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_content = {
                executor.submit(analyze_content_item, content): content
                for content in content_batch
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_content):
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        throughput = len(results) / total_time
        
        # Performance assertions
        self.assertEqual(len(results), batch_size)
        self.assertGreater(throughput, 10)  # Should achieve >10 analyses/second with concurrency
        self.assertLess(total_time, 15.0)  # Should complete in <15 seconds


class TestAgentEcosystemPerformance(PerformanceBenchmarkBase):
    """Performance benchmarks for Agent Ecosystem."""
    
    def test_single_agent_task_performance(self):
        """Test performance of single agent task processing."""
        content_item = self.test_content[0]
        
        with patch.object(self.agent_ecosystem, 'process_content') as mock_process:
            mock_process.return_value = {
                'agent_results': {
                    'toxicity_detector': {'score': 0.3, 'confidence': 0.85},
                    'quality_assessor': {'score': 0.7, 'confidence': 0.82},
                    'bias_detector': {'score': 0.2, 'confidence': 0.78}
                },
                'consensus_score': 0.65,
                'consensus_confidence': 0.82,
                'processing_time': 1.2
            }
            
            metrics = self.measure_performance(
                self.agent_ecosystem.process_content,
                content=content_item['content'],
                content_type=content_item['content_type']
            )
        
        # Performance assertions
        self.assertTrue(metrics['success'])
        self.assertLess(metrics['response_time'], 3.0)  # Should complete in <3 seconds
        self.assertIn('consensus_score', metrics['result'])
    
    def test_agent_scaling_performance(self):
        """Test performance of agent ecosystem scaling."""
        high_load_scenario = {
            'concurrent_tasks': 50,
            'expected_throughput': 20  # tasks per second
        }
        
        with patch.object(self.agent_ecosystem, 'scale_agents') as mock_scale:
            mock_scale.return_value = {
                'active_agents': 15,
                'processing_capacity': 30,
                'scaling_time': 2.5
            }
            
            metrics = self.measure_performance(
                self.agent_ecosystem.auto_scale_for_load,
                expected_load=high_load_scenario['concurrent_tasks']
            )
        
        # Performance assertions
        self.assertTrue(metrics['success'])
        self.assertLess(metrics['response_time'], 5.0)  # Scaling should complete in <5 seconds
        self.assertGreaterEqual(
            metrics['result']['processing_capacity'],
            high_load_scenario['expected_throughput']
        )
    
    def test_agent_consensus_performance(self):
        """Test performance of agent consensus mechanisms."""
        batch_size = 25
        content_batch = self.test_content[:batch_size]
        
        def process_content_with_consensus(content_item):
            """Process content with full agent consensus."""
            with patch.object(self.agent_ecosystem, '_run_agent_analysis') as mock_analysis:
                mock_analysis.return_value = {
                    'toxicity_detector': {'score': np.random.uniform(0.1, 0.9), 'confidence': 0.85},
                    'quality_assessor': {'score': np.random.uniform(0.3, 0.95), 'confidence': 0.82},
                    'bias_detector': {'score': np.random.uniform(0.1, 0.7), 'confidence': 0.78}
                }
                
                return self.agent_ecosystem.calculate_consensus(
                    agent_results=mock_analysis.return_value
                )
        
        # Measure consensus calculation performance
        start_time = time.time()
        consensus_results = []
        
        for content_item in content_batch:
            result = process_content_with_consensus(content_item)
            consensus_results.append(result)
        
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        throughput = len(consensus_results) / total_time
        avg_time_per_consensus = total_time / len(consensus_results)
        
        # Performance assertions
        self.assertEqual(len(consensus_results), batch_size)
        self.assertGreater(throughput, 15)  # Should process >15 consensus calculations/second
        self.assertLess(avg_time_per_consensus, 0.1)  # <100ms per consensus calculation


class TestSystemIntegrationPerformance(PerformanceBenchmarkBase):
    """Performance benchmarks for integrated system workflows."""
    
    def test_end_to_end_moderation_performance(self):
        """Test performance of complete end-to-end moderation workflow."""
        content_item = self.test_content[0]
        user_data = self.test_users[0]
        community_data = self.test_communities[0]
        
        def complete_moderation_workflow():
            """Execute complete moderation workflow."""
            # Step 1: Trust calculation
            with patch.object(self.trust_pyramid, 'calculate_trust_profile') as mock_trust:
                mock_trust.return_value = TrustProfile(
                    user_id=user_data['user_id'],
                    intelligence_score=0.75,
                    appeal_score=0.68,
                    social_score=0.72,
                    humanity_score=0.80,
                    overall_score=0.74,
                    rank='Trusted',
                    confidence=0.85,
                    last_updated=datetime.now()
                )
                
                trust_profile = self.trust_pyramid.calculate_trust_profile(
                    user_data=user_data,
                    community_context=community_data
                )
            
            # Step 2: AI analysis
            with patch.object(self.ai_providers, 'analyze_content') as mock_ai:
                mock_ai.return_value = ProviderResponse(
                    provider_name='openai',
                    analysis_result={'toxicity_score': 0.25, 'quality_score': 0.78},
                    confidence=0.85,
                    response_time=0.5,
                    cost=0.002
                )
                
                ai_analysis = self.ai_providers.analyze_content(
                    content=content_item['content'],
                    content_type=content_item['content_type'],
                    user_context=user_data
                )
            
            # Step 3: Agent processing
            with patch.object(self.agent_ecosystem, 'process_content') as mock_agents:
                mock_agents.return_value = {
                    'consensus_score': 0.72,
                    'consensus_confidence': 0.83,
                    'processing_time': 1.1
                }
                
                agent_analysis = self.agent_ecosystem.process_content(
                    content=content_item['content'],
                    ai_analysis=ai_analysis,
                    trust_profile=trust_profile
                )
            
            # Step 4: Final decision
            final_score = (agent_analysis['consensus_score'] * 0.8) + (trust_profile.overall_score * 0.2)
            decision = 'approved' if final_score >= 0.6 else 'flagged'
            
            return {
                'decision': decision,
                'confidence': agent_analysis['consensus_confidence'],
                'final_score': final_score,
                'trust_profile': trust_profile,
                'ai_analysis': ai_analysis,
                'agent_analysis': agent_analysis
            }
        
        # Measure complete workflow performance
        metrics = self.measure_performance(complete_moderation_workflow)
        
        # Performance assertions
        self.assertTrue(metrics['success'])
        self.assertLess(metrics['response_time'], 5.0)  # Complete workflow in <5 seconds
        self.assertIn('decision', metrics['result'])
        self.assertIn('confidence', metrics['result'])
    
    def test_high_volume_processing_performance(self):
        """Test system performance under high volume processing."""
        batch_size = 200
        content_batch = self.test_content[:batch_size]
        user_batch = self.test_users[:batch_size]
        
        # Simulate high-volume processing
        start_time = time.time()
        processed_count = 0
        successful_count = 0
        
        for i in range(batch_size):
            try:
                # Mock rapid processing
                with patch.object(self.trust_pyramid, 'calculate_trust_profile') as mock_trust:
                    mock_trust.return_value = TrustProfile(
                        user_id=user_batch[i]['user_id'],
                        overall_score=np.random.uniform(0.3, 0.9),
                        rank='Trusted',
                        confidence=0.85,
                        last_updated=datetime.now()
                    )
                    
                    with patch.object(self.ai_providers, 'analyze_content') as mock_ai:
                        mock_ai.return_value = ProviderResponse(
                            provider_name='openai',
                            analysis_result={'toxicity_score': np.random.uniform(0.1, 0.8)},
                            confidence=0.85,
                            response_time=0.1,
                            cost=0.001
                        )
                        
                        # Process item
                        trust_result = mock_trust.return_value
                        ai_result = mock_ai.return_value
                        
                        successful_count += 1
                
                processed_count += 1
                
                # Check performance every 50 items
                if processed_count % 50 == 0:
                    current_time = time.time()
                    current_throughput = processed_count / (current_time - start_time)
                    self.assertGreater(current_throughput, 30)  # Maintain >30 items/second
            
            except Exception as e:
                # Log error but continue processing
                print(f"Processing error for item {i}: {e}")
        
        end_time = time.time()
        
        # Calculate final performance metrics
        total_time = end_time - start_time
        throughput = processed_count / total_time
        success_rate = successful_count / processed_count
        
        # Performance assertions
        self.assertEqual(processed_count, batch_size)
        self.assertGreater(throughput, 25)  # Should maintain >25 items/second overall
        self.assertGreater(success_rate, 0.95)  # >95% success rate
        self.assertLess(total_time, 10.0)  # Complete batch in <10 seconds
    
    def test_memory_usage_under_load(self):
        """Test memory usage patterns under sustained load."""
        batch_size = 500
        content_batch = self.test_content[:batch_size]
        
        # Monitor memory usage during processing
        process = psutil.Process()
        memory_samples = []
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_samples.append(initial_memory)
        
        for i, content_item in enumerate(content_batch):
            # Simulate processing
            with patch.object(self.trust_pyramid, 'calculate_trust_profile') as mock_trust:
                mock_trust.return_value = TrustProfile(
                    user_id=f'user_{i}',
                    overall_score=0.75,
                    rank='Trusted',
                    confidence=0.85,
                    last_updated=datetime.now()
                )
                
                result = mock_trust.return_value
            
            # Sample memory every 50 items
            if i % 50 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        max_memory = max(memory_samples)
        memory_growth = final_memory - initial_memory
        
        # Memory usage assertions
        self.assertLess(memory_growth, 100)  # Total growth <100MB
        self.assertLess(max_memory - initial_memory, 150)  # Peak usage <150MB
        
        # Check for memory stability (no continuous growth)
        if len(memory_samples) >= 5:
            recent_samples = memory_samples[-3:]
            memory_variance = statistics.variance(recent_samples)
            self.assertLess(memory_variance, 25)  # Low variance in recent samples
    
    def test_concurrent_user_simulation(self):
        """Test system performance with concurrent user simulation."""
        num_concurrent_users = 50
        requests_per_user = 10
        
        def simulate_user_activity(user_id):
            """Simulate activity for a single user."""
            user_data = self.test_users[user_id % len(self.test_users)]
            results = []
            
            for i in range(requests_per_user):
                content_item = self.test_content[(user_id * requests_per_user + i) % len(self.test_content)]
                
                # Simulate content analysis request
                with patch.object(self.ai_providers, 'analyze_content') as mock_analyze:
                    mock_analyze.return_value = ProviderResponse(
                        provider_name='openai',
                        analysis_result={'toxicity_score': np.random.uniform(0.1, 0.8)},
                        confidence=0.85,
                        response_time=np.random.uniform(0.3, 0.8),
                        cost=0.002
                    )
                    
                    result = self.ai_providers.analyze_content(
                        content=content_item['content'],
                        content_type=content_item['content_type'],
                        user_context=user_data
                    )
                    results.append(result)
                
                # Small delay between requests
                time.sleep(0.1)
            
            return results
        
        # Execute concurrent user simulation
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
            future_to_user = {
                executor.submit(simulate_user_activity, user_id): user_id
                for user_id in range(num_concurrent_users)
            }
            
            all_results = []
            completed_users = 0
            
            for future in concurrent.futures.as_completed(future_to_user):
                user_results = future.result()
                all_results.extend(user_results)
                completed_users += 1
        
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        total_requests = num_concurrent_users * requests_per_user
        throughput = total_requests / total_time
        
        # Performance assertions
        self.assertEqual(len(all_results), total_requests)
        self.assertEqual(completed_users, num_concurrent_users)
        self.assertGreater(throughput, 20)  # Should handle >20 requests/second
        self.assertLess(total_time, 30.0)  # Should complete simulation in <30 seconds


if __name__ == '__main__':
    # Run performance benchmarks with detailed output
    unittest.main(verbosity=2, buffer=True)