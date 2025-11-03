# truststream/tests/test_agent_ecosystem.py

"""
Unit Tests for TrustStream Agent Ecosystem

This module contains comprehensive unit tests for the Agent Ecosystem,
testing agent management, task distribution, consensus mechanisms,
performance monitoring, and specialized agent behaviors.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum

from truststream.agent_ecosystem import (
    TrustStreamAgentEcosystem, Agent, AgentTask, AgentResponse,
    ConsensusResult, AgentType, TaskType, AgentStatus
)


class TestAgent(unittest.TestCase):
    """Test cases for Agent data class."""
    
    def test_agent_creation(self):
        """Test Agent creation with valid configuration."""
        agent = Agent(
            agent_id="toxicity_detector_001",
            name="Toxicity Detector",
            agent_type=AgentType.TOXICITY_DETECTOR,
            specialization="hate_speech_detection",
            model_config={
                "model": "bert-toxicity-classifier",
                "threshold": 0.7,
                "confidence_threshold": 0.8
            },
            performance_metrics={
                "accuracy": 0.94,
                "precision": 0.91,
                "recall": 0.89,
                "f1_score": 0.90
            },
            status=AgentStatus.ACTIVE,
            last_active=datetime.now(),
            total_tasks=1250,
            successful_tasks=1180,
            average_response_time=0.3
        )
        
        self.assertEqual(agent.agent_id, "toxicity_detector_001")
        self.assertEqual(agent.name, "Toxicity Detector")
        self.assertEqual(agent.agent_type, AgentType.TOXICITY_DETECTOR)
        self.assertEqual(agent.specialization, "hate_speech_detection")
        self.assertIn("model", agent.model_config)
        self.assertEqual(agent.status, AgentStatus.ACTIVE)
        self.assertEqual(agent.total_tasks, 1250)


class TestAgentTask(unittest.TestCase):
    """Test cases for AgentTask data class."""
    
    def test_agent_task_creation(self):
        """Test AgentTask creation with complete data."""
        task = AgentTask(
            task_id="task_12345",
            task_type=TaskType.CONTENT_ANALYSIS,
            content={
                "content_id": "post_789",
                "text": "This is a test post for analysis",
                "author_id": "user_456",
                "metadata": {"community": "tech_discussion"}
            },
            priority=8,
            assigned_agents=["toxicity_detector_001", "quality_assessor_002"],
            created_at=datetime.now(),
            deadline=datetime.now() + timedelta(seconds=30),
            context={
                "community_rules": ["no_hate_speech", "constructive_discussion"],
                "author_trust_score": 0.75
            }
        )
        
        self.assertEqual(task.task_id, "task_12345")
        self.assertEqual(task.task_type, TaskType.CONTENT_ANALYSIS)
        self.assertIn("content_id", task.content)
        self.assertEqual(task.priority, 8)
        self.assertEqual(len(task.assigned_agents), 2)
        self.assertIn("community_rules", task.context)


class TestAgentResponse(unittest.TestCase):
    """Test cases for AgentResponse data class."""
    
    def test_agent_response_creation(self):
        """Test AgentResponse creation with analysis results."""
        response = AgentResponse(
            agent_id="toxicity_detector_001",
            task_id="task_12345",
            decision="approve",
            confidence=0.85,
            reasoning="Content shows no signs of toxicity or harmful language",
            analysis_details={
                "toxicity_score": 0.12,
                "hate_speech_probability": 0.05,
                "offensive_language_detected": False,
                "flagged_terms": [],
                "sentiment_analysis": {
                    "polarity": 0.3,
                    "subjectivity": 0.6
                }
            },
            processing_time=0.28,
            timestamp=datetime.now(),
            metadata={
                "model_version": "v2.1",
                "confidence_threshold": 0.8
            }
        )
        
        self.assertEqual(response.agent_id, "toxicity_detector_001")
        self.assertEqual(response.task_id, "task_12345")
        self.assertEqual(response.decision, "approve")
        self.assertEqual(response.confidence, 0.85)
        self.assertIn("toxicity_score", response.analysis_details)
        self.assertEqual(response.processing_time, 0.28)


class TestTrustStreamAgentEcosystem(unittest.TestCase):
    """Test cases for TrustStreamAgentEcosystem main class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ecosystem = TrustStreamAgentEcosystem()
        
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
        
        # Mock agent configurations
        self.mock_agents = {
            'toxicity_detector_001': Agent(
                agent_id="toxicity_detector_001",
                name="Toxicity Detector",
                agent_type=AgentType.TOXICITY_DETECTOR,
                specialization="hate_speech_detection",
                model_config={"model": "bert-toxicity", "threshold": 0.7},
                performance_metrics={"accuracy": 0.94, "precision": 0.91},
                status=AgentStatus.ACTIVE,
                last_active=datetime.now(),
                total_tasks=1250,
                successful_tasks=1180,
                average_response_time=0.3
            ),
            'quality_assessor_002': Agent(
                agent_id="quality_assessor_002",
                name="Quality Assessor",
                agent_type=AgentType.QUALITY_ASSESSOR,
                specialization="content_quality_evaluation",
                model_config={"model": "quality-bert", "min_quality": 3.0},
                performance_metrics={"accuracy": 0.89, "precision": 0.87},
                status=AgentStatus.ACTIVE,
                last_active=datetime.now(),
                total_tasks=980,
                successful_tasks=920,
                average_response_time=0.45
            )
        }
    
    def test_ecosystem_initialization(self):
        """Test TrustStreamAgentEcosystem initialization."""
        self.assertIsInstance(self.ecosystem, TrustStreamAgentEcosystem)
        self.assertIsInstance(self.ecosystem.agents, dict)
        self.assertIsInstance(self.ecosystem.task_queue, list)
        self.assertIsInstance(self.ecosystem.active_tasks, dict)
        self.assertIsInstance(self.ecosystem.agent_performance, dict)
    
    def test_register_agent(self):
        """Test agent registration."""
        agent = self.mock_agents['toxicity_detector_001']
        
        self.ecosystem.register_agent(agent)
        
        self.assertIn(agent.agent_id, self.ecosystem.agents)
        self.assertEqual(self.ecosystem.agents[agent.agent_id], agent)
        self.assertIn(agent.agent_id, self.ecosystem.agent_performance)
    
    def test_unregister_agent(self):
        """Test agent unregistration."""
        agent = self.mock_agents['toxicity_detector_001']
        self.ecosystem.register_agent(agent)
        
        self.ecosystem.unregister_agent(agent.agent_id)
        
        self.assertNotIn(agent.agent_id, self.ecosystem.agents)
        # Performance data should be preserved for analytics
        self.assertIn(agent.agent_id, self.ecosystem.agent_performance)
    
    def test_create_task(self):
        """Test task creation and queuing."""
        task = self.ecosystem.create_task(
            task_type=TaskType.CONTENT_ANALYSIS,
            content=self.mock_content,
            priority=7,
            context={'community_rules': ['no_spam']}
        )
        
        self.assertIsInstance(task, AgentTask)
        self.assertEqual(task.task_type, TaskType.CONTENT_ANALYSIS)
        self.assertEqual(task.content, self.mock_content)
        self.assertEqual(task.priority, 7)
        self.assertIn(task, self.ecosystem.task_queue)
    
    def test_assign_task_to_agents(self):
        """Test task assignment to appropriate agents."""
        # Register agents
        for agent in self.mock_agents.values():
            self.ecosystem.register_agent(agent)
        
        task = self.ecosystem.create_task(
            task_type=TaskType.CONTENT_ANALYSIS,
            content=self.mock_content,
            priority=8
        )
        
        assigned_agents = self.ecosystem._assign_task_to_agents(task)
        
        self.assertGreater(len(assigned_agents), 0)
        # Should include toxicity detector for content analysis
        agent_types = [self.ecosystem.agents[agent_id].agent_type for agent_id in assigned_agents]
        self.assertIn(AgentType.TOXICITY_DETECTOR, agent_types)
    
    def test_agent_selection_algorithm(self):
        """Test agent selection based on performance and availability."""
        # Register agents with different performance metrics
        high_perf_agent = Agent(
            agent_id="high_perf_001",
            name="High Performance Agent",
            agent_type=AgentType.TOXICITY_DETECTOR,
            specialization="general",
            model_config={},
            performance_metrics={"accuracy": 0.95, "precision": 0.93},
            status=AgentStatus.ACTIVE,
            last_active=datetime.now(),
            total_tasks=1000,
            successful_tasks=950,
            average_response_time=0.2
        )
        
        low_perf_agent = Agent(
            agent_id="low_perf_002",
            name="Low Performance Agent",
            agent_type=AgentType.TOXICITY_DETECTOR,
            specialization="general",
            model_config={},
            performance_metrics={"accuracy": 0.80, "precision": 0.78},
            status=AgentStatus.ACTIVE,
            last_active=datetime.now(),
            total_tasks=1000,
            successful_tasks=800,
            average_response_time=0.8
        )
        
        self.ecosystem.register_agent(high_perf_agent)
        self.ecosystem.register_agent(low_perf_agent)
        
        # Select best agent for toxicity detection
        selected_agents = self.ecosystem._select_agents_by_type(
            AgentType.TOXICITY_DETECTOR, 
            max_agents=1
        )
        
        self.assertEqual(len(selected_agents), 1)
        self.assertEqual(selected_agents[0], "high_perf_001")  # Should select higher performing agent
    
    @patch('truststream.agent_ecosystem.TrustStreamAgentEcosystem._execute_agent_analysis')
    async def test_process_task(self, mock_execute):
        """Test task processing with agent execution."""
        # Mock agent responses
        mock_execute.side_effect = [
            AgentResponse(
                agent_id="toxicity_detector_001",
                task_id="test_task",
                decision="approve",
                confidence=0.85,
                reasoning="No toxicity detected",
                analysis_details={"toxicity_score": 0.1},
                processing_time=0.3,
                timestamp=datetime.now(),
                metadata={}
            ),
            AgentResponse(
                agent_id="quality_assessor_002",
                task_id="test_task",
                decision="approve",
                confidence=0.78,
                reasoning="Good quality content",
                analysis_details={"quality_score": 4.2},
                processing_time=0.4,
                timestamp=datetime.now(),
                metadata={}
            )
        ]
        
        # Register agents
        for agent in self.mock_agents.values():
            self.ecosystem.register_agent(agent)
        
        # Create and process task
        task = self.ecosystem.create_task(
            task_type=TaskType.CONTENT_ANALYSIS,
            content=self.mock_content,
            priority=8
        )
        
        result = await self.ecosystem.process_task(task)
        
        self.assertIsInstance(result, ConsensusResult)
        self.assertEqual(len(result.agent_responses), 2)
        self.assertIn("approve", [resp.decision for resp in result.agent_responses])
    
    def test_consensus_calculation(self):
        """Test consensus calculation from multiple agent responses."""
        responses = [
            AgentResponse(
                "toxicity_detector_001", "task_123", "approve", 0.85,
                "No toxicity", {}, 0.3, datetime.now(), {}
            ),
            AgentResponse(
                "quality_assessor_002", "task_123", "approve", 0.78,
                "Good quality", {}, 0.4, datetime.now(), {}
            ),
            AgentResponse(
                "bias_detector_003", "task_123", "flag", 0.65,
                "Potential bias", {}, 0.5, datetime.now(), {}
            )
        ]
        
        consensus = self.ecosystem._calculate_consensus(responses)
        
        self.assertIsInstance(consensus, ConsensusResult)
        self.assertEqual(consensus.final_decision, "approve")  # Majority decision
        self.assertEqual(len(consensus.agent_responses), 3)
        self.assertGreater(consensus.confidence, 0.5)
        self.assertLess(consensus.agreement_score, 1.0)  # Not unanimous
    
    def test_agent_performance_tracking(self):
        """Test agent performance metrics tracking."""
        agent_id = "toxicity_detector_001"
        
        # Initialize performance tracking
        self.ecosystem._initialize_agent_performance(agent_id)
        
        # Record successful task
        self.ecosystem._update_agent_performance(
            agent_id, 
            success=True, 
            response_time=0.3, 
            confidence=0.85
        )
        
        performance = self.ecosystem.agent_performance[agent_id]
        self.assertEqual(performance['total_tasks'], 1)
        self.assertEqual(performance['successful_tasks'], 1)
        self.assertEqual(performance['failed_tasks'], 0)
        self.assertEqual(performance['average_response_time'], 0.3)
        self.assertEqual(performance['average_confidence'], 0.85)
        
        # Record failed task
        self.ecosystem._update_agent_performance(
            agent_id, 
            success=False, 
            response_time=1.2, 
            confidence=0.4
        )
        
        self.assertEqual(performance['total_tasks'], 2)
        self.assertEqual(performance['successful_tasks'], 1)
        self.assertEqual(performance['failed_tasks'], 1)
        self.assertAlmostEqual(performance['average_response_time'], 0.75, places=2)
        self.assertAlmostEqual(performance['average_confidence'], 0.625, places=2)
    
    def test_task_prioritization(self):
        """Test task queue prioritization."""
        # Create tasks with different priorities
        high_priority_task = self.ecosystem.create_task(
            TaskType.URGENT_REVIEW, self.mock_content, priority=10
        )
        medium_priority_task = self.ecosystem.create_task(
            TaskType.CONTENT_ANALYSIS, self.mock_content, priority=5
        )
        low_priority_task = self.ecosystem.create_task(
            TaskType.ROUTINE_CHECK, self.mock_content, priority=2
        )
        
        # Tasks should be ordered by priority
        sorted_tasks = self.ecosystem._get_prioritized_tasks()
        
        self.assertEqual(sorted_tasks[0], high_priority_task)
        self.assertEqual(sorted_tasks[1], medium_priority_task)
        self.assertEqual(sorted_tasks[2], low_priority_task)
    
    def test_agent_load_balancing(self):
        """Test load balancing across agents."""
        # Register multiple agents of same type
        agents = []
        for i in range(3):
            agent = Agent(
                agent_id=f"toxicity_detector_{i:03d}",
                name=f"Toxicity Detector {i}",
                agent_type=AgentType.TOXICITY_DETECTOR,
                specialization="general",
                model_config={},
                performance_metrics={"accuracy": 0.90},
                status=AgentStatus.ACTIVE,
                last_active=datetime.now(),
                total_tasks=100 * i,  # Different load levels
                successful_tasks=90 * i,
                average_response_time=0.3
            )
            agents.append(agent)
            self.ecosystem.register_agent(agent)
        
        # Select agents with load balancing
        selected = self.ecosystem._select_agents_with_load_balancing(
            AgentType.TOXICITY_DETECTOR, 
            max_agents=2
        )
        
        self.assertEqual(len(selected), 2)
        # Should prefer agents with lower current load
        self.assertIn("toxicity_detector_000", selected)  # Lowest load
    
    def test_agent_specialization_matching(self):
        """Test matching agents based on specialization."""
        # Register specialized agents
        hate_speech_agent = Agent(
            agent_id="hate_speech_specialist",
            name="Hate Speech Specialist",
            agent_type=AgentType.TOXICITY_DETECTOR,
            specialization="hate_speech_detection",
            model_config={},
            performance_metrics={"accuracy": 0.95},
            status=AgentStatus.ACTIVE,
            last_active=datetime.now(),
            total_tasks=500,
            successful_tasks=475,
            average_response_time=0.3
        )
        
        spam_agent = Agent(
            agent_id="spam_specialist",
            name="Spam Specialist",
            agent_type=AgentType.TOXICITY_DETECTOR,
            specialization="spam_detection",
            model_config={},
            performance_metrics={"accuracy": 0.92},
            status=AgentStatus.ACTIVE,
            last_active=datetime.now(),
            total_tasks=800,
            successful_tasks=736,
            average_response_time=0.25
        )
        
        self.ecosystem.register_agent(hate_speech_agent)
        self.ecosystem.register_agent(spam_agent)
        
        # Test specialization matching
        hate_speech_content = {
            'content_id': 'test_hate',
            'text': 'Content that might contain hate speech',
            'flags': ['potential_hate_speech']
        }
        
        selected = self.ecosystem._match_agents_by_specialization(
            hate_speech_content, 
            AgentType.TOXICITY_DETECTOR
        )
        
        self.assertIn("hate_speech_specialist", selected)
    
    def test_task_timeout_handling(self):
        """Test handling of task timeouts."""
        # Create task with short deadline
        task = AgentTask(
            task_id="timeout_test",
            task_type=TaskType.CONTENT_ANALYSIS,
            content=self.mock_content,
            priority=5,
            assigned_agents=["toxicity_detector_001"],
            created_at=datetime.now(),
            deadline=datetime.now() - timedelta(seconds=1),  # Already expired
            context={}
        )
        
        # Check if task is expired
        self.assertTrue(self.ecosystem._is_task_expired(task))
        
        # Test timeout handling
        result = self.ecosystem._handle_task_timeout(task)
        
        self.assertIsInstance(result, ConsensusResult)
        self.assertEqual(result.final_decision, "timeout")
        self.assertIn("timeout", result.reasoning.lower())
    
    def test_agent_health_monitoring(self):
        """Test agent health monitoring and status updates."""
        agent = self.mock_agents['toxicity_detector_001']
        self.ecosystem.register_agent(agent)
        
        # Simulate agent becoming unresponsive
        self.ecosystem._update_agent_status(agent.agent_id, AgentStatus.UNRESPONSIVE)
        
        updated_agent = self.ecosystem.agents[agent.agent_id]
        self.assertEqual(updated_agent.status, AgentStatus.UNRESPONSIVE)
        
        # Test health check
        health_status = self.ecosystem.check_agent_health(agent.agent_id)
        
        self.assertIn('status', health_status)
        self.assertIn('last_active', health_status)
        self.assertIn('response_time', health_status)
        self.assertIn('success_rate', health_status)
    
    def test_batch_task_processing(self):
        """Test batch processing of multiple tasks."""
        # Register agents
        for agent in self.mock_agents.values():
            self.ecosystem.register_agent(agent)
        
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = self.ecosystem.create_task(
                TaskType.CONTENT_ANALYSIS,
                {**self.mock_content, 'content_id': f'batch_content_{i}'},
                priority=5
            )
            tasks.append(task)
        
        with patch('truststream.agent_ecosystem.TrustStreamAgentEcosystem.process_task') as mock_process:
            mock_process.return_value = ConsensusResult(
                final_decision="approve",
                confidence=0.8,
                agreement_score=0.9,
                agent_responses=[],
                reasoning="Batch test result",
                metadata={}
            )
            
            # Process tasks in batch
            results = asyncio.run(self.ecosystem.process_batch_tasks(tasks))
            
            self.assertEqual(len(results), 5)
            self.assertEqual(mock_process.call_count, 5)
            
            for result in results:
                self.assertIn('task_id', result)
                self.assertIn('result', result)
                self.assertIsInstance(result['result'], ConsensusResult)
    
    def test_agent_consensus_weighting(self):
        """Test weighted consensus based on agent performance."""
        # Create responses from agents with different performance levels
        responses = [
            AgentResponse(
                "high_perf_agent", "task_123", "approve", 0.90,
                "High confidence approval", {}, 0.2, datetime.now(), {}
            ),
            AgentResponse(
                "medium_perf_agent", "task_123", "approve", 0.75,
                "Medium confidence approval", {}, 0.4, datetime.now(), {}
            ),
            AgentResponse(
                "low_perf_agent", "task_123", "reject", 0.60,
                "Low confidence rejection", {}, 0.8, datetime.now(), {}
            )
        ]
        
        # Set up agent performance weights
        agent_weights = {
            "high_perf_agent": 0.95,    # High performance weight
            "medium_perf_agent": 0.80,  # Medium performance weight
            "low_perf_agent": 0.65      # Low performance weight
        }
        
        consensus = self.ecosystem._calculate_weighted_consensus(responses, agent_weights)
        
        self.assertIsInstance(consensus, ConsensusResult)
        # Should favor high-performance agent's decision
        self.assertEqual(consensus.final_decision, "approve")
        self.assertGreater(consensus.confidence, 0.75)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Test handling of agent failures
        agent = self.mock_agents['toxicity_detector_001']
        self.ecosystem.register_agent(agent)
        
        # Simulate agent failure
        with patch('truststream.agent_ecosystem.TrustStreamAgentEcosystem._execute_agent_analysis') as mock_execute:
            mock_execute.side_effect = Exception("Agent execution failed")
            
            task = self.ecosystem.create_task(
                TaskType.CONTENT_ANALYSIS,
                self.mock_content,
                priority=5
            )
            
            # Should handle the error gracefully
            result = asyncio.run(self.ecosystem.process_task(task))
            
            self.assertIsInstance(result, ConsensusResult)
            # Should have fallback decision
            self.assertIn(result.final_decision, ["flag", "manual_review"])
    
    def test_performance_optimization(self):
        """Test performance optimization features."""
        # Test agent caching
        agent_id = "toxicity_detector_001"
        self.ecosystem.register_agent(self.mock_agents[agent_id])
        
        # Cache agent analysis result
        content_hash = self.ecosystem._generate_content_hash(self.mock_content)
        cached_response = AgentResponse(
            agent_id, "cached_task", "approve", 0.85,
            "Cached response", {}, 0.1, datetime.now(), {}
        )
        
        self.ecosystem._cache_agent_response(agent_id, content_hash, cached_response)
        
        # Retrieve cached response
        retrieved = self.ecosystem._get_cached_response(agent_id, content_hash)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.decision, "approve")
        
        # Test cache expiration
        expired_response = AgentResponse(
            agent_id, "expired_task", "approve", 0.85,
            "Expired response", {}, 0.1, 
            datetime.now() - timedelta(hours=25), {}  # Expired
        )
        
        expired_hash = "expired_hash"
        self.ecosystem._cache_agent_response(agent_id, expired_hash, expired_response)
        expired_retrieved = self.ecosystem._get_cached_response(agent_id, expired_hash)
        self.assertIsNone(expired_retrieved)  # Should be None due to expiration


