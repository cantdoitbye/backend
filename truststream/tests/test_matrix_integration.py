# truststream/tests/test_matrix_integration.py

"""
Unit Tests for TrustStream Matrix Integration

This module contains comprehensive unit tests for the Matrix Integration,
testing real-time moderation, room management, user interactions,
automated actions, and Matrix protocol compliance.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from datetime import datetime, timedelta

from truststream.matrix_integration import (
    MatrixModerationBot, MatrixEvent, ModerationAction, 
    RoomConfig, UserTrustData, ModerationDecision
)


class TestMatrixEvent(unittest.TestCase):
    """Test cases for MatrixEvent data class."""
    
    def test_matrix_event_creation(self):
        """Test MatrixEvent creation with complete data."""
        event = MatrixEvent(
            event_id="$event_12345:matrix.org",
            room_id="!room_abc:matrix.org",
            sender="@user123:matrix.org",
            event_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": "Hello, this is a test message!"
            },
            timestamp=datetime.now(),
            origin_server_ts=1640995200000,
            unsigned={},
            prev_content=None
        )
        
        self.assertEqual(event.event_id, "$event_12345:matrix.org")
        self.assertEqual(event.room_id, "!room_abc:matrix.org")
        self.assertEqual(event.sender, "@user123:matrix.org")
        self.assertEqual(event.event_type, "m.room.message")
        self.assertIn("msgtype", event.content)
        self.assertEqual(event.content["body"], "Hello, this is a test message!")


class TestModerationAction(unittest.TestCase):
    """Test cases for ModerationAction data class."""
    
    def test_moderation_action_creation(self):
        """Test ModerationAction creation with all fields."""
        action = ModerationAction(
            action_type="warn",
            target_user="@problematic_user:matrix.org",
            room_id="!room_abc:matrix.org",
            reason="Inappropriate language detected",
            severity=6,
            duration=timedelta(hours=24),
            automated=True,
            confidence=0.85,
            evidence={
                "flagged_content": "This is inappropriate content",
                "toxicity_score": 0.78,
                "rule_violations": ["inappropriate_language"]
            },
            timestamp=datetime.now()
        )
        
        self.assertEqual(action.action_type, "warn")
        self.assertEqual(action.target_user, "@problematic_user:matrix.org")
        self.assertEqual(action.room_id, "!room_abc:matrix.org")
        self.assertEqual(action.severity, 6)
        self.assertTrue(action.automated)
        self.assertEqual(action.confidence, 0.85)
        self.assertIn("toxicity_score", action.evidence)


class TestRoomConfig(unittest.TestCase):
    """Test cases for RoomConfig data class."""
    
    def test_room_config_creation(self):
        """Test RoomConfig creation with comprehensive settings."""
        config = RoomConfig(
            room_id="!room_abc:matrix.org",
            moderation_enabled=True,
            auto_moderation_threshold=0.8,
            escalation_threshold=0.9,
            allowed_actions=["warn", "mute", "kick"],
            community_rules=[
                "No hate speech or harassment",
                "Keep discussions constructive",
                "No spam or excessive self-promotion"
            ],
            trust_score_requirements={
                "min_trust_to_post": 0.3,
                "min_trust_for_media": 0.5,
                "trusted_user_threshold": 0.8
            },
            rate_limits={
                "messages_per_minute": 10,
                "media_per_hour": 5
            },
            custom_settings={
                "language_filter_enabled": True,
                "link_preview_allowed": False,
                "file_upload_max_size": "10MB"
            }
        )
        
        self.assertEqual(config.room_id, "!room_abc:matrix.org")
        self.assertTrue(config.moderation_enabled)
        self.assertEqual(config.auto_moderation_threshold, 0.8)
        self.assertIn("warn", config.allowed_actions)
        self.assertEqual(len(config.community_rules), 3)
        self.assertIn("min_trust_to_post", config.trust_score_requirements)
        self.assertIn("messages_per_minute", config.rate_limits)


class TestMatrixModerationBot(unittest.TestCase):
    """Test cases for MatrixModerationBot main class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bot_config = {
            'homeserver': 'https://matrix.org',
            'username': '@truststream_bot:matrix.org',
            'access_token': 'test_access_token',
            'device_id': 'TRUSTSTREAM_BOT'
        }
        
        self.bot = MatrixModerationBot(self.bot_config)
        
        # Mock room configuration
        self.mock_room_config = RoomConfig(
            room_id="!test_room:matrix.org",
            moderation_enabled=True,
            auto_moderation_threshold=0.7,
            escalation_threshold=0.9,
            allowed_actions=["warn", "mute", "kick", "ban"],
            community_rules=["No hate speech", "Be respectful"],
            trust_score_requirements={"min_trust_to_post": 0.2},
            rate_limits={"messages_per_minute": 15},
            custom_settings={}
        )
        
        # Mock Matrix event
        self.mock_event = MatrixEvent(
            event_id="$test_event:matrix.org",
            room_id="!test_room:matrix.org",
            sender="@test_user:matrix.org",
            event_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": "This is a test message for moderation."
            },
            timestamp=datetime.now(),
            origin_server_ts=1640995200000,
            unsigned={},
            prev_content=None
        )
    
    def test_bot_initialization(self):
        """Test MatrixModerationBot initialization."""
        self.assertIsInstance(self.bot, MatrixModerationBot)
        self.assertEqual(self.bot.homeserver, 'https://matrix.org')
        self.assertEqual(self.bot.username, '@truststream_bot:matrix.org')
        self.assertIsInstance(self.bot.room_configs, dict)
        self.assertIsInstance(self.bot.user_trust_cache, dict)
        self.assertIsInstance(self.bot.moderation_history, list)
    
    @patch('nio.AsyncClient')
    async def test_bot_startup(self, mock_client):
        """Test bot startup and Matrix client initialization."""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.login.return_value = Mock(access_token="test_token")
        mock_client_instance.sync.return_value = Mock()
        
        await self.bot.start()
        
        mock_client.assert_called_once()
        mock_client_instance.login.assert_called_once()
        self.assertTrue(self.bot.is_running)
    
    def test_room_configuration(self):
        """Test room configuration management."""
        # Add room configuration
        self.bot.configure_room(self.mock_room_config)
        
        self.assertIn(self.mock_room_config.room_id, self.bot.room_configs)
        stored_config = self.bot.room_configs[self.mock_room_config.room_id]
        self.assertEqual(stored_config.auto_moderation_threshold, 0.7)
        
        # Update room configuration
        updated_config = RoomConfig(
            room_id="!test_room:matrix.org",
            moderation_enabled=True,
            auto_moderation_threshold=0.8,  # Changed
            escalation_threshold=0.9,
            allowed_actions=["warn", "mute"],  # Reduced actions
            community_rules=["No hate speech", "Be respectful", "No spam"],  # Added rule
            trust_score_requirements={"min_trust_to_post": 0.3},  # Increased
            rate_limits={"messages_per_minute": 10},  # Reduced
            custom_settings={}
        )
        
        self.bot.configure_room(updated_config)
        updated_stored = self.bot.room_configs[updated_config.room_id]
        self.assertEqual(updated_stored.auto_moderation_threshold, 0.8)
        self.assertEqual(len(updated_stored.allowed_actions), 2)
        self.assertEqual(len(updated_stored.community_rules), 3)
    
    @patch('truststream.matrix_integration.MatrixModerationBot._analyze_content_with_truststream')
    async def test_message_analysis(self, mock_analyze):
        """Test message content analysis."""
        # Mock TrustStream analysis result
        mock_analyze.return_value = {
            'decision': 'approve',
            'confidence': 0.85,
            'trust_score': 0.75,
            'analysis_details': {
                'toxicity_score': 0.1,
                'quality_score': 4.2,
                'safety_indicators': ['appropriate_language']
            },
            'reasoning': 'Content appears safe and appropriate'
        }
        
        # Configure room
        self.bot.configure_room(self.mock_room_config)
        
        # Analyze message
        result = await self.bot._analyze_message(self.mock_event)
        
        self.assertIsInstance(result, ModerationDecision)
        self.assertEqual(result.decision, 'approve')
        self.assertEqual(result.confidence, 0.85)
        self.assertIn('toxicity_score', result.analysis_details)
        mock_analyze.assert_called_once()
    
    @patch('truststream.matrix_integration.MatrixModerationBot._send_matrix_message')
    async def test_warning_action(self, mock_send):
        """Test warning action execution."""
        mock_send.return_value = True
        
        action = ModerationAction(
            action_type="warn",
            target_user="@test_user:matrix.org",
            room_id="!test_room:matrix.org",
            reason="Inappropriate language detected",
            severity=5,
            duration=None,
            automated=True,
            confidence=0.8,
            evidence={"toxicity_score": 0.7},
            timestamp=datetime.now()
        )
        
        result = await self.bot._execute_warning(action)
        
        self.assertTrue(result)
        mock_send.assert_called_once()
        # Verify warning was logged
        self.assertGreater(len(self.bot.moderation_history), 0)
        logged_action = self.bot.moderation_history[-1]
        self.assertEqual(logged_action.action_type, "warn")
        self.assertEqual(logged_action.target_user, "@test_user:matrix.org")
    
    @patch('nio.AsyncClient.room_ban')
    async def test_ban_action(self, mock_ban):
        """Test ban action execution."""
        mock_ban.return_value = Mock(transport_response=Mock(status=200))
        
        action = ModerationAction(
            action_type="ban",
            target_user="@problematic_user:matrix.org",
            room_id="!test_room:matrix.org",
            reason="Severe rule violation",
            severity=10,
            duration=timedelta(days=7),
            automated=False,
            confidence=0.95,
            evidence={"multiple_violations": True},
            timestamp=datetime.now()
        )
        
        # Mock Matrix client
        self.bot.client = Mock()
        self.bot.client.room_ban = mock_ban
        
        result = await self.bot._execute_ban(action)
        
        self.assertTrue(result)
        mock_ban.assert_called_once_with(
            action.room_id, 
            action.target_user, 
            reason=action.reason
        )
    
    def test_user_trust_caching(self):
        """Test user trust score caching mechanism."""
        user_id = "@test_user:matrix.org"
        trust_data = UserTrustData(
            user_id=user_id,
            trust_score=0.75,
            reputation_score=0.82,
            behavioral_indicators={
                "message_quality_avg": 4.1,
                "community_engagement": 0.8,
                "rule_violations": 0
            },
            last_updated=datetime.now(),
            cache_expiry=datetime.now() + timedelta(hours=1)
        )
        
        # Cache user trust data
        self.bot._cache_user_trust(trust_data)
        
        self.assertIn(user_id, self.bot.user_trust_cache)
        cached_data = self.bot.user_trust_cache[user_id]
        self.assertEqual(cached_data.trust_score, 0.75)
        
        # Retrieve cached data
        retrieved = self.bot._get_cached_user_trust(user_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.trust_score, 0.75)
        
        # Test cache expiration
        expired_data = UserTrustData(
            user_id="@expired_user:matrix.org",
            trust_score=0.6,
            reputation_score=0.7,
            behavioral_indicators={},
            last_updated=datetime.now() - timedelta(hours=2),
            cache_expiry=datetime.now() - timedelta(hours=1)  # Expired
        )
        
        self.bot._cache_user_trust(expired_data)
        expired_retrieved = self.bot._get_cached_user_trust("@expired_user:matrix.org")
        self.assertIsNone(expired_retrieved)  # Should be None due to expiration
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        room_id = "!test_room:matrix.org"
        user_id = "@test_user:matrix.org"
        
        # Configure room with rate limits
        self.bot.configure_room(self.mock_room_config)
        
        # Initialize rate limiting for user
        self.bot._initialize_rate_limiting(room_id, user_id)
        
        # Test within rate limit
        for i in range(10):  # Within limit of 15 messages per minute
            allowed = self.bot._check_rate_limit(room_id, user_id, "message")
            self.assertTrue(allowed)
            self.bot._record_user_action(room_id, user_id, "message")
        
        # Test exceeding rate limit
        for i in range(10):  # This should exceed the limit
            allowed = self.bot._check_rate_limit(room_id, user_id, "message")
            if i < 5:  # First few should still be allowed
                self.assertTrue(allowed)
            else:  # Later ones should be blocked
                self.assertFalse(allowed)
            self.bot._record_user_action(room_id, user_id, "message")
    
    @patch('truststream.matrix_integration.MatrixModerationBot._analyze_message')
    async def test_event_processing_pipeline(self, mock_analyze):
        """Test complete event processing pipeline."""
        # Mock analysis result that triggers moderation
        mock_analyze.return_value = ModerationDecision(
            decision="flag",
            confidence=0.85,
            trust_score=0.4,
            analysis_details={
                "toxicity_score": 0.8,
                "rule_violations": ["inappropriate_language"]
            },
            reasoning="High toxicity detected",
            recommended_action="warn",
            escalate_to_human=False
        )
        
        # Configure room
        self.bot.configure_room(self.mock_room_config)
        
        with patch('truststream.matrix_integration.MatrixModerationBot._execute_moderation_action') as mock_execute:
            mock_execute.return_value = True
            
            # Process event
            await self.bot._process_room_event(self.mock_event)
            
            # Verify analysis was called
            mock_analyze.assert_called_once_with(self.mock_event)
            
            # Verify moderation action was executed
            mock_execute.assert_called_once()
            executed_action = mock_execute.call_args[0][0]
            self.assertEqual(executed_action.action_type, "warn")
            self.assertEqual(executed_action.target_user, "@test_user:matrix.org")
    
    def test_escalation_logic(self):
        """Test escalation to human moderators."""
        # High-confidence decision that should escalate
        high_risk_decision = ModerationDecision(
            decision="flag",
            confidence=0.95,  # Above escalation threshold
            trust_score=0.2,
            analysis_details={
                "toxicity_score": 0.95,
                "hate_speech_probability": 0.9,
                "rule_violations": ["hate_speech", "harassment"]
            },
            reasoning="Severe rule violations detected",
            recommended_action="ban",
            escalate_to_human=True
        )
        
        should_escalate = self.bot._should_escalate_to_human(
            high_risk_decision, 
            self.mock_room_config
        )
        
        self.assertTrue(should_escalate)
        
        # Low-confidence decision that should not escalate
        low_risk_decision = ModerationDecision(
            decision="approve",
            confidence=0.6,  # Below escalation threshold
            trust_score=0.8,
            analysis_details={"toxicity_score": 0.1},
            reasoning="Content appears safe",
            recommended_action="none",
            escalate_to_human=False
        )
        
        should_not_escalate = self.bot._should_escalate_to_human(
            low_risk_decision, 
            self.mock_room_config
        )
        
        self.assertFalse(should_not_escalate)
    
    @patch('truststream.matrix_integration.MatrixModerationBot._send_matrix_message')
    async def test_human_escalation_notification(self, mock_send):
        """Test human moderator escalation notifications."""
        mock_send.return_value = True
        
        escalation_data = {
            'event': self.mock_event,
            'decision': ModerationDecision(
                decision="flag",
                confidence=0.95,
                trust_score=0.2,
                analysis_details={"toxicity_score": 0.9},
                reasoning="Severe violation detected",
                recommended_action="ban",
                escalate_to_human=True
            ),
            'urgency': 'high'
        }
        
        result = await self.bot._escalate_to_human_moderators(escalation_data)
        
        self.assertTrue(result)
        mock_send.assert_called()
        
        # Verify escalation was logged
        self.assertGreater(len(self.bot.escalation_queue), 0)
        escalated_item = self.bot.escalation_queue[-1]
        self.assertEqual(escalated_item['urgency'], 'high')
        self.assertEqual(escalated_item['event'].event_id, self.mock_event.event_id)
    
    def test_cross_room_coordination(self):
        """Test cross-room moderation coordination."""
        # Configure multiple rooms
        room1_config = RoomConfig(
            room_id="!room1:matrix.org",
            moderation_enabled=True,
            auto_moderation_threshold=0.7,
            escalation_threshold=0.9,
            allowed_actions=["warn", "mute"],
            community_rules=["No spam"],
            trust_score_requirements={},
            rate_limits={},
            custom_settings={}
        )
        
        room2_config = RoomConfig(
            room_id="!room2:matrix.org",
            moderation_enabled=True,
            auto_moderation_threshold=0.8,
            escalation_threshold=0.9,
            allowed_actions=["warn", "kick", "ban"],
            community_rules=["No hate speech"],
            trust_score_requirements={},
            rate_limits={},
            custom_settings={}
        )
        
        self.bot.configure_room(room1_config)
        self.bot.configure_room(room2_config)
        
        # Record violation in room1
        violation = {
            'user_id': '@problematic_user:matrix.org',
            'room_id': '!room1:matrix.org',
            'violation_type': 'spam',
            'severity': 7,
            'timestamp': datetime.now()
        }
        
        self.bot._record_cross_room_violation(violation)
        
        # Check if user's violations are tracked across rooms
        user_violations = self.bot._get_user_violations_across_rooms('@problematic_user:matrix.org')
        
        self.assertEqual(len(user_violations), 1)
        self.assertEqual(user_violations[0]['room_id'], '!room1:matrix.org')
        
        # Test cross-room action recommendation
        recommendation = self.bot._get_cross_room_action_recommendation(
            '@problematic_user:matrix.org',
            '!room2:matrix.org'
        )
        
        self.assertIsNotNone(recommendation)
        self.assertIn('action_type', recommendation)
        self.assertIn('reason', recommendation)
    
    def test_audit_logging(self):
        """Test comprehensive audit logging."""
        # Execute a moderation action
        action = ModerationAction(
            action_type="mute",
            target_user="@test_user:matrix.org",
            room_id="!test_room:matrix.org",
            reason="Excessive messaging",
            severity=4,
            duration=timedelta(minutes=30),
            automated=True,
            confidence=0.8,
            evidence={"rate_limit_exceeded": True},
            timestamp=datetime.now()
        )
        
        # Log the action
        self.bot._log_moderation_action(action)
        
        # Verify logging
        self.assertGreater(len(self.bot.moderation_history), 0)
        logged_action = self.bot.moderation_history[-1]
        self.assertEqual(logged_action.action_type, "mute")
        self.assertEqual(logged_action.target_user, "@test_user:matrix.org")
        
        # Test audit trail retrieval
        user_audit_trail = self.bot.get_user_audit_trail("@test_user:matrix.org")
        self.assertEqual(len(user_audit_trail), 1)
        self.assertEqual(user_audit_trail[0].action_type, "mute")
        
        room_audit_trail = self.bot.get_room_audit_trail("!test_room:matrix.org")
        self.assertEqual(len(room_audit_trail), 1)
        self.assertEqual(room_audit_trail[0].room_id, "!test_room:matrix.org")
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Initialize metrics
        self.bot._initialize_performance_metrics()
        
        # Record some metrics
        self.bot._record_performance_metric('analysis_time', 0.3)
        self.bot._record_performance_metric('analysis_time', 0.5)
        self.bot._record_performance_metric('analysis_time', 0.2)
        
        self.bot._record_performance_metric('action_execution_time', 0.1)
        self.bot._record_performance_metric('action_execution_time', 0.15)
        
        metrics = self.bot.get_performance_metrics()
        
        self.assertIn('analysis_time', metrics)
        self.assertIn('action_execution_time', metrics)
        
        # Check analysis time metrics
        analysis_metrics = metrics['analysis_time']
        self.assertAlmostEqual(analysis_metrics['average'], 0.33, places=1)
        self.assertEqual(analysis_metrics['min'], 0.2)
        self.assertEqual(analysis_metrics['max'], 0.5)
        self.assertEqual(analysis_metrics['count'], 3)
    
    def test_error_handling(self):
        """Test error handling and recovery mechanisms."""
        # Test handling of malformed events
        malformed_event = MatrixEvent(
            event_id="$malformed:matrix.org",
            room_id="!test_room:matrix.org",
            sender="@test_user:matrix.org",
            event_type="m.room.message",
            content={},  # Missing required content
            timestamp=datetime.now(),
            origin_server_ts=1640995200000,
            unsigned={},
            prev_content=None
        )
        
        # Should handle gracefully without crashing
        result = asyncio.run(self.bot._process_room_event(malformed_event))
        self.assertIsNone(result)  # Should return None for malformed events
        
        # Test handling of network errors
        with patch('truststream.matrix_integration.MatrixModerationBot._analyze_content_with_truststream') as mock_analyze:
            mock_analyze.side_effect = Exception("Network error")
            
            # Should handle the error gracefully
            result = asyncio.run(self.bot._analyze_message(self.mock_event))
            
            # Should return a safe default decision
            self.assertIsInstance(result, ModerationDecision)
            self.assertEqual(result.decision, "manual_review")


