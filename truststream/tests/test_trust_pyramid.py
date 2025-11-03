# truststream/tests/test_trust_pyramid.py

"""
Unit Tests for TrustStream Trust Pyramid Calculator

This module contains comprehensive unit tests for the Trust Pyramid Calculator,
testing all aspects of the 4-layer trust scoring system including individual
layer calculations, overall scoring, ranking, and behavioral adjustments.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from truststream.trust_pyramid import (
    TrustPyramidCalculator, TrustLayer, TrustScore, TrustProfile
)


class TestTrustLayer(unittest.TestCase):
    """Test cases for TrustLayer data class."""
    
    def test_trust_layer_creation(self):
        """Test TrustLayer creation with valid values."""
        layer = TrustLayer(
            iq=4.2,
            appeal=3.8,
            social=4.0,
            humanity=3.5
        )
        
        self.assertEqual(layer.iq, 4.2)
        self.assertEqual(layer.appeal, 3.8)
        self.assertEqual(layer.social, 4.0)
        self.assertEqual(layer.humanity, 3.5)
    
    def test_trust_layer_validation(self):
        """Test TrustLayer validation for score ranges."""
        # Valid scores should work
        layer = TrustLayer(iq=5.0, appeal=0.0, social=2.5, humanity=1.0)
        self.assertIsInstance(layer, TrustLayer)
        
        # Test boundary values
        layer_min = TrustLayer(iq=0.0, appeal=0.0, social=0.0, humanity=0.0)
        layer_max = TrustLayer(iq=5.0, appeal=5.0, social=5.0, humanity=5.0)
        
        self.assertIsInstance(layer_min, TrustLayer)
        self.assertIsInstance(layer_max, TrustLayer)


class TestTrustScore(unittest.TestCase):
    """Test cases for TrustScore data class."""
    
    def test_trust_score_creation(self):
        """Test TrustScore creation with all components."""
        layers = TrustLayer(iq=4.0, appeal=3.5, social=4.2, humanity=3.8)
        
        score = TrustScore(
            layers=layers,
            overall_score=3.875,
            confidence=0.85,
            rank='gold',
            percentile=78.5
        )
        
        self.assertEqual(score.layers, layers)
        self.assertEqual(score.overall_score, 3.875)
        self.assertEqual(score.confidence, 0.85)
        self.assertEqual(score.rank, 'gold')
        self.assertEqual(score.percentile, 78.5)


class TestTrustProfile(unittest.TestCase):
    """Test cases for TrustProfile data class."""
    
    def test_trust_profile_creation(self):
        """Test TrustProfile creation with complete data."""
        layers = TrustLayer(iq=4.0, appeal=3.5, social=4.2, humanity=3.8)
        score = TrustScore(
            layers=layers,
            overall_score=3.875,
            confidence=0.85,
            rank='gold',
            percentile=78.5
        )
        
        profile = TrustProfile(
            user_id="user123",
            current_score=score,
            historical_scores=[score],
            behavioral_patterns={'consistency': 0.8},
            last_updated=datetime.now()
        )
        
        self.assertEqual(profile.user_id, "user123")
        self.assertEqual(profile.current_score, score)
        self.assertEqual(len(profile.historical_scores), 1)
        self.assertIn('consistency', profile.behavioral_patterns)


class TestTrustPyramidCalculator(unittest.TestCase):
    """Test cases for TrustPyramidCalculator main class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = TrustPyramidCalculator()
        
        # Mock user data
        self.mock_user_data = {
            'user_id': 'test_user_123',
            'content_quality': 4.2,
            'engagement_metrics': {
                'likes_received': 150,
                'comments_received': 45,
                'shares_received': 20,
                'meaningful_interactions': 80
            },
            'social_connections': {
                'followers': 500,
                'following': 200,
                'mutual_connections': 150,
                'community_memberships': 5
            },
            'behavioral_data': {
                'account_age_days': 365,
                'posting_frequency': 0.8,
                'response_time_hours': 2.5,
                'authenticity_indicators': ['verified_email', 'phone_verified']
            },
            'violation_history': [],
            'peer_endorsements': 12
        }
        
        # Mock content data
        self.mock_content_data = {
            'content_id': 'post_456',
            'text': 'This is a high-quality, informative post about technology.',
            'engagement': {
                'likes': 25,
                'comments': 8,
                'shares': 3
            },
            'author_trust_score': 4.0,
            'topic_relevance': 0.9,
            'readability_score': 0.85
        }
    
    def test_calculator_initialization(self):
        """Test TrustPyramidCalculator initialization."""
        self.assertIsInstance(self.calculator, TrustPyramidCalculator)
        self.assertEqual(len(self.calculator.layer_weights), 4)
        self.assertAlmostEqual(sum(self.calculator.layer_weights.values()), 1.0)
    
    def test_calculate_iq_layer(self):
        """Test IQ layer calculation."""
        iq_score = self.calculator._calculate_iq_layer(self.mock_user_data)
        
        self.assertIsInstance(iq_score, float)
        self.assertGreaterEqual(iq_score, 0.0)
        self.assertLessEqual(iq_score, 5.0)
        
        # Test with high-quality content
        high_quality_data = self.mock_user_data.copy()
        high_quality_data['content_quality'] = 4.8
        high_iq_score = self.calculator._calculate_iq_layer(high_quality_data)
        
        self.assertGreater(high_iq_score, iq_score)
    
    def test_calculate_appeal_layer(self):
        """Test Appeal layer calculation."""
        appeal_score = self.calculator._calculate_appeal_layer(self.mock_user_data)
        
        self.assertIsInstance(appeal_score, float)
        self.assertGreaterEqual(appeal_score, 0.0)
        self.assertLessEqual(appeal_score, 5.0)
        
        # Test with higher engagement
        high_engagement_data = self.mock_user_data.copy()
        high_engagement_data['engagement_metrics']['likes_received'] = 500
        high_appeal_score = self.calculator._calculate_appeal_layer(high_engagement_data)
        
        self.assertGreater(high_appeal_score, appeal_score)
    
    def test_calculate_social_layer(self):
        """Test Social layer calculation."""
        social_score = self.calculator._calculate_social_layer(self.mock_user_data)
        
        self.assertIsInstance(social_score, float)
        self.assertGreaterEqual(social_score, 0.0)
        self.assertLessEqual(social_score, 5.0)
        
        # Test with more social connections
        high_social_data = self.mock_user_data.copy()
        high_social_data['social_connections']['followers'] = 2000
        high_social_score = self.calculator._calculate_social_layer(high_social_data)
        
        self.assertGreater(high_social_score, social_score)
    
    def test_calculate_humanity_layer(self):
        """Test Humanity layer calculation."""
        humanity_score = self.calculator._calculate_humanity_layer(self.mock_user_data)
        
        self.assertIsInstance(humanity_score, float)
        self.assertGreaterEqual(humanity_score, 0.0)
        self.assertLessEqual(humanity_score, 5.0)
        
        # Test with longer account age
        older_account_data = self.mock_user_data.copy()
        older_account_data['behavioral_data']['account_age_days'] = 1000
        higher_humanity_score = self.calculator._calculate_humanity_layer(older_account_data)
        
        self.assertGreater(higher_humanity_score, humanity_score)
    
    def test_calculate_user_trust_score(self):
        """Test complete user trust score calculation."""
        trust_score = self.calculator.calculate_user_trust_score(self.mock_user_data)
        
        self.assertIsInstance(trust_score, TrustScore)
        self.assertIsInstance(trust_score.layers, TrustLayer)
        self.assertGreaterEqual(trust_score.overall_score, 0.0)
        self.assertLessEqual(trust_score.overall_score, 5.0)
        self.assertGreaterEqual(trust_score.confidence, 0.0)
        self.assertLessEqual(trust_score.confidence, 1.0)
        self.assertIn(trust_score.rank, ['bronze', 'silver', 'gold', 'platinum', 'diamond'])
        self.assertGreaterEqual(trust_score.percentile, 0.0)
        self.assertLessEqual(trust_score.percentile, 100.0)
    
    def test_determine_trust_rank(self):
        """Test trust rank determination."""
        # Test different score ranges
        self.assertEqual(self.calculator._determine_trust_rank(0.5), 'bronze')
        self.assertEqual(self.calculator._determine_trust_rank(1.5), 'bronze')
        self.assertEqual(self.calculator._determine_trust_rank(2.5), 'silver')
        self.assertEqual(self.calculator._determine_trust_rank(3.5), 'gold')
        self.assertEqual(self.calculator._determine_trust_rank(4.2), 'platinum')
        self.assertEqual(self.calculator._determine_trust_rank(4.8), 'diamond')
        
        # Test boundary values
        self.assertEqual(self.calculator._determine_trust_rank(2.0), 'bronze')
        self.assertEqual(self.calculator._determine_trust_rank(3.0), 'silver')
        self.assertEqual(self.calculator._determine_trust_rank(4.0), 'gold')
        self.assertEqual(self.calculator._determine_trust_rank(4.5), 'platinum')
    
    def test_analyze_content_quality(self):
        """Test content quality analysis."""
        quality_score = self.calculator.analyze_content_quality(self.mock_content_data)
        
        self.assertIsInstance(quality_score, dict)
        self.assertIn('overall_quality', quality_score)
        self.assertIn('trust_impact', quality_score)
        self.assertIn('quality_factors', quality_score)
        
        self.assertGreaterEqual(quality_score['overall_quality'], 0.0)
        self.assertLessEqual(quality_score['overall_quality'], 5.0)
    
    def test_apply_behavioral_adjustments(self):
        """Test behavioral adjustments to trust scores."""
        base_score = 3.5
        
        # Test positive behavioral patterns
        positive_patterns = {
            'consistency_score': 0.9,
            'authenticity_indicators': 0.8,
            'community_contribution': 0.85
        }
        
        adjusted_score = self.calculator._apply_behavioral_adjustments(
            base_score, positive_patterns
        )
        
        self.assertGreater(adjusted_score, base_score)
        self.assertLessEqual(adjusted_score, 5.0)
        
        # Test negative behavioral patterns
        negative_patterns = {
            'consistency_score': 0.3,
            'authenticity_indicators': 0.2,
            'community_contribution': 0.1
        }
        
        adjusted_score_negative = self.calculator._apply_behavioral_adjustments(
            base_score, negative_patterns
        )
        
        self.assertLess(adjusted_score_negative, base_score)
        self.assertGreaterEqual(adjusted_score_negative, 0.0)
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        # Test with sufficient data
        sufficient_data = self.mock_user_data.copy()
        confidence = self.calculator._calculate_confidence_score(sufficient_data)
        
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        # Test with limited data
        limited_data = {
            'user_id': 'new_user',
            'content_quality': 2.0,
            'engagement_metrics': {'likes_received': 5},
            'social_connections': {'followers': 10},
            'behavioral_data': {'account_age_days': 7}
        }
        
        limited_confidence = self.calculator._calculate_confidence_score(limited_data)
        self.assertLess(limited_confidence, confidence)
    
    def test_get_trust_profile(self):
        """Test trust profile retrieval and creation."""
        profile = self.calculator.get_trust_profile('test_user_123', self.mock_user_data)
        
        self.assertIsInstance(profile, TrustProfile)
        self.assertEqual(profile.user_id, 'test_user_123')
        self.assertIsInstance(profile.current_score, TrustScore)
        self.assertIsInstance(profile.last_updated, datetime)
    
    def test_update_trust_profile(self):
        """Test trust profile updates."""
        # Create initial profile
        initial_profile = self.calculator.get_trust_profile('test_user_123', self.mock_user_data)
        
        # Update with new data
        updated_data = self.mock_user_data.copy()
        updated_data['content_quality'] = 4.8
        
        updated_profile = self.calculator.update_trust_profile(
            'test_user_123', updated_data, initial_profile
        )
        
        self.assertIsInstance(updated_profile, TrustProfile)
        self.assertGreater(len(updated_profile.historical_scores), 1)
        self.assertGreater(
            updated_profile.current_score.overall_score,
            initial_profile.current_score.overall_score
        )
    
    def test_batch_calculate_trust_scores(self):
        """Test batch calculation of trust scores."""
        users_data = [
            {'user_id': 'user1', **self.mock_user_data},
            {'user_id': 'user2', **self.mock_user_data},
            {'user_id': 'user3', **self.mock_user_data}
        ]
        
        batch_results = self.calculator.batch_calculate_trust_scores(users_data)
        
        self.assertEqual(len(batch_results), 3)
        for result in batch_results:
            self.assertIn('user_id', result)
            self.assertIn('trust_score', result)
            self.assertIsInstance(result['trust_score'], TrustScore)
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with minimal data
        minimal_data = {'user_id': 'minimal_user'}
        
        try:
            score = self.calculator.calculate_user_trust_score(minimal_data)
            self.assertIsInstance(score, TrustScore)
            # Should have low confidence
            self.assertLess(score.confidence, 0.5)
        except Exception as e:
            self.fail(f"Calculator should handle minimal data gracefully: {e}")
        
        # Test with invalid data types
        invalid_data = {
            'user_id': 'invalid_user',
            'content_quality': 'invalid',
            'engagement_metrics': None
        }
        
        try:
            score = self.calculator.calculate_user_trust_score(invalid_data)
            self.assertIsInstance(score, TrustScore)
        except Exception as e:
            self.fail(f"Calculator should handle invalid data gracefully: {e}")
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks for trust calculations."""
        import time
        
        # Test single calculation performance
        start_time = time.time()
        self.calculator.calculate_user_trust_score(self.mock_user_data)
        single_calc_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(single_calc_time, 1.0)  # Less than 1 second
        
        # Test batch calculation performance
        batch_data = [self.mock_user_data.copy() for _ in range(100)]
        for i, data in enumerate(batch_data):
            data['user_id'] = f'user_{i}'
        
        start_time = time.time()
        batch_results = self.calculator.batch_calculate_trust_scores(batch_data)
        batch_calc_time = time.time() - start_time
        
        # Should process 100 users in reasonable time
        self.assertLess(batch_calc_time, 10.0)  # Less than 10 seconds
        self.assertEqual(len(batch_results), 100)


class TestTrustPyramidIntegration(unittest.TestCase):
    """Integration tests for Trust Pyramid Calculator."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.calculator = TrustPyramidCalculator()
    
    @patch('truststream.trust_pyramid.TrustPyramidCalculator._get_user_data_from_db')
    def test_real_world_scenario(self, mock_get_data):
        """Test real-world scenario with realistic data."""
        # Mock realistic user data
        mock_get_data.return_value = {
            'user_id': 'real_user_456',
            'content_quality': 3.8,
            'engagement_metrics': {
                'likes_received': 320,
                'comments_received': 85,
                'shares_received': 42,
                'meaningful_interactions': 150
            },
            'social_connections': {
                'followers': 1200,
                'following': 450,
                'mutual_connections': 280,
                'community_memberships': 8
            },
            'behavioral_data': {
                'account_age_days': 547,
                'posting_frequency': 0.6,
                'response_time_hours': 3.2,
                'authenticity_indicators': ['verified_email', 'phone_verified', 'id_verified']
            },
            'violation_history': [
                {'type': 'minor_spam', 'date': '2023-06-15', 'resolved': True}
            ],
            'peer_endorsements': 28
        }
        
        # Calculate trust score
        trust_score = self.calculator.calculate_user_trust_score(mock_get_data.return_value)
        
        # Verify realistic results
        self.assertIsInstance(trust_score, TrustScore)
        self.assertGreater(trust_score.overall_score, 2.0)  # Should be above average
        self.assertLess(trust_score.overall_score, 5.0)     # But not perfect
        self.assertGreater(trust_score.confidence, 0.7)    # High confidence with good data
        
        # Should be in gold or platinum range
        self.assertIn(trust_score.rank, ['gold', 'platinum'])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)