class TestAgentEcosystemIntegration(unittest.TestCase):
    """Integration tests for Agent Ecosystem."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.ecosystem = TrustStreamAgentEcosystem()
    
    @patch('truststream.agent_ecosystem.TrustStreamAgentEcosystem._execute_agent_analysis')
    async def test_full_ecosystem_workflow(self, mock_execute):
        """Test complete ecosystem workflow with multiple agents and tasks."""
        # Mock agent responses
        mock_execute.side_effect = [
            AgentResponse(
                "toxicity_detector_001", "integration_task", "approve", 0.88,
                "No toxicity detected", {"toxicity_score": 0.08}, 0.3, datetime.now(), {}
            ),
            AgentResponse(
                "quality_assessor_002", "integration_task", "approve", 0.82,
                "Good quality content", {"quality_score": 4.1}, 0.4, datetime.now(), {}
            ),
            AgentResponse(
                "bias_detector_003", "integration_task", "approve", 0.75,
                "No significant bias", {"bias_score": 0.2}, 0.5, datetime.now(), {}
            )
        ]
        
        # Register diverse agent ecosystem
        agents = [
            Agent(
                "toxicity_detector_001", "Toxicity Detector", AgentType.TOXICITY_DETECTOR,
                "hate_speech_detection", {}, {"accuracy": 0.94}, AgentStatus.ACTIVE,
                datetime.now(), 1000, 940, 0.3
            ),
            Agent(
                "quality_assessor_002", "Quality Assessor", AgentType.QUALITY_ASSESSOR,
                "content_quality", {}, {"accuracy": 0.89}, AgentStatus.ACTIVE,
                datetime.now(), 800, 712, 0.4
            ),
            Agent(
                "bias_detector_003", "Bias Detector", AgentType.BIAS_DETECTOR,
                "bias_analysis", {}, {"accuracy": 0.86}, AgentStatus.ACTIVE,
                datetime.now(), 600, 516, 0.5
            )
        ]
        
        for agent in agents:
            self.ecosystem.register_agent(agent)
        
        # Create comprehensive analysis task
        content = {
            'content_id': 'integration_test_content',
            'text': 'This is a comprehensive test of the agent ecosystem integration.',
            'author_id': 'integration_test_user',
            'content_type': 'post',
            'metadata': {
                'community': 'test_community',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        task = self.ecosystem.create_task(
            TaskType.COMPREHENSIVE_ANALYSIS,
            content,
            priority=9,
            context={
                'community_rules': ['no_hate_speech', 'high_quality_only'],
                'author_trust_score': 0.75
            }
        )
        
        # Process task through ecosystem
        result = await self.ecosystem.process_task(task)
        
        # Verify comprehensive analysis
        self.assertIsInstance(result, ConsensusResult)
        self.assertEqual(result.final_decision, "approve")
        self.assertEqual(len(result.agent_responses), 3)
        self.assertGreater(result.confidence, 0.7)
        self.assertGreater(result.agreement_score, 0.8)
        
        # Verify all agent types participated
        agent_types_used = [
            self.ecosystem.agents[resp.agent_id].agent_type 
            for resp in result.agent_responses
        ]
        self.assertIn(AgentType.TOXICITY_DETECTOR, agent_types_used)
        self.assertIn(AgentType.QUALITY_ASSESSOR, agent_types_used)
        self.assertIn(AgentType.BIAS_DETECTOR, agent_types_used)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)