class TestMatrixIntegrationIntegration(unittest.TestCase):
    """Integration tests for Matrix Integration."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.bot_config = {
            'homeserver': 'https://matrix.org',
            'username': '@truststream_bot:matrix.org',
            'access_token': 'test_access_token',
            'device_id': 'TRUSTSTREAM_BOT'
        }
        self.bot = MatrixModerationBot(self.bot_config)
    
    @patch('nio.AsyncClient')
    @patch('truststream.matrix_integration.MatrixModerationBot._analyze_content_with_truststream')
    async def test_full_moderation_workflow(self, mock_analyze, mock_client):
        """Test complete moderation workflow from event to action."""
        # Mock Matrix client
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.room_ban = AsyncMock(return_value=Mock(transport_response=Mock(status=200)))
        mock_client_instance.room_kick = AsyncMock(return_value=Mock(transport_response=Mock(status=200)))
        
        self.bot.client = mock_client_instance
        
        # Mock TrustStream analysis
        mock_analyze.return_value = {
            'decision': 'flag',
            'confidence': 0.9,
            'trust_score': 0.2,
            'analysis_details': {
                'toxicity_score': 0.85,
                'hate_speech_probability': 0.8,
                'rule_violations': ['hate_speech']
            },
            'reasoning': 'Hate speech detected with high confidence'
        }
        
        # Configure room
        room_config = RoomConfig(
            room_id="!integration_room:matrix.org",
            moderation_enabled=True,
            auto_moderation_threshold=0.7,
            escalation_threshold=0.95,
            allowed_actions=["warn", "mute", "kick", "ban"],
            community_rules=["No hate speech"],
            trust_score_requirements={"min_trust_to_post": 0.3},
            rate_limits={"messages_per_minute": 20},
            custom_settings={}
        )
        
        self.bot.configure_room(room_config)
        
        # Create problematic event
        problematic_event = MatrixEvent(
            event_id="$problematic_event:matrix.org",
            room_id="!integration_room:matrix.org",
            sender="@problematic_user:matrix.org",
            event_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": "This is hate speech content that should be moderated"
            },
            timestamp=datetime.now(),
            origin_server_ts=1640995200000,
            unsigned={},
            prev_content=None
        )
        
        # Process the event through the full pipeline
        with patch('truststream.matrix_integration.MatrixModerationBot._send_matrix_message') as mock_send:
            mock_send.return_value = True
            
            await self.bot._process_room_event(problematic_event)
            
            # Verify analysis was performed
            mock_analyze.assert_called_once()
            
            # Verify moderation action was taken
            self.assertGreater(len(self.bot.moderation_history), 0)
            
            # Verify the action was appropriate for the severity
            action = self.bot.moderation_history[-1]
            self.assertIn(action.action_type, ["kick", "ban"])  # High severity action
            self.assertEqual(action.target_user, "@problematic_user:matrix.org")
            self.assertGreater(action.confidence, 0.8)